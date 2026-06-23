"""ORM models matching docs/DB_Tables.sql."""

from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('analyst', 'admin')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str | None] = mapped_column(String, nullable=True, default="analyst")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)

    watchlists: Mapped[list["Watchlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = ()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    sector: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)

    watchlists: Mapped[list["Watchlist"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    analyst_reports: Mapped[list["AnalystReport"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    update_logs: Mapped[list["UpdateLog"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    annual_reports: Mapped[list["AnnualReportRecord"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Watchlist(Base):
    __tablename__ = "watchlists"
    __table_args__ = (
        CheckConstraint("frequency IN ('daily', 'weekly')", name="ck_watchlists_frequency"),
        CheckConstraint("status IN ('active', 'paused')", name="ck_watchlists_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String, nullable=True)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str | None] = mapped_column(String, default="active", nullable=True)

    user: Mapped["User"] = relationship(back_populates="watchlists")
    company: Mapped["Company"] = relationship(back_populates="watchlists")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('annual_report', 'announcement', 'other')", name="ck_documents_type"
        ),
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_documents_processing_status",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String, nullable=True)
    document_title: Mapped[str | None] = mapped_column(String, nullable=True)
    report_year: Mapped[str | None] = mapped_column(String, nullable=True)
    s3_key: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    upload_date: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    processing_status: Mapped[str | None] = mapped_column(String, default="pending", nullable=True)

    company: Mapped["Company"] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    pinecone_namespace: Mapped[str | None] = mapped_column(String, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class AnalystReport(Base):
    __tablename__ = "analyst_reports"
    __table_args__ = (
        CheckConstraint(
            "sentiment_score >= 0.0 AND sentiment_score <= 1.0", name="ck_analyst_reports_sentiment_score"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    broker_name: Mapped[str | None] = mapped_column(String, nullable=True)
    report_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    s3_key: Mapped[str | None] = mapped_column(String, nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="analyst_reports")


class UpdateLog(Base):
    __tablename__ = "update_logs"
    __table_args__ = (
        CheckConstraint("update_type IN ('mcp_refresh', 'rag_process', 'manual')", name="ck_update_logs_type"),
        CheckConstraint("status IN ('success', 'failed', 'skipped')", name="ck_update_logs_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    update_type: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="update_logs")


class AnnualReportRecord(Base):
    __tablename__ = "annual_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    from_yr: Mapped[str | None] = mapped_column(String, nullable=True)
    to_yr: Mapped[str | None] = mapped_column(String, nullable=True)
    submission_type: Mapped[str | None] = mapped_column(String, nullable=True)
    broadcast_dttm: Mapped[str | None] = mapped_column(String, nullable=True)
    dissemination_date_time: Mapped[str | None] = mapped_column(String, nullable=True)
    time_taken: Mapped[str | None] = mapped_column(String, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    att_file_size: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="annual_reports")


class FinancialResult(Base):
    __tablename__ = "financial_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    seq_number: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    isin: Mapped[str | None] = mapped_column(String, nullable=True)
    audited: Mapped[str | None] = mapped_column(String, nullable=True)
    bank: Mapped[str | None] = mapped_column(String, nullable=True)
    consolidated: Mapped[str | None] = mapped_column(String, nullable=True)
    cumulative: Mapped[str | None] = mapped_column(String, nullable=True)
    period: Mapped[str | None] = mapped_column(String, nullable=True)
    relating_to: Mapped[str | None] = mapped_column(String, nullable=True)
    financial_year: Mapped[str | None] = mapped_column(String, nullable=True)
    from_date: Mapped[str | None] = mapped_column(String, nullable=True)
    to_date: Mapped[str | None] = mapped_column(String, nullable=True)
    format: Mapped[str | None] = mapped_column(String, nullable=True)
    ind_as: Mapped[str | None] = mapped_column(String, nullable=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    old_new_flag: Mapped[str | None] = mapped_column(String, nullable=True)
    re_ind: Mapped[str | None] = mapped_column(String, nullable=True)
    params: Mapped[str | None] = mapped_column(String, nullable=True)
    broadcast_date: Mapped[str | None] = mapped_column(String, nullable=True)
    filing_date: Mapped[str | None] = mapped_column(String, nullable=True)
    exchdisstime: Mapped[str | None] = mapped_column(String, nullable=True)
    difference: Mapped[str | None] = mapped_column(String, nullable=True)
    result_description: Mapped[str | None] = mapped_column(String, nullable=True)
    result_detailed_data_link: Mapped[str | None] = mapped_column(String, nullable=True)
    xbrl: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)


class NscAnnouncement(Base):
    __tablename__ = "nsc_announcements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    seq_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    sm_name: Mapped[str | None] = mapped_column(String, nullable=True)
    sm_isin: Mapped[str | None] = mapped_column(String, nullable=True)
    sm_industry: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    attchmnt_text: Mapped[str | None] = mapped_column(String, nullable=True)
    attchmnt_file: Mapped[str | None] = mapped_column(String, nullable=True)
    att_file_size: Mapped[str | None] = mapped_column(String, nullable=True)
    file_size: Mapped[str | None] = mapped_column(String, nullable=True)
    has_xbrl: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    an_dt: Mapped[str | None] = mapped_column(String, nullable=True)
    exchdisstime: Mapped[str | None] = mapped_column(String, nullable=True)
    dt: Mapped[str | None] = mapped_column(String, nullable=True)
    sort_date: Mapped[str | None] = mapped_column(String, nullable=True)
    difference: Mapped[str | None] = mapped_column(String, nullable=True)
    bflag: Mapped[str | None] = mapped_column(String, nullable=True)
    csv_name: Mapped[str | None] = mapped_column(String, nullable=True)
    old_new: Mapped[str | None] = mapped_column(String, nullable=True)
    orgid: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)