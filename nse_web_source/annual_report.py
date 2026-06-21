from datetime import datetime
from dataclasses import dataclass, fields
from typing import Optional

import pandas as pd

from app.models import Company
from nse_data_storage import LocalFileStorage

from .common import BASE_URL, create_nse_session
from .data_channel import ChannelData, DataChannel

ANNUAL_REPORTS_URL = f"{BASE_URL}/api/annual-reports"
BROADCAST_DTTM_FORMAT = "%d-%b-%Y %H:%M:%S"


@dataclass
class AnnualReport:
    companyName: Optional[str] = None
    fromYr: Optional[str] = None
    toYr: Optional[str] = None
    submission_type: Optional[str] = None
    broadcast_dttm: Optional[str] = None
    disseminationDateTime: Optional[str] = None
    timeTaken: Optional[str] = None
    fileName: Optional[str] = None
    attFileSize: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "AnnualReport":
        known_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known_fields})


class AnnualReportClient(DataChannel):
    """Client for the NSE India annual-reports API."""

    def __init__(self):
        self.session = create_nse_session()
        self.storage = LocalFileStorage()

    def fetch_annual_report(
        self,
        symbol: str,
        index: str = "equities",
    ) -> list[AnnualReport]:
        params = {
            "index": index,
            "symbol": symbol,
        }

        response = self.session.get(ANNUAL_REPORTS_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", [])
        return [AnnualReport.from_dict(item) for item in data]

    def fetch_annual_report_df(self, **kwargs) -> pd.DataFrame:
        annual_reports = self.fetch_annual_report(**kwargs)
        return pd.DataFrame(r.__dict__ for r in annual_reports)

    def get_data(self, company: Company, start_date: str) -> list[ChannelData]:
        company_symbol = company.symbol
        start = datetime.strptime(start_date, "%d-%m-%Y")
        annual_reports = self.fetch_annual_report(symbol=company_symbol)

        result = []
        for r in annual_reports:
            try:
                event_dt = datetime.strptime(r.broadcast_dttm, BROADCAST_DTTM_FORMAT)
            except (TypeError, ValueError):
                continue
            if event_dt < start:
                continue
            attachment_storage_id = self.storage.store(r.fileName) if r.fileName else None
            result.append(
                ChannelData(
                    companyName=r.companyName,
                    Symbol=company_symbol,
                    Subject=f"Annual Report {r.fromYr}-{r.toYr}",
                    Detail=r.submission_type,
                    attachment=r.fileName,
                    XBRL=None,
                    event_date_time=r.broadcast_dttm,
                    source="NSE_ANNUAL_REPORT",
                    sync_date_time=r.disseminationDateTime,
                    sync_status="SUCCESS",
                    attachment_storage_id=attachment_storage_id,
                    xbrl_storage_id=None,
                )
            )
        return result