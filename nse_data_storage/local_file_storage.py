import json
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from .storage import DataStorage

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "storage"))
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

RAG_API_BASE_URL = os.environ.get("RAG_API_BASE_URL", "http://localhost:8080")
INGEST_FILE_URL = f"{RAG_API_BASE_URL}/api/v1/ingest/file"


class LocalFileStorage(DataStorage):
    """Stores the content fetched from a URL as a file on the local filesystem."""

    def __init__(self, storage_dir: Path | str = DEFAULT_STORAGE_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._ingest_executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="ingest"
        )

    def store(
        self,
        url: str,
        bucket: str | None,
        json_obj: dict | None = None,
        embeddingRequired: bool = False,
    ) -> str:
        try:
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

            if embeddingRequired:
                self._ingest_executor.submit(
                    self._ingest_file, file_path.name, response.content, json_obj
                )

            return "file://" + file_id
        except:
            return "FILE_NOT_FOUND"

    def store_bytes(self, content: bytes, file_name: str, bucket: str | None = None) -> str:
        """Persist already-loaded bytes (e.g. an uploaded file) and return its storage id."""
        target_dir = self.storage_dir
        if bucket is not None:
            target_dir = target_dir / bucket
            target_dir.mkdir(parents=True, exist_ok=True)

        file_id = uuid.uuid4().hex
        suffix = Path(file_name).suffix
        file_path = target_dir / f"{file_id}{suffix}"
        file_path.write_bytes(content)

        return "file://" + file_id

    def retrieve(self, storage_id: str, bucket: str | None = None) -> bytes:
        file_id = storage_id.removeprefix("file://")

        target_dir = self.storage_dir
        if bucket is not None:
            target_dir = target_dir / bucket

        matches = list(target_dir.glob(f"{file_id}.*")) + list(target_dir.glob(file_id))
        if not matches:
            raise FileNotFoundError(
                f"No stored content for storage id {storage_id!r} in bucket {bucket!r}"
            )

        return matches[0].read_bytes()

    def _ingest_file(self, filename: str, content: bytes, json_obj: dict | None) -> None:
        """Forward the downloaded document and its record to the RAG ingest API.

        Runs on a background thread, so it logs failures instead of propagating
        them (the future is never awaited).
        """
        try:
            files = [("files", (filename, content, "application/octet-stream"))]
            data = {"metadata": json.dumps(json_obj)} if json_obj is not None else None
            response = requests.post(INGEST_FILE_URL, files=files, data=data, timeout=60000)
            response.raise_for_status()
        except Exception:
            logger.exception("Failed to ingest file %s into RAG API", filename)