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

# 1. Create virtual environment
cd backend
python -m venv venv && source venv/bin/activate

# 2. Install pinned dependencies (runtime plus test and lint tools)
pip install -r requirements-dev.txt

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
pytest --cov          # unit, contract and integration suites, fails under 35% coverage
ruff check .          # lint
pip-audit -r requirements.txt --no-deps --disable-pip
```

`pytest` collects `tests/unit`, `tests/contract` and `tests/integration` by default.
The older suites under `tests/test_*` and the loose `tests/test_*.py` scripts expect live services and are not part of the default run.

## Updating dependencies

Edit `requirements.in` or `requirements-dev.in`, then regenerate the pinned files.

```bash
uv pip compile requirements.in --universal --python-version 3.12 -o requirements.txt
uv pip compile requirements-dev.in --universal --python-version 3.12 -o requirements-dev.txt
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
