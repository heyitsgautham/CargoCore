# Backend — Logistics & Move Management System

FastAPI · PostgreSQL 16 · SQLAlchemy 2.0 (async) · Alembic · Redis · Docker

---

## Quickstart (Docker Compose)

The compose file lives at the repo root and starts this API with Postgres, Redis and the web app.

```bash
cd ..
docker compose up --build
```

The API listens on http://localhost:8000, with Swagger UI at `/docs` and ReDoc at `/redoc`.
Alembic migrations run when the `app` container starts.

---

## Local Dev (without Docker)

```bash
# Requires: Python 3.12+, PostgreSQL 16, Redis 7

# 1. Install the locked dependencies (runtime plus test and lint tools)
#    from the repo root, which holds the uv workspace and uv.lock
uv sync --frozen
source .venv/bin/activate
cd backend

# 2. Commands below run inside that virtualenv, or prefix them with `uv run`

# 3. Copy and configure environment variables
cp .env.example .env
# Open .env and update:
#   DATABASE_URL=postgresql+asyncpg://<your_mac_username>@localhost:5432/logistics_db
#   REDIS_URL=redis://localhost:6379/0
#   SECRET_KEY=<any long random string>

# 4. Create the database
createdb logistics_db

# 5. Run migrations
alembic upgrade head

# 6. Start dev server (with auto-reload)
uvicorn app.main:app --reload --port 8000
```

---

## Running Tests

The suites need a Postgres database named `logistics_db_test` that `DATABASE_URL` can reach.
Redis is mocked.

```bash
createdb logistics_db_test
uv run pytest --cov   # every backend suite, fails under 70% coverage
uv run ruff check .   # lint
uv export --frozen --no-dev --no-hashes --package cargocore-api -o /tmp/req.txt
uv run pip-audit -r /tmp/req.txt --no-deps --disable-pip
```

`pytest` collects `tests/unit`, `tests/contract`, `tests/integration`, `tests/flows` and the `tests/test_*` suites by default.
`tests/flows` drives whole features over HTTP against a seeded hub built by `tests/factories.py`, with outbound network calls blocked.

## Updating dependencies

Add or upgrade a package with uv from this directory, then commit `pyproject.toml` and the root `uv.lock`.

```bash
uv add <package>             # runtime dependency
uv add --dev <package>       # test or lint tool
uv lock --upgrade-package <package>
```

---

## Project Structure

```
app/
├── main.py           # FastAPI app factory
├── config.py         # pydantic-settings (reads .env)
├── database.py       # Async engine, get_db() dependency
├── dependencies.py   # get_current_user, require_role()
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic v2 request/response schemas
├── routers/          # Route handlers (grouped by domain)
├── services/         # Business logic layer
├── utils/            # JWT, hashing, Redis, file upload helpers
└── middleware/       # Logging, auth middleware
alembic/              # DB migrations
tests/                # pytest integration tests
```

---

## Auth Endpoints (Phase 1)

| Method | Path | Auth |
|---|---|---|
| POST | `/api/v1/auth/register` | None |
| POST | `/api/v1/auth/login` | None |
| POST | `/api/v1/auth/refresh` | Refresh token |
| POST | `/api/v1/auth/logout` | Bearer |
| GET | `/api/v1/auth/me` | Bearer |
| PUT | `/api/v1/auth/me` | Bearer |
| POST | `/api/v1/auth/change-password` | Bearer |
| POST | `/api/v1/auth/forgot-password` | None |
| POST | `/api/v1/auth/reset-password` | None |
| GET | `/health` | None |
