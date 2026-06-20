You are a senior Python backend engineer. Generate a clean, layered backend for the SQL table provided below.

## Input table
SQL table Location : /docs/DB_Tables.sql

## Stack & conventions
- Python 3.14+, SQLAlchemy 2.0 (use the modern `Mapped` / `mapped_column` typed ORM style, not the legacy Query API).
- Async SQLAlchemy with `async_sessionmaker` and `AsyncSession`. (If you prefer sync, say so and keep it consistent everywhere.)
- Pydantic v2 for schemas.
- FastAPI for the REST layer.
- Type hints everywhere; no `Any` unless unavoidable.
- SQLite Database  in-memory speed and file-based persistence to be configured at directory /data

## Architecture — produce these layers, each in its own module
1. **Model** (`models.py`): the SQLAlchemy ORM model matching the table exactly (columns, types, nullability, defaults, primary/foreign keys, unique constraints, indexes).

2. **Schemas** (`schemas.py`): Pydantic v2 models:
   - `XCreate` (fields required to create; exclude server-generated fields like id, created_at).
   - `XUpdate` (all fields optional, for PATCH semantics).
   - `XRead` (full representation returned to clients; `from_attributes=True`).

3. **Repository layer** (`repository.py`): a class that takes an `AsyncSession` and exposes pure data-access methods only — no business rules:
   - `create(data) -> Model`
   - `get_by_id(id) -> Model | None`
   - `get_all(skip, limit, filters) -> Sequence[Model]`
   - `update(id, data) -> Model | None`
   - `delete(id) -> bool`
   - Use `select()` statements; flush but do NOT commit inside the repo (let the caller/session own the transaction).

4. **Service layer** (`service.py`): a class that depends on the repository and holds business logic:
   - Validates business rules and uniqueness before writes.
   - Raises domain exceptions (e.g. `NotFoundError`, `ConflictError`) instead of returning None.
   - Owns the transaction boundary (commit/rollback).
   - Converts ORM objects to/from schemas where appropriate.

5. **API layer** (`router.py`): a FastAPI `APIRouter` exposing full CRUD:
   - `POST   /xs`           -> 201, returns XRead
   - `GET    /xs/{id}`      -> 200 / 404
   - `GET    /xs`           -> 200, paginated (skip/limit query params)
   - `PATCH  /xs/{id}`      -> 200 / 404
   - `DELETE /xs/{id}`      -> 204 / 404
   - Use FastAPI dependency injection to provide the session, repository, and service.
   - Map domain exceptions to proper HTTP responses via exception handlers.

6. **Wiring** (`database.py` + `dependencies.py`): async engine/session setup and the `Depends()` providers that assemble repo -> service -> route.

## Requirements
- Each layer depends only on the layer directly beneath it (router -> service -> repository -> model).
- No raw SQL strings; use the SQLAlchemy expression API.
- Handle not-found and unique-constraint/conflict cases explicitly.
- Add docstrings on public methods and brief inline comments only where non-obvious.

## Output format
- Give the complete code for each file under a clear filename header.
- After the code, include a short tree of the file structure and the exact pip install / run commands.
- End with 3–4 example requests (curl) covering create, read, update, delete.