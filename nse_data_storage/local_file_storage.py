import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests

from .storage import DataStorage

DEFAULT_STORAGE_DIR = Path("storage")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}


class LocalFileStorage(DataStorage):
    """Stores the content fetched from a URL as a file on the local filesystem."""

    def __init__(self, storage_dir: Path | str = DEFAULT_STORAGE_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def store(self, url: str, bucket: str | None) -> str:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        target_dir = self.storage_dir
        if bucket is not None:
            target_dir = target_dir / bucket
            target_dir.mkdir(parents=True, exist_ok=True)

        file_id = uuid.uuid4().hex
        suffix = Path(urlparse(url).path).suffix
        file_path = target_dir / f"{file_id}{suffix}"
        file_path.write_bytes(response.content)

        return "file://" + file_id