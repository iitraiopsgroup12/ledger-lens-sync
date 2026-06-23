from abc import ABC, abstractmethod


class DataStorage(ABC):
    """Common interface for storing the content found at a URL."""

    @abstractmethod
    def store(self, url: str, bucket: str | None, json_obj: dict | None = None) -> str:
        """Fetch the content at url, persist it, and return its storage id.

        json_obj carries the record being persisted alongside the file, so
        implementations may use it as metadata for the stored content.
        """
        ...
