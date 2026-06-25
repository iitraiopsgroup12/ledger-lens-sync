from datetime import datetime
from dataclasses import dataclass, fields
from typing import Optional

import pandas as pd

from app.models import Company
from nse_data_storage import LocalFileStorage

from .common import BASE_URL, create_nse_session, extract_file_name
from .data_channel import ChannelData, DataChannel

ANNOUNCEMENTS_URL = f"{BASE_URL}/api/corporate-announcements"


@dataclass
class Announcement:
    an_dt: Optional[str] = None
    attFileSize: Optional[str] = None
    attchmntFile: Optional[str] = None
    attchmntText: Optional[str] = None
    bflag: Optional[str] = None
    csvName: Optional[str] = None
    desc: Optional[str] = None
    difference: Optional[str] = None
    dt: Optional[str] = None
    exchdisstime: Optional[str] = None
    fileSize: Optional[str] = None
    hasXbrl: Optional[bool] = None
    old_new: Optional[str] = None
    orgid: Optional[str] = None
    seq_id: Optional[str] = None
    smIndustry: Optional[str] = None
    sm_isin: Optional[str] = None
    sm_name: Optional[str] = None
    sort_date: Optional[str] = None
    symbol: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Announcement":
        known_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known_fields})


class AnnouncementClient(DataChannel):
    """Client for the NSE India corporate-announcements API."""

    def __init__(self):
        self.session = create_nse_session()
        self.storage = LocalFileStorage()
        self.documents: list[dict] = []
        self.nsc_announcements: list[dict] = []

    def get_announcements(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
        index: str = "equities",
        issuer: Optional[str] = None,
        reqXbrl: bool = False,
    ) -> list[Announcement]:
        params = {
            "index": index,
            "from_date": from_date,
            "to_date": to_date,
            "symbol": symbol,
            "reqXbrl": str(reqXbrl).lower(),
        }
        if issuer:
            params["issuer"] = issuer

        response = self.session.get(ANNOUNCEMENTS_URL, params=params, timeout=10)
        response.raise_for_status()
        return [Announcement.from_dict(item) for item in response.json()]

    def get_announcements_df(self, **kwargs) -> pd.DataFrame:
        announcements = self.get_announcements(**kwargs)
        return pd.DataFrame(a.__dict__ for a in announcements)

    def get_data(self, company: Company, start_date: str) -> list[ChannelData]:
        company_symbol = company.symbol
        to_date = datetime.now().strftime("%d-%m-%Y")
        announcements = self.get_announcements(
            symbol=company_symbol, from_date=start_date, to_date=to_date
        )
        xbrl_announcements = self.get_announcements(
            symbol=company_symbol, from_date=start_date, to_date=to_date, reqXbrl=True
        )
        xbrl_url_by_seq_id = {a.seq_id: a.attchmntFile for a in xbrl_announcements}

        result = []
        documents = []
        nsc_announcements = []
        for a in announcements:

            xbrl_url = xbrl_url_by_seq_id.get(a.seq_id)
            attachment_url = a.attchmntFile if a.attchmntFile and a.attchmntFile != "-" else None
            xbrl_url = xbrl_url if xbrl_url and xbrl_url != "-" else None
            jsonObj = {
                    "company_id": company.id,
                    "seq_id": a.seq_id,
                    "symbol": a.symbol,
                    "sm_name": a.sm_name,
                    "sm_isin": a.sm_isin,
                    "sm_industry": a.smIndustry,
                    "description": a.desc,
                    "attchmnt_text": a.attchmntText,
                    "attchmnt_file": a.attchmntFile,
                    "att_file_size": a.attFileSize,
                    "file_size": a.fileSize,
                    "has_xbrl": a.hasXbrl,
                    "an_dt": a.an_dt,
                    "exchdisstime": a.exchdisstime,
                    "dt": a.dt,
                    "sort_date": a.sort_date,
                    "difference": a.difference,
                    "bflag": a.bflag,
                    "csv_name": a.csvName,
                    "old_new": a.old_new,
                    "orgid": a.orgid,
                }
            nsc_announcements.append(jsonObj)

            attachment_storage_id = self.storage.store(attachment_url, company.symbol, jsonObj) if attachment_url else None
            xbrl_storage_id = self.storage.store(xbrl_url, company.symbol, jsonObj) if xbrl_url else None
            documents.append(
                {
                    "company_id": company.id,
                    "document_type": "announcement",
                    "document_title": a.desc,
                    "report_year": a.an_dt,
                    "file_name": extract_file_name(xbrl_url),
                    "s3_key": attachment_storage_id,
                    "source": "NSE_CORPORATE_ANNOUNCEMENT",
                    "upload_date": datetime.utcnow(),
                    "processing_status": "completed",
                }
            )

            result.append(
                ChannelData(
                    companyName=a.sm_name,
                    Symbol=a.symbol,
                    Subject=a.desc,
                    Detail=a.attchmntText,
                    attachment=a.attchmntFile,
                    XBRL=xbrl_url,
                    event_date_time=a.an_dt,
                    source="NSE_CORPORATE_ANNOUNCEMENT",
                    sync_date_time=a.exchdisstime,
                    sync_status="SUCCESS",
                    attachment_storage_id=attachment_storage_id,
                    xbrl_storage_id=xbrl_storage_id,
                )
            )
        self.documents = documents
        self.nsc_announcements = nsc_announcements
        return result