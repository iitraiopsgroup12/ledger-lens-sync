from abc import ABC, abstractmethod


class DataStorage(ABC):
    """Common interface for storing the content found at a URL."""

    @abstractmethod
    def store(self, url: str) -> str:
        """Fetch the content at url, persist it, and return its storage id."""
        ...
