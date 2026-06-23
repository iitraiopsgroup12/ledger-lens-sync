"""Repository layer: pure data-access methods, no business rules.

Each repository wraps a single ORM model and an `AsyncSession`. Repositories
flush so callers can see generated defaults (e.g. primary keys) but never
commit or rollback — the service layer owns the transaction boundary.
"""

from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AnalystReport,
    AnnualReportRecord,
    Chunk,
    Company,
    Document,
    FinancialResult,
    NscAnnouncement,
    UpdateLog,
    User,
    Watchlist,
)

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Generic CRUD data-access methods shared by all entity repositories."""

    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self._session = session
        self._model = model

    async def create(self, data: dict) -> ModelType:
        """Insert a new row and flush to obtain server-generated defaults."""
        instance = self._model(**data)
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def get_by_id(self, entity_id: int) -> ModelType | None:
        """Fetch a single row by primary key, or None if absent."""
        return await self._session.get(self._model, entity_id)

    async def get_all(self, skip: int = 0, limit: int = 100, filters: dict | None = None) -> Sequence[ModelType]:
        """Fetch a page of rows, optionally filtered by exact column matches."""
        stmt = select(self._model)
        if filters:
            for column, value in filters.items():
                stmt = stmt.where(getattr(self._model, column) == value)
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update(self, entity_id: int, data: dict) -> ModelType | None:
        """Apply partial updates to an existing row, or return None if absent."""
        instance = await self.get_by_id(entity_id)
        if instance is None:
            return None
        for field, value in data.items():
            setattr(instance, field, value)
        await self._session.flush()
        return instance

    async def delete(self, entity_id: int) -> bool:
        """Delete a row by primary key. Returns False if it did not exist."""
        instance = await self.get_by_id(entity_id)
        if instance is None:
            return False
        await self._session.delete(instance)
        await self._session.flush()
        return True


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Company)

    async def get_by_symbol(self, symbol: str) -> Company | None:
        result = await self._session.execute(select(Company).where(Company.symbol == symbol))
        return result.scalar_one_or_none()


class WatchlistRepository(BaseRepository[Watchlist]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Watchlist)


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Document)


class ChunkRepository(BaseRepository[Chunk]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Chunk)


class AnalystReportRepository(BaseRepository[AnalystReport]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AnalystReport)


class UpdateLogRepository(BaseRepository[UpdateLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UpdateLog)


class NscAnnouncementRepository(BaseRepository[NscAnnouncement]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, NscAnnouncement)

    async def get_by_seq_id(self, seq_id: str) -> NscAnnouncement | None:
        result = await self._session.execute(select(NscAnnouncement).where(NscAnnouncement.seq_id == seq_id))
        return result.scalar_one_or_none()


class AnnualReportRecordRepository(BaseRepository[AnnualReportRecord]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AnnualReportRecord)

    async def get_by_file_name(self, file_name: str) -> AnnualReportRecord | None:
        result = await self._session.execute(
            select(AnnualReportRecord).where(AnnualReportRecord.file_name == file_name)
        )
        return result.scalar_one_or_none()


class FinancialResultRepository(BaseRepository[FinancialResult]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, FinancialResult)

    async def get_by_seq_number(self, seq_number: str) -> FinancialResult | None:
        result = await self._session.execute(
            select(FinancialResult).where(FinancialResult.seq_number == seq_number)
        )
        return result.scalar_one_or_none()