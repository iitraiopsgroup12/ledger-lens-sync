# Ledger Lens Sync

A backend service for tracking companies, watchlists, and company documents
(annual reports, announcements, analyst reports) for retrieval-augmented
analysis. It exposes a REST API for full CRUD over the following entities:

- **Users** — analysts/admins who own watchlists.
- **Companies** — tracked tickers/symbols.
- **Watchlists** — per-user subscriptions to a company at a given refresh
  frequency (`daily` / `weekly`).
- **Documents** — annual reports, announcements, etc. uploaded for a
  company, with a processing status (`pending` → `processing` →
  `completed` / `failed`).
- **Chunks** — text chunks produced from a document, referencing a Pinecone
  namespace for vector search.
- **Analyst Reports** — broker reports for a company with a sentiment
  score.
- **Update Logs** — audit trail of refresh/sync events per company
  (`mcp_refresh`, `rag_process`, `manual`).

## Architecture

The code is organized in layers, each depending only on the layer beneath
it:

```
app/
├── models.py        SQLAlchemy ORM models (matches docs/DB_Tables.sql)
├── schemas.py        Pydantic v2 request/response schemas (Create/Update/Read)
├── repository.py     Pure data-access (no business rules, no commit/rollback)
├── service.py         Business rules, uniqueness checks, transaction boundaries
├── dependencies.py   FastAPI Depends() wiring: session -> repository -> service
├── router.py          FastAPI routers exposing CRUD endpoints per entity
├── exceptions.py      Domain exceptions (NotFoundError, ConflictError)
└── database.py        Async SQLAlchemy engine/session setup
```

Routers call services, services call repositories, repositories talk to
the database — no layer skips ahead.

The canonical schema lives in `docs/DB_Tables.sql` (written for
PostgreSQL); `app/models.py` is the SQLAlchemy equivalent used at runtime
against SQLite.

## Configuration

- **Database**: SQLite, accessed asynchronously via `aiosqlite`. The file
  lives at `data/ledger_lens.db`, relative to the project root. The `data/`
  directory is created automatically on import of `app/database.py`
  (`app/database.py:9-12`). There are currently no environment variables —
  the database path is hard-coded.
- **Python version**: requires Python >= 3.14 (see `.python-version`).

## Running

`main.py` is the service entry point: it builds the FastAPI `app`, mounts
all routers from `app.router.all_routers`, and initializes the database
schema on startup via a lifespan handler.

Install dependencies (declared in `pyproject.toml`):

```bash
uv sync
```

Run the server:

```bash
uv run python main.py
```

or directly with uvicorn (enables `--reload`):

```bash
uv run uvicorn main:app --reload
```

The API is served at `http://localhost:8000`. A `GET /health` endpoint
(no database dependency) is available for liveness/readiness checks.

## Docker / Kubernetes

Build the image (multi-stage, using `uv` for dependency installation):

```bash
docker build -t ledger-lens-sync:latest .
```

Run it locally:

```bash
docker run -p 8000:8000 ledger-lens-sync:latest
```

The container runs as a non-root user and serves the app with `uvicorn`
on port 8000. The SQLite file is written to `/app/data/ledger_lens.db`
inside the container — for Kubernetes, back this with a `PersistentVolumeClaim`
mounted at `/app/data` if data needs to survive pod restarts, or treat the
deployment as ephemeral/single-replica if not. Since SQLite has no
built-in concurrent-writer support across pods, do not scale this
deployment beyond a single replica without first switching to a
network-backed database.

### Deploying with Helm

The `ledger-lens-sync-chart/` directory contains a Helm chart for this
service (probes wired to `/health`, container port 8000, resource
requests/limits, and an optional `persistence` PVC for the SQLite file).

```bash
helm upgrade --install ledger-lens-sync ./ledger-lens-sync-chart \
  --set image.repository=<your-registry>/ledger-lens-sync \
  --set image.tag=<tag>
```

To persist the SQLite database across pod restarts, enable the bundled
PVC:

```bash
helm upgrade --install ledger-lens-sync ./ledger-lens-sync-chart \
  --set image.repository=<your-registry>/ledger-lens-sync \
  --set image.tag=<tag> \
  --set persistence.enabled=true
```

Keep `replicaCount: 1` and `autoscaling.enabled: false` — SQLite does not
support concurrent writers across pods.

## API

All entities expose the same CRUD shape, mounted under their plural
prefix (`/users`, `/companies`, `/watchlists`, `/documents`, `/chunks`,
`/analyst-reports`, `/update-logs`):

| Method | Path        | Status | Description            |
|--------|-------------|--------|-------------------------|
| POST   | `/{entity}`           | 201 | Create a new record |
| GET    | `/{entity}/{id}`      | 200/404 | Fetch one record |
| GET    | `/{entity}?skip=&limit=` | 200 | List records (paginated, `limit` defaults to 100, max 500) |
| PATCH  | `/{entity}/{id}`      | 200/404 | Partially update a record |
| DELETE | `/{entity}/{id}`      | 204/404 | Delete a record |

Example:

```bash
curl -X POST http://localhost:8000/companies \
  -H "Content-Type: application/json" \
  -d '{"symbol": "ACME", "company_name": "Acme Corp", "sector": "Industrials"}'

curl http://localhost:8000/companies?skip=0&limit=20

curl -X PATCH http://localhost:8000/companies/<id> \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

curl -X DELETE http://localhost:8000/companies/<id>
```