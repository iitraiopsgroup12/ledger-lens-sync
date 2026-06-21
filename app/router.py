"""API layer: FastAPI routers exposing full CRUD for every entity."""

from collections.abc import Sequence

from fastapi import APIRouter, Query, status

from app.dependencies import (
    AnalystReportServiceDep,
    ChunkServiceDep,
    CompanyOnboardServiceDep,
    CompanyServiceDep,
    DocumentServiceDep,
    UpdateLogServiceDep,
    UserServiceDep,
    WatchlistServiceDep,
)
from app.schemas import (
    AnalystReportCreate,
    AnalystReportRead,
    AnalystReportUpdate,
    ChannelDataRead,
    ChunkCreate,
    ChunkRead,
    ChunkUpdate,
    CompanyCreate,
    CompanyRead,
    CompanyUpdate,
    DocumentCreate,
    DocumentRead,
    DocumentUpdate,
    UpdateLogCreate,
    UpdateLogRead,
    UpdateLogUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
    WatchlistCreate,
    WatchlistRead,
    WatchlistUpdate,
)

# --- Users -------------------------------------------------------------

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, service: UserServiceDep) -> UserRead:
    user = await service.create(payload.model_dump())
    return UserRead.model_validate(user)


@users_router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, service: UserServiceDep) -> UserRead:
    user = await service.get(user_id)
    return UserRead.model_validate(user)


@users_router.get("", response_model=list[UserRead])
async def list_users(
    service: UserServiceDep, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
) -> Sequence[UserRead]:
    users = await service.list(skip=skip, limit=limit)
    return [UserRead.model_validate(u) for u in users]


@users_router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, payload: UserUpdate, service: UserServiceDep) -> UserRead:
    user = await service.update(user_id, payload.model_dump(exclude_unset=True))
    return UserRead.model_validate(user)


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, service: UserServiceDep) -> None:
    await service.delete(user_id)


# --- Companies -----------------------------------------------------------

companies_router = APIRouter(prefix="/companies", tags=["companies"])


@companies_router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
async def create_company(payload: CompanyCreate, service: CompanyServiceDep) -> CompanyRead:
    company = await service.create(payload.model_dump())
    return CompanyRead.model_validate(company)


@companies_router.get("/{company_id}", response_model=CompanyRead)
async def get_company(company_id: int, service: CompanyServiceDep) -> CompanyRead:
    company = await service.get(company_id)
    return CompanyRead.model_validate(company)


@companies_router.get("", response_model=list[CompanyRead])
async def list_companies(
    service: CompanyServiceDep, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
) -> Sequence[CompanyRead]:
    companies = await service.list(skip=skip, limit=limit)
    return [CompanyRead.model_validate(c) for c in companies]


@companies_router.patch("/{company_id}", response_model=CompanyRead)
async def update_company(company_id: int, payload: CompanyUpdate, service: CompanyServiceDep) -> CompanyRead:
    company = await service.update(company_id, payload.model_dump(exclude_unset=True))
    return CompanyRead.model_validate(company)


@companies_router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: int, service: CompanyServiceDep) -> None:
    await service.delete(company_id)


# --- Watchlists ------------------------------------------------------------

watchlists_router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@watchlists_router.post("", response_model=WatchlistRead, status_code=status.HTTP_201_CREATED)
async def create_watchlist(payload: WatchlistCreate, service: WatchlistServiceDep) -> WatchlistRead:
    watchlist = await service.create(payload.model_dump())
    return WatchlistRead.model_validate(watchlist)


@watchlists_router.get("/{watchlist_id}", response_model=WatchlistRead)
async def get_watchlist(watchlist_id: int, service: WatchlistServiceDep) -> WatchlistRead:
    watchlist = await service.get(watchlist_id)
    return WatchlistRead.model_validate(watchlist)


@watchlists_router.get("", response_model=list[WatchlistRead])
async def list_watchlists(
    service: WatchlistServiceDep, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
) -> Sequence[WatchlistRead]:
    watchlists = await service.list(skip=skip, limit=limit)
    return [WatchlistRead.model_validate(w) for w in watchlists]


@watchlists_router.patch("/{watchlist_id}", response_model=WatchlistRead)
async def update_watchlist(
    watchlist_id: int, payload: WatchlistUpdate, service: WatchlistServiceDep
) -> WatchlistRead:
    watchlist = await service.update(watchlist_id, payload.model_dump(exclude_unset=True))
    return WatchlistRead.model_validate(watchlist)


@watchlists_router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(watchlist_id: int, service: WatchlistServiceDep) -> None:
    await service.delete(watchlist_id)


# --- Documents -------------------------------------------------------------

documents_router = APIRouter(prefix="/documents", tags=["documents"])


@documents_router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(payload: DocumentCreate, service: DocumentServiceDep) -> DocumentRead:
    document = await service.create(payload.model_dump())
    return DocumentRead.model_validate(document)


@documents_router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: int, service: DocumentServiceDep) -> DocumentRead:
    document = await service.get(document_id)
    return DocumentRead.model_validate(document)


@documents_router.get("", response_model=list[DocumentRead])
async def list_documents(
    service: DocumentServiceDep, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
) -> Sequence[DocumentRead]:
    documents = await service.list(skip=skip, limit=limit)
    return [DocumentRead.model_validate(d) for d in documents]


@documents_router.patch("/{document_id}", response_model=DocumentRead)
async def update_document(document_id: int, payload: DocumentUpdate, service: DocumentServiceDep) -> DocumentRead:
    document = await service.update(document_id, payload.model_dump(exclude_unset=True))
    return DocumentRead.model_validate(document)


@documents_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int, service: DocumentServiceDep) -> None:
    await service.delete(document_id)


# --- Chunks ------------------------------------------------------------------

chunks_router = APIRouter(prefix="/chunks", tags=["chunks"])


@chunks_router.post("", response_model=ChunkRead, status_code=status.HTTP_201_CREATED)
async def create_chunk(payload: ChunkCreate, service: ChunkServiceDep) -> ChunkRead:
    chunk = await service.create(payload.model_dump())
    return ChunkRead.model_validate(chunk)


@chunks_router.get("/{chunk_id}", response_model=ChunkRead)
async def get_chunk(chunk_id: int, service: ChunkServiceDep) -> ChunkRead:
    chunk = await service.get(chunk_id)
    return ChunkRead.model_validate(chunk)


@chunks_router.get("", response_model=list[ChunkRead])
async def list_chunks(
    service: ChunkServiceDep, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
) -> Sequence[ChunkRead]:
    chunks = await service.list(skip=skip, limit=limit)
    return [ChunkRead.model_validate(c) for c in chunks]


@chunks_router.patch("/{chunk_id}", response_model=ChunkRead)
async def update_chunk(chunk_id: int, payload: ChunkUpdate, service: ChunkServiceDep) -> ChunkRead:
    chunk = await service.update(chunk_id, payload.model_dump(exclude_unset=True))
    return ChunkRead.model_validate(chunk)


@chunks_router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chunk(chunk_id: int, service: ChunkServiceDep) -> None:
    await service.delete(chunk_id)


# --- Analyst reports -----------------------------------------------------------

analyst_reports_router = APIRouter(prefix="/analyst-reports", tags=["analyst-reports"])


@analyst_reports_router.post("", response_model=AnalystReportRead, status_code=status.HTTP_201_CREATED)
async def create_analyst_report(
    payload: AnalystReportCreate, service: AnalystReportServiceDep
) -> AnalystReportRead:
    report = await service.create(payload.model_dump())
    return AnalystReportRead.model_validate(report)


@analyst_reports_router.get("/{report_id}", response_model=AnalystReportRead)
async def get_analyst_report(report_id: int, service: AnalystReportServiceDep) -> AnalystReportRead:
    report = await service.get(report_id)
    return AnalystReportRead.model_validate(report)


@analyst_reports_router.get("", response_model=list[AnalystReportRead])
async def list_analyst_reports(
    service: AnalystReportServiceDep, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
) -> Sequence[AnalystReportRead]:
    reports = await service.list(skip=skip, limit=limit)
    return [AnalystReportRead.model_validate(r) for r in reports]


@analyst_reports_router.patch("/{report_id}", response_model=AnalystReportRead)
async def update_analyst_report(
    report_id: int, payload: AnalystReportUpdate, service: AnalystReportServiceDep
) -> AnalystReportRead:
    report = await service.update(report_id, payload.model_dump(exclude_unset=True))
    return AnalystReportRead.model_validate(report)


@analyst_reports_router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analyst_report(report_id: int, service: AnalystReportServiceDep) -> None:
    await service.delete(report_id)


# --- Update logs -----------------------------------------------------------

update_logs_router = APIRouter(prefix="/update-logs", tags=["update-logs"])


@update_logs_router.post("", response_model=UpdateLogRead, status_code=status.HTTP_201_CREATED)
async def create_update_log(payload: UpdateLogCreate, service: UpdateLogServiceDep) -> UpdateLogRead:
    log = await service.create(payload.model_dump())
    return UpdateLogRead.model_validate(log)


@update_logs_router.get("/{log_id}", response_model=UpdateLogRead)
async def get_update_log(log_id: int, service: UpdateLogServiceDep) -> UpdateLogRead:
    log = await service.get(log_id)
    return UpdateLogRead.model_validate(log)


@update_logs_router.get("", response_model=list[UpdateLogRead])
async def list_update_logs(
    service: UpdateLogServiceDep, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
) -> Sequence[UpdateLogRead]:
    logs = await service.list(skip=skip, limit=limit)
    return [UpdateLogRead.model_validate(l) for l in logs]


@update_logs_router.patch("/{log_id}", response_model=UpdateLogRead)
async def update_update_log(log_id: int, payload: UpdateLogUpdate, service: UpdateLogServiceDep) -> UpdateLogRead:
    log = await service.update(log_id, payload.model_dump(exclude_unset=True))
    return UpdateLogRead.model_validate(log)


@update_logs_router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_update_log(log_id: int, service: UpdateLogServiceDep) -> None:
    await service.delete(log_id)


# --- Onboarding --------------------------------------------------------------

onboard_router = APIRouter(tags=["onboard"])


@onboard_router.get("/onboard", response_model=list[ChannelDataRead])
async def onboard_company(symbol: str, service: CompanyOnboardServiceDep) -> list[ChannelDataRead]:
    channel_data = await service.on_board(symbol)
    return [ChannelDataRead.model_validate(d) for d in channel_data]


all_routers = (
    users_router,
    companies_router,
    watchlists_router,
    documents_router,
    chunks_router,
    analyst_reports_router,
    update_logs_router,
    onboard_router,
)