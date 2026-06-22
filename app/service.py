"""Service layer: business rules and transaction boundaries.

Each service wraps a repository, validates business rules before writes,
raises domain exceptions instead of returning None, and commits/rolls back
the session. ORM instances are returned to the router, which converts them
to read schemas.
"""

import os
from collections.abc import Sequence
from datetime import datetime
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models import (
    AnalystReport,
    AnnualReportRecord,
    Chunk,
    Company,
    Document,
    NscAnnouncement,
    UpdateLog,
    User,
    Watchlist,
)
from app.repository import (
    AnalystReportRepository,
    AnnualReportRecordRepository,
    BaseRepository,
    ChunkRepository,
    CompanyRepository,
    DocumentRepository,
    NscAnnouncementRepository,
    UpdateLogRepository,
    UserRepository,
    WatchlistRepository,
)
from nse_web_source.announcement import AnnouncementClient
from nse_web_source.annual_report import AnnualReportClient
from nse_web_source.common import BASE_URL, create_nse_session
from nse_web_source.data_channel import ChannelData, DataChannel

SMART_SEARCH_URL = f"{BASE_URL}/api/smart-search/eqEtf"

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    """Shared CRUD orchestration: commit/rollback + not-found translation."""

    entity_name = "entity"

    def __init__(self, session: AsyncSession, repository: BaseRepository[ModelType]) -> None:
        self._session = session
        self._repository = repository

    async def get(self, entity_id: int) -> ModelType:
        instance = await self._repository.get_by_id(entity_id)
        if instance is None:
            raise NotFoundError(self.entity_name, entity_id)
        return instance

    async def list(self, skip: int = 0, limit: int = 100, filters: dict | None = None) -> Sequence[ModelType]:
        return await self._repository.get_all(skip=skip, limit=limit, filters=filters)

    async def create(self, data: dict) -> ModelType:
        try:
            instance = await self._repository.create(data)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(f"{self.entity_name} violates a uniqueness or foreign-key constraint") from exc
        return instance

    async def update(self, entity_id: int, data: dict) -> ModelType:
        try:
            instance = await self._repository.update(entity_id, data)
            if instance is None:
                raise NotFoundError(self.entity_name, entity_id)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(f"{self.entity_name} violates a uniqueness or foreign-key constraint") from exc
        return instance

    async def delete(self, entity_id: int) -> None:
        deleted = await self._repository.delete(entity_id)
        if not deleted:
            raise NotFoundError(self.entity_name, entity_id)
        await self._session.commit()


class UserService(BaseService[User]):
    entity_name = "User"

    def __init__(self, session: AsyncSession, repository: UserRepository) -> None:
        super().__init__(session, repository)

    async def create(self, data: dict) -> User:
        existing = await self._session.execute(select(User).where(User.email == data["email"]))
        if existing.scalar_one_or_none() is not None:
            raise ConflictError(f"User with email '{data['email']}' already exists")
        return await super().create(data)


class CompanyService(BaseService[Company]):
    entity_name = "Company"

    def __init__(self, session: AsyncSession, repository: CompanyRepository) -> None:
        super().__init__(session, repository)

    async def create(self, data: dict) -> Company:
        existing = await self._repository.get_by_symbol(data["symbol"])
        if existing is not None:
            raise ConflictError(f"Company with symbol '{data['symbol']}' already exists")
        return await super().create(data)

    async def get_by_symbol(self, symbol: str) -> Company | None:
        return await self._repository.get_by_symbol(symbol)


class WatchlistService(BaseService[Watchlist]):
    entity_name = "Watchlist"

    def __init__(self, session: AsyncSession, repository: WatchlistRepository) -> None:
        super().__init__(session, repository)


class DocumentService(BaseService[Document]):
    entity_name = "Document"

    def __init__(self, session: AsyncSession, repository: DocumentRepository) -> None:
        super().__init__(session, repository)


class ChunkService(BaseService[Chunk]):
    entity_name = "Chunk"

    def __init__(self, session: AsyncSession, repository: ChunkRepository) -> None:
        super().__init__(session, repository)


class AnalystReportService(BaseService[AnalystReport]):
    entity_name = "AnalystReport"

    def __init__(self, session: AsyncSession, repository: AnalystReportRepository) -> None:
        super().__init__(session, repository)


class UpdateLogService(BaseService[UpdateLog]):
    entity_name = "UpdateLog"

    def __init__(self, session: AsyncSession, repository: UpdateLogRepository) -> None:
        super().__init__(session, repository)


class NscAnnouncementService(BaseService[NscAnnouncement]):
    entity_name = "NscAnnouncement"

    def __init__(self, session: AsyncSession, repository: NscAnnouncementRepository) -> None:
        super().__init__(session, repository)

    async def create(self, data: dict) -> NscAnnouncement:
        existing = await self._repository.get_by_seq_id(data["seq_id"])
        if existing is not None:
            return existing
        return await super().create(data)


class AnnualReportRecordService(BaseService[AnnualReportRecord]):
    entity_name = "AnnualReportRecord"

    def __init__(self, session: AsyncSession, repository: AnnualReportRecordRepository) -> None:
        super().__init__(session, repository)

    async def create(self, data: dict) -> AnnualReportRecord:
        if data.get("file_name"):
            existing = await self._repository.get_by_file_name(data["file_name"])
            if existing is not None:
                return existing
        return await super().create(data)


class CompanyOnboardService:
    """Pulls a company's full historical record from every NSE data channel."""

    EARLIEST_START_DATE = os.environ.get("EARLIEST_START_DATE", "01-01-2022")

    def __init__(
        self,
        company_service: CompanyService,
        document_service: DocumentService,
        nsc_announcement_service: NscAnnouncementService,
        annual_report_record_service: AnnualReportRecordService,
        watchlist_service: WatchlistService,
        channels: tuple[DataChannel, ...] | None = None,
    ) -> None:
        self._company_service = company_service
        self._document_service = document_service
        self._nsc_announcement_service = nsc_announcement_service
        self._annual_report_record_service = annual_report_record_service
        self._watchlist_service = watchlist_service
        self._channels = channels or (AnnouncementClient(), AnnualReportClient())

    async def on_board(self, company_symbol: str, user_id: int) -> list[ChannelData]:
        company = await self._save_company(company_symbol)
        await self._watchlist_service.create(
            {
                "user_id": user_id,
                "company_id": company.id,
                "frequency": "daily",
                "last_checked": datetime.utcnow(),
                "status": "active",
            }
        )

        result: list[ChannelData] = []
        for channel in self._channels:
            result.extend(channel.get_data(company, self.EARLIEST_START_DATE))
            for document_data in getattr(channel, "documents", []):
                await self._document_service.create(document_data)
            for nsc_announcement_data in getattr(channel, "nsc_announcements", []):
                await self._nsc_announcement_service.create(nsc_announcement_data)
            for annual_report_data in getattr(channel, "annual_reports", []):
                await self._annual_report_record_service.create(annual_report_data)
        return result

    async def _save_company(self, company_symbol: str) -> Company:
        existing_company = await self._company_service.get_by_symbol(company_symbol)
        if existing_company is not None:
            return existing_company

        session = create_nse_session()
        response = session.get(SMART_SEARCH_URL, params={"q": company_symbol}, timeout=10)
        response.raise_for_status()
        matches = response.json()

        match = next((m for m in matches if m.get("symbol") == company_symbol), None)
        if match is None:
            raise NotFoundError("Company", company_symbol)

        company_data = {
            "symbol": company_symbol,
            "company_name": match["companyName"],
            "sector": match.get("segment"),
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        return await self._company_service.create(company_data)