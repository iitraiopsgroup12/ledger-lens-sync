"""Pydantic v2 schemas for request/response validation."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserRole = Literal["analyst", "admin"]
WatchlistFrequency = Literal["daily", "weekly"]
WatchlistStatus = Literal["active", "paused"]
DocumentType = Literal["annual_report", "announcement", "other"]
ProcessingStatus = Literal["pending", "processing", "completed", "failed"]
UpdateType = Literal["mcp_refresh", "rag_process", "manual"]
UpdateStatus = Literal["success", "failed", "skipped"]


# --- Users -------------------------------------------------------------


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: UserRole = "analyst"


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role: UserRole | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    role: str
    created_at: datetime


# --- Companies -----------------------------------------------------------


class CompanyCreate(BaseModel):
    symbol: str
    company_name: str
    sector: str | None = None
    is_active: bool = True


class CompanyUpdate(BaseModel):
    symbol: str | None = None
    company_name: str | None = None
    sector: str | None = None
    is_active: bool | None = None


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    company_name: str
    sector: str | None
    is_active: bool
    created_at: datetime


# --- Watchlists ------------------------------------------------------------


class WatchlistCreate(BaseModel):
    user_id: int
    company_id: int
    frequency: WatchlistFrequency
    status: WatchlistStatus = "active"


class WatchlistUpdate(BaseModel):
    frequency: WatchlistFrequency | None = None
    last_checked: datetime | None = None
    status: WatchlistStatus | None = None


class WatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company_id: int
    frequency: str
    last_checked: datetime | None
    status: str


# --- Documents -------------------------------------------------------------


class DocumentCreate(BaseModel):
    company_id: int
    document_type: DocumentType
    document_title: str | None = None
    report_year: str | None = None
    s3_key: str | None = None
    source: str | None = None
    processing_status: ProcessingStatus = "pending"


class DocumentUpdate(BaseModel):
    document_type: DocumentType | None = None
    document_title: str | None = None
    report_year: str | None = None
    s3_key: str | None = None
    source: str | None = None
    processing_status: ProcessingStatus | None = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    document_type: str
    document_title: str | None
    report_year: str | None
    s3_key: str | None
    source: str | None
    upload_date: datetime
    processing_status: str


# --- Chunks ------------------------------------------------------------------


class ChunkCreate(BaseModel):
    document_id: int
    pinecone_namespace: str
    chunk_count: int | None = None


class ChunkUpdate(BaseModel):
    pinecone_namespace: str | None = None
    chunk_count: int | None = None


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    pinecone_namespace: str
    chunk_count: int | None


# --- Analyst reports -----------------------------------------------------------


class AnalystReportCreate(BaseModel):
    company_id: int
    broker_name: str | None = None
    report_date: date | None = None
    s3_key: str | None = None
    sentiment_score: float | None = Field(default=None, ge=0.0, le=1.0)


class AnalystReportUpdate(BaseModel):
    broker_name: str | None = None
    report_date: date | None = None
    s3_key: str | None = None
    sentiment_score: float | None = Field(default=None, ge=0.0, le=1.0)


class AnalystReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    broker_name: str | None
    report_date: date | None
    s3_key: str | None
    sentiment_score: float | None


# --- Update logs -----------------------------------------------------------


class UpdateLogCreate(BaseModel):
    company_id: int
    update_type: UpdateType | None = None
    status: UpdateStatus | None = None
    message: str | None = None


class UpdateLogUpdate(BaseModel):
    update_type: UpdateType | None = None
    status: UpdateStatus | None = None
    message: str | None = None


class UpdateLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    update_type: str | None
    status: str | None
    message: str | None
    created_at: datetime


# --- Onboarding --------------------------------------------------------------


class ChannelDataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    companyName: str | None
    Symbol: str | None
    Subject: str | None
    Detail: str | None
    attachment: str | None
    XBRL: str | None
    event_date_time: str | None
    source: str | None
    sync_date_time: str | None
    sync_status: str | None
    attachment_storage_id: str | None
    xbrl_storage_id: str | None