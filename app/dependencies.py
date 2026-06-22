"""FastAPI Depends() providers assembling repository -> service per entity."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repository import (
    AnalystReportRepository,
    AnnualReportRecordRepository,
    ChunkRepository,
    CompanyRepository,
    DocumentRepository,
    NscAnnouncementRepository,
    UpdateLogRepository,
    UserRepository,
    WatchlistRepository,
)
from app.service import (
    AnalystReportService,
    AnnualReportRecordService,
    ChunkService,
    CompanyOnboardService,
    CompanyService,
    DocumentService,
    NscAnnouncementService,
    UpdateLogService,
    UserService,
    WatchlistService,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session, UserRepository(session))


def get_company_service(session: SessionDep) -> CompanyService:
    return CompanyService(session, CompanyRepository(session))


def get_watchlist_service(session: SessionDep) -> WatchlistService:
    return WatchlistService(session, WatchlistRepository(session))


def get_document_service(session: SessionDep) -> DocumentService:
    return DocumentService(session, DocumentRepository(session))


def get_chunk_service(session: SessionDep) -> ChunkService:
    return ChunkService(session, ChunkRepository(session))


def get_analyst_report_service(session: SessionDep) -> AnalystReportService:
    return AnalystReportService(session, AnalystReportRepository(session))


def get_update_log_service(session: SessionDep) -> UpdateLogService:
    return UpdateLogService(session, UpdateLogRepository(session))


def get_nsc_announcement_service(session: SessionDep) -> NscAnnouncementService:
    return NscAnnouncementService(session, NscAnnouncementRepository(session))


def get_annual_report_record_service(session: SessionDep) -> AnnualReportRecordService:
    return AnnualReportRecordService(session, AnnualReportRecordRepository(session))


def get_company_onboard_service(
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    nsc_announcement_service: Annotated[NscAnnouncementService, Depends(get_nsc_announcement_service)],
    annual_report_record_service: Annotated[AnnualReportRecordService, Depends(get_annual_report_record_service)],
    watchlist_service: Annotated[WatchlistService, Depends(get_watchlist_service)],
) -> CompanyOnboardService:
    return CompanyOnboardService(
        company_service,
        document_service,
        nsc_announcement_service,
        annual_report_record_service,
        watchlist_service,
    )


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]
WatchlistServiceDep = Annotated[WatchlistService, Depends(get_watchlist_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
ChunkServiceDep = Annotated[ChunkService, Depends(get_chunk_service)]
AnalystReportServiceDep = Annotated[AnalystReportService, Depends(get_analyst_report_service)]
UpdateLogServiceDep = Annotated[UpdateLogService, Depends(get_update_log_service)]
NscAnnouncementServiceDep = Annotated[NscAnnouncementService, Depends(get_nsc_announcement_service)]
AnnualReportRecordServiceDep = Annotated[AnnualReportRecordService, Depends(get_annual_report_record_service)]
CompanyOnboardServiceDep = Annotated[CompanyOnboardService, Depends(get_company_onboard_service)]