from datetime import datetime
from dataclasses import dataclass, fields
from typing import Optional

import pandas as pd

from app.models import Company
from nse_data_storage import LocalFileStorage

from .common import BASE_URL, create_nse_session
from .data_channel import ChannelData, DataChannel

INTEGRATED_RESULTS_URL = f"{BASE_URL}/api/integrated-filing-results"
BROADCAST_DATE_FORMAT = "%d-%b-%Y %H:%M:%S"


@dataclass
class IntegratedResult:
    attFileSize: Optional[str] = None
    audited: Optional[str] = None
    broadcast_Date: Optional[str] = None
    cmName: Optional[str] = None
    consolidated: Optional[str] = None
    creation_Date: Optional[str] = None
    diff: Optional[str] = None
    ixbrl: Optional[str] = None
    ixbrlFileSize: Optional[str] = None
    pdf_attach: Optional[str] = None
    qe_Date: Optional[str] = None
    revised_Date: Optional[str] = None
    revision_Remark: Optional[str] = None
    seq_Id: Optional[str] = None
    smName: Optional[str] = None
    symbol: Optional[str] = None
    type: Optional[str] = None
    type_Sub: Optional[str] = None
    xbrl: Optional[str] = None
    xbrlFileSize: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "IntegratedResult":
        known_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known_fields})


class IntegratedResultsClient(DataChannel):
    """Client for the NSE India integrated-filing-results API."""

    def __init__(self):
        self.session = create_nse_session()
        self.storage = LocalFileStorage()
        self.documents: list[dict] = []
        self.integrated_results: list[dict] = []

    def fetch_integrated_results(
        self,
        symbol: str,
        issuer: Optional[str] = None,
        index: str = "equities",
        period_ended: str = "all",
        type: str = "Integrated Filing- Financials",
        page: int = 1,
        size: int = 200,
    ) -> list[IntegratedResult]:
        params = {
            "index": index,
            "symbol": symbol,
            "period_ended": period_ended,
            "type": type,
            "page": page,
            "size": size,
        }
        if issuer:
            params["issuer"] = issuer

        response = self.session.get(INTEGRATED_RESULTS_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", [])
        return [IntegratedResult.from_dict(item) for item in data]

    def fetch_integrated_results_df(self, **kwargs) -> pd.DataFrame:
        integrated_results = self.fetch_integrated_results(**kwargs)
        return pd.DataFrame(r.__dict__ for r in integrated_results)

    def get_data(self, company: Company, start_date: str) -> list[ChannelData]:

        company_symbol = company.symbol
        start = datetime.strptime(start_date, "%d-%m-%Y")
        integrated_results = self.fetch_integrated_results(
            symbol=company_symbol, issuer=company.company_name
        )

        result = []
        documents = []
        integrated_result_records = []
        for r in integrated_results:
            try:
                event_dt = datetime.strptime(r.broadcast_Date, BROADCAST_DATE_FORMAT)
            except (TypeError, ValueError):
                continue
            if event_dt < start:
                continue
            xbrl_url = r.xbrl if r.xbrl and not r.xbrl.endswith("/null") else None
            jsonObj = {
                    "seq_id": r.seq_Id,
                    "symbol": r.symbol,
                    "cm_name": r.cmName,
                    "sm_name": r.smName,
                    "audited": r.audited,
                    "consolidated": r.consolidated,
                    "type": r.type,
                    "type_sub": r.type_Sub,
                    "qe_date": r.qe_Date,
                    "broadcast_date": r.broadcast_Date,
                    "creation_date": r.creation_Date,
                    "revised_date": r.revised_Date,
                    "revision_remark": r.revision_Remark,
                    "diff": r.diff,
                    "ixbrl": r.ixbrl,
                    "ixbrl_file_size": r.ixbrlFileSize,
                    "xbrl": r.xbrl,
                    "xbrl_file_size": r.xbrlFileSize,
                    "pdf_attach": r.pdf_attach,
                    "att_file_size": r.attFileSize,
                }
            integrated_result_records.append(jsonObj)
            xbrl_storage_id = self.storage.store(xbrl_url, company_symbol, jsonObj) if xbrl_url else None
            documents.append(
                {
                    "company_id": company.id,
                    "document_type": "other",
                    "document_title": f"{r.type} {r.qe_Date}",
                    "report_year": r.qe_Date,
                    "s3_key": xbrl_storage_id,
                    "source": "NSE_INTEGRATED_FILING",
                    "upload_date": datetime.utcnow(),
                    "processing_status": "completed",
                }
            )
            result.append(
                ChannelData(
                    companyName=r.cmName,
                    Symbol=r.symbol,
                    Subject=f"Integrated Filing {r.type} {r.qe_Date}",
                    Detail=f"{r.consolidated} / {r.audited}",
                    attachment=None,
                    XBRL=xbrl_url,
                    event_date_time=r.broadcast_Date,
                    source="NSE_INTEGRATED_FILING",
                    sync_date_time=r.creation_Date,
                    sync_status="SUCCESS",
                    attachment_storage_id=None,
                    xbrl_storage_id=xbrl_storage_id,
                )
            )
        self.documents = documents
        self.integrated_results = integrated_result_records
        return result