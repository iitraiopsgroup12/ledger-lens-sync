from datetime import datetime
from dataclasses import dataclass, fields
from typing import Optional

import pandas as pd

from app.models import Company
from nse_data_storage import LocalFileStorage

from .common import BASE_URL, create_nse_session
from .data_channel import ChannelData, DataChannel

FINANCIAL_RESULTS_URL = f"{BASE_URL}/api/corporates-financial-results"
BROADCAST_DATE_FORMAT = "%d-%b-%Y %H:%M:%S"

@dataclass
class FinancialResult:
    audited: Optional[str] = None
    bank: Optional[str] = None
    broadCastDate: Optional[str] = None
    companyName: Optional[str] = None
    consolidated: Optional[str] = None
    cumulative: Optional[str] = None
    difference: Optional[str] = None
    exchdisstime: Optional[str] = None
    filingDate: Optional[str] = None
    financialYear: Optional[str] = None
    format: Optional[str] = None
    fromDate: Optional[str] = None
    indAs: Optional[str] = None
    industry: Optional[str] = None
    isin: Optional[str] = None
    oldNewFlag: Optional[str] = None
    params: Optional[str] = None
    period: Optional[str] = None
    reInd: Optional[str] = None
    relatingTo: Optional[str] = None
    resultDescription: Optional[str] = None
    resultDetailedDataLink: Optional[str] = None
    seqNumber: Optional[str] = None
    symbol: Optional[str] = None
    toDate: Optional[str] = None
    xbrl: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "FinancialResult":
        known_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known_fields})


class FinancialResultsClient(DataChannel):
    """Client for the NSE India corporates-financial-results API."""

    def __init__(self, period):
        self.session = create_nse_session()
        self.storage = LocalFileStorage()
        self.documents: list[dict] = []
        self.financial_results: list[dict] = []
        self.period = period
    def fetch_financial_results(
        self,
        symbol: str,
        issuer: Optional[str] = None,
        index: str = "equities"
    ) -> list[FinancialResult]:
        params = {
            "index": index,
            "symbol": symbol,
            "period": self.period,
        }
        if issuer:
            params["issuer"] = issuer

        response = self.session.get(FINANCIAL_RESULTS_URL, params=params, timeout=10)
        response.raise_for_status()
        return [FinancialResult.from_dict(item) for item in response.json()]

    def fetch_financial_results_df(self, **kwargs) -> pd.DataFrame:
        financial_results = self.fetch_financial_results(**kwargs)
        return pd.DataFrame(r.__dict__ for r in financial_results)

    def get_data(self, company: Company, start_date: str) -> list[ChannelData]:

        company_symbol = company.symbol
        start = datetime.strptime(start_date, "%d-%m-%Y")
        financial_results = self.fetch_financial_results(
            symbol=company_symbol, issuer=company.company_name
        )

        result = []
        documents = []
        financial_result_records = []
        for r in financial_results:
            if r.xbrl.endswith((".xml",".pdf")):
                try:
                    event_dt = datetime.strptime(r.broadCastDate, BROADCAST_DATE_FORMAT)
                except (TypeError, ValueError):
                    continue
                if event_dt < start:
                    continue
                xbrl_url = r.xbrl if r.xbrl and not r.xbrl.endswith("/-") else None
                jsonObj = {
                        "seq_number": r.seqNumber,
                        "symbol": r.symbol,
                        "company_name": r.companyName,
                        "isin": r.isin,
                        "audited": r.audited,
                        "bank": r.bank,
                        "consolidated": r.consolidated,
                        "cumulative": r.cumulative,
                        "period": r.period,
                        "relating_to": r.relatingTo,
                        "financial_year": r.financialYear,
                        "from_date": r.fromDate,
                        "to_date": r.toDate,
                        "format": r.format,
                        "ind_as": r.indAs,
                        "industry": r.industry,
                        "old_new_flag": r.oldNewFlag,
                        "re_ind": r.reInd,
                        "params": r.params,
                        "broadcast_date": r.broadCastDate,
                        "filing_date": r.filingDate,
                        "exchdisstime": r.exchdisstime,
                        "difference": r.difference,
                        "result_description": r.resultDescription,
                        "result_detailed_data_link": r.resultDetailedDataLink,
                        "xbrl": r.xbrl,
                    }
                financial_result_records.append(jsonObj)
                xbrl_storage_id = self.storage.store(xbrl_url, company_symbol, jsonObj) if xbrl_url else None
                documents.append(
                    {
                        "company_id": company.id,
                        "document_type": self.period,
                        "document_title":r.relatingTo,
                        "report_year": r.financialYear,
                        "s3_key": xbrl_storage_id,
                        "source": "NSE_CORPORATE_ANNOUNCEMENT",
                        "upload_date": datetime.utcnow(),
                        "processing_status": "completed",
                    }
                )
                result.append(
                    ChannelData(
                        companyName=r.companyName,
                        Symbol=r.symbol,
                        Subject=f"Financial Results {r.relatingTo} {r.financialYear}",
                        Detail=f"{r.consolidated} / {r.audited}",
                        attachment=None,
                        XBRL=xbrl_url,
                        event_date_time=r.broadCastDate,
                        source="NSE_FINANCIAL_RESULT",
                        sync_date_time=r.exchdisstime,
                        sync_status="SUCCESS",
                        attachment_storage_id=None,
                        xbrl_storage_id=xbrl_storage_id,
                    )
                )
        self.documents = documents
        self.financial_results = financial_result_records
        return result
