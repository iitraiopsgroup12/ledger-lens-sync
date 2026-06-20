"""Service layer: business rules and transaction boundaries.

Each service wraps a repository, validates business rules before writes,
raises domain exceptions instead of returning None, and commits/rolls back
the session. ORM instances are returned to the router, which converts them
to read schemas.
"""

from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models import AnalystReport, Chunk, Company, Document, UpdateLog, User, Watchlist
from app.repository import (
    AnalystReportRepository,
    BaseRepository,
    ChunkRepository,
    CompanyRepository,
    DocumentRepository,
    UpdateLogRepository,
    UserRepository,
    WatchlistRepository,
)

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    """Shared CRUD orchestration: commit/rollback + not-found translation."""

    entity_name = "entity"

    def __init__(self, session: AsyncSession, repository: BaseRepository[ModelType]) -> None:
        self._session = session
        self._repository = repository

    async def get(self, entity_id: str) -> ModelType:
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

    async def update(self, entity_id: str, data: dict) -> ModelType:
        try:
            instance = await self._repository.update(entity_id, data)
            if instance is None:
                raise NotFoundError(self.entity_name, entity_id)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(f"{self.entity_name} violates a uniqueness or foreign-key constraint") from exc
        return instance

    async def delete(self, entity_id: str) -> None:
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
        existing = await self._session.execute(select(Company).where(Company.symbol == data["symbol"]))
        if existing.scalar_one_or_none() is not None:
            raise ConflictError(f"Company with symbol '{data['symbol']}' already exists")
        return await super().create(data)


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