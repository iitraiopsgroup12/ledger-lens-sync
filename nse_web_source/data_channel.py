from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChannelData:
    companyName: Optional[str] = None
    Symbol: Optional[str] = None
    Subject: Optional[str] = None
    Detail: Optional[str] = None
    attachment: Optional[str] = None
    XBRL: Optional[str] = None
    event_date_time: Optional[str] = None
    source: Optional[str] = None
    sync_date_time: Optional[str] = None
    sync_status: Optional[str] = None
    attachment_storage_id: Optional[str] = None
    xbrl_storage_id: Optional[str] = None


class DataChannel(ABC):
    """Common interface for NSE data sources that yield normalized ChannelData."""

    @abstractmethod
    def get_data(self, company_symbol: str, start_date: str) -> list[ChannelData]:
        ...