# Ledger Lens Sync — Service Notes

> Companion notes for [`architecture.drawio`](./architecture.drawio).
> **Ledger Lens Sync** is a FastAPI service that synchronises company disclosures from
> **NSE India** (announcements, annual reports, integrated/financial results), persists the
> structured records in PostgreSQL, stores the underlying files, and forwards selected files
> to an external **RAG service** for embedding/ingestion. It also exposes full CRUD over
> every domain entity and a one-call company **onboarding** workflow.

The service follows a strict **layered architecture**:

```
Client ──HTTP──▶ Router (REST) ──▶ Service (business rules + tx) ──▶ Repository (data access) ──▶ PostgreSQL
                                         │
                                         ├──▶ nse_web_source   (pull data from NSE)
                                         └──▶ nse_data_storage (store files → S3 / local → RAG ingest)
```

Key boundary rules:
- **Routers** only translate HTTP ↔ Pydantic schemas and delegate to a service (injected via `Depends()`).
- **Services** own business rules and the **transaction boundary** (`commit` / `rollback`) and raise domain exceptions (`NotFoundError`, `ConflictError`).
- **Repositories** are pure data access — they `flush` (to surface generated keys) but **never** commit or rollback.

---

## 1. REST Endpoints

Defined in [`app/router.py`](../app/router.py) as one `APIRouter` per entity (registered in `main.py`). Every CRUD router exposes the standard five operations:

| Router (prefix) | Tag | Endpoints |
|---|---|---|
| `/users` | users | `POST` · `GET /{user_id}` · `GET /email/{email_address}` · `GET` (list) · `PATCH /{user_id}` · `DELETE /{user_id}` |
| `/companies` | companies | `POST` · `GET /{company_id}` · `GET` (list) · `PATCH` · `DELETE` |
| `/watchlists` | watchlists | `POST` · `GET /{watchlist_id}` · `GET` (list) · `PATCH` · `DELETE` |
| `/documents` | documents | `POST` · `GET /{document_id}` · `GET` (list) · `PATCH` · `DELETE` |
| `/chunks` | chunks | `POST` · `GET /{chunk_id}` · `GET` (list) · `PATCH` · `DELETE` |
| `/analyst-reports` | analyst-reports | `POST` (**multipart file upload**) · `GET /{report_id}` · `GET ?company_symbol` · `PATCH` · `DELETE` |
| `/update-logs` | update-logs | `POST` · `GET /{log_id}` · `GET` (list) · `PATCH` · `DELETE` |
| `/financial-results` | financial-results | `POST` · `GET /{result_id}` · `GET` (list) · `PATCH` · `DELETE` |
| `/onboard` | onboard | `GET /onboard?symbol=&user_id=` — **orchestration endpoint** |
| `/health` | — | `GET /health` — liveness/readiness probe (no DB dependency) |

Notable, non-generic endpoints:
- **`POST /analyst-reports`** — accepts `multipart/form-data` (`company_symbol`, `file`, optional `broker_name`, `report_date`, `sentiment_score`). Validates the extension against `{.pdf, .docx, .doc, .xml, .json}`, stores the bytes, and persists both an `AnalystReport` and a matching `Document` row in one transaction.
- **`GET /analyst-reports?company_symbol=`** — returns both the analyst reports and the associated documents for a company (`AnalystReportListResponse`).
- **`GET /onboard`** — resolves the company on NSE, creates a watchlist entry for the user, then pulls and persists the company's full historical record across every NSE data channel.

List endpoints support pagination via `skip` (`>= 0`) and `limit` (`1..500`).

---

## 2. Service Layer & Repository Layer

### Service layer — [`app/service.py`](../app/service.py)

`BaseService[Model]` provides shared CRUD orchestration: `get`, `list`, `create`, `update`, `delete`, with `commit`/`rollback` and `IntegrityError → ConflictError` translation. Concrete services add business rules:

| Service | Responsibility / business rule |
|---|---|
| `UserService` | Enforces unique email; hashes passwords with **bcrypt** before insert/update; `get_by_email`. |
| `CompanyService` | Enforces unique `symbol`; `get_by_symbol`. |
| `WatchlistService` | Plain CRUD. |
| `DocumentService` | Plain CRUD. |
| `ChunkService` | Plain CRUD (RAG text chunks). |
| `AnalystReportService` | `create_from_upload()` — resolves company, stores the file via `LocalFileStorage`, persists report + document atomically; `list_by_company_symbol()`. |
| `UpdateLogService` | Plain CRUD (sync audit log). |
| `NscAnnouncementService` | Idempotent create keyed by `seq_id` (returns existing if present). |
| `AnnualReportRecordService` | Idempotent create keyed by `file_name`. |
| `FinancialResultService` | Idempotent create keyed by `seq_number`. |
| `IntegratedResultService` | Idempotent create keyed by `seq_id`. |
| `CompanyOnboardService` | **Orchestrator** — not a `BaseService`; coordinates multiple services + NSE channels (see §4). |

### Repository layer — [`app/repository.py`](../app/repository.py)

`BaseRepository[Model]` wraps a single ORM model + `AsyncSession`: `create`, `get_by_id`, `get_all` (with optional exact-match filters + pagination), `update`, `delete`. It **flushes only** — the service owns the transaction. Subclasses add targeted finders:

- `UserRepository.get_by_email`
- `CompanyRepository.get_by_symbol`
- `DocumentRepository.get_analyst_reports_by_company_id`
- `AnalystReportRepository.get_by_company_id`
- `NscAnnouncementRepository.get_by_seq_id`
- `AnnualReportRecordRepository.get_by_file_name`
- `FinancialResultRepository.get_by_seq_number`
- `IntegratedResultRepository.get_by_seq_id`

### Dependency wiring — [`app/dependencies.py`](../app/dependencies.py)

Per-request `Depends()` providers assemble `Repository → Service`, sharing one request-scoped `AsyncSession` (`get_session`). `CompanyOnboardService` is composed from the other services. Pydantic I/O contracts live in [`app/schemas.py`](../app/schemas.py).

---

## 3. External / Internal Packages

### `nse_web_source` — NSE data acquisition

A pluggable set of "channel" clients implementing a common interface:

- **`DataChannel` (ABC)** — `get_data(company, start_date) -> list[ChannelData]`.
- **`ChannelData`** (dataclass) — normalised record (subject, detail, attachment URL, XBRL, event time, storage ids, sync status).
- **Clients**: `AnnouncementClient`, `AnnualReportClient`, `IntegratedResultsClient`, `FinancialResultsClient`.
- **`common.py`** — `create_nse_session()` builds a `requests.Session` that first visits `nseindia.com` to obtain cookies (NSE rejects API calls without them); `extract_file_name()` helper; `BASE_URL`.

Each client fetches disclosures from NSE, downloads the referenced files via `nse_data_storage`, and yields `ChannelData` plus side-collections (`documents`, `annual_reports`, `integrated_results`, `nsc_announcements`) that the onboard service persists.

### `nse_data_storage` — file storage + RAG ingest

- **`DataStorage` (ABC)** — `store(url, bucket, json_obj)` (download + persist, returns a storage id) and `retrieve(storage_id, bucket)`.
- **`LocalFileStorage`** — writes to a local `STORAGE_DIR`; `store_bytes()` for already-loaded uploads; runs RAG ingest on a background `ThreadPoolExecutor` (4 workers).
- **`AwsFileStorage`** — stores objects in **Amazon S3** via `boto3` (`put_object`/`get_object`); all config from env (`AWS_S3_BUCKET`, `AWS_REGION`, `AWS_S3_PREFIX`, credentials, optional `AWS_S3_ENDPOINT_URL` for MinIO/LocalStack).

Both implementations expose `_ingest_file()` which forwards the file to the RAG API (see §4).

> Note: the codebase imports this package as `nse_data_storage` (the request refers to it as `nsc_data_storage`).

---

## 4. RAG Ingestion Flow

Files are pushed to an external **RAG service** for embedding so they become searchable. The target is built from configuration:

```python
RAG_API_BASE_URL = os.environ.get("RAG_API_BASE_URL", "http://localhost:8080")
INGEST_FILE_URL  = f"{RAG_API_BASE_URL}/api/v1/ingest/file"
```

Trigger and mechanics (`LocalFileStorage`):

1. A `nse_web_source` client calls `storage.store(url, bucket, json_obj, embeddingRequired=True)`.
2. `store()` downloads the file (with browser-like headers), writes it under `STORAGE_DIR/<bucket>/`, and returns a `file://<id>` storage id.
3. When `embeddingRequired=True`, ingestion is **submitted to a background thread pool** (`ThreadPoolExecutor`) so it never blocks the sync request.
4. `_ingest_file(filename, content, metadata)` issues a **multipart `POST {RAG_API_BASE_URL}/api/v1/ingest/file`** with `files=[("files", (filename, content, "application/octet-stream"))]` and `data={"metadata": json.dumps(json_obj)}`.
5. Because it runs detached on a worker thread, failures are **logged, not propagated** (the future is never awaited).

`AwsFileStorage` contains the same `_ingest_file()` method; its call site is currently commented out, so S3 storage and RAG ingestion can be toggled independently.

```
Channel.get_data() ──▶ storage.store(url, embeddingRequired=True)
                              │ writes file to disk / S3
                              └─(background thread)─▶ POST /api/v1/ingest/file ──▶ RAG service (embeds + indexes)
```

---

## 5. Tools & Technologies

| Area | Technology |
|---|---|
| Language | **Python 3.14** (`.python-version`) |
| Web framework | **FastAPI** 0.137 + **Uvicorn** (standard) |
| Validation / serialization | **Pydantic v2** (with `email` extras) |
| ORM / database | **SQLAlchemy 2.0 async** + **asyncpg** → **PostgreSQL** |
| Auth | **bcrypt** (password hashing) |
| HTTP client | **requests** (NSE + RAG calls) |
| Data | **pandas** |
| Cloud storage | **boto3** / **Amazon S3** |
| Config | **python-dotenv** (`.env`) |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` (background RAG ingest) |
| External RAG | RAG ingestion microservice (`/api/v1/ingest/file`) |
| Packaging | **uv** (`uv.lock`) / `requirements.txt`, `pyproject.toml` |
| Containerization | **Docker** (`Dockerfile`, `.dockerignore`) |
| Orchestration | **Kubernetes** via **Helm** chart (`ledger-lens-sync-chart`: Deployment, Service, Ingress/HTTPRoute, HPA, PVC, ServiceAccount) |
| External data source | **NSE India** (`www.nseindia.com`) |

### Run locally

```bash
python main.py            # serves on 0.0.0.0:8000 (set UVICORN_RELOAD=true for autoreload)
# OpenAPI docs at http://localhost:8000/docs
```

Key environment variables: `DATABASE_URL` (or `POSTGRES_*`), `RAG_API_BASE_URL`, `STORAGE_DIR`,
`AWS_S3_BUCKET` / `AWS_REGION` / `AWS_S3_PREFIX` / AWS credentials, `EARLIEST_START_DATE`.