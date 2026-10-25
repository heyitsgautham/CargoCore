# CargoCore

CargoCore is a logistics and house-move management system built by Team QuadCore-Devs for the IIT Madras Software Engineering course.
One FastAPI backend and one Postgres database serve three clients.

| Part | Folder | Stack |
|---|---|---|
| API | `backend/` | FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2, Redis, Loguru |
| Web app for every office role | `frontend/` | Vue 3, Vite, Pinia, Vue Router, Tailwind CSS 4 |
| Driver app | `driver-app/` | Vue 3, Capacitor 6 for Android |

The web app has dashboards for six roles: individual customer, vendor, logistics manager, warehouse manager, dispatcher and AI support agent.
Drivers use the Android app for manifests, GPS tracking and proof of delivery.

## Architecture

```
 frontend/ (Vue SPA)        driver-app/ (Capacitor APK)
        │  REST + JWT                │  REST + JWT, WebSocket
        └──────────────┬─────────────┘
                       ▼
              backend/app/main.py  (FastAPI app factory)
                       │
        routers/   one module per domain: auth, orders, logistics,
                   warehouses, warehouse_operations, inventory, vendor,
                   customer, finance, rates, tracking, ai, ws_fleet ...
                       │  request bodies validated by schemas/ (Pydantic)
        services/  business rules, one module per domain
                       │
        models/    SQLAlchemy ORM ──► PostgreSQL 16 (Alembic migrations)
        utils/     JWT, hashing, Redis client, Gemini client, geocoding
```

- `middleware/logging_middleware.py` logs method, path, status and duration for every request with Loguru, tags every log line with a request id, and returns that id in the `X-Request-ID` header.
- `app/logging_config.py` writes one JSON object per line when `LOG_JSON` is on, which is the default in production.
- `GET /health` returns `{"status": "ok"}` and backs the container health check.
- `GET /health/ready` also checks Postgres and Redis, and returns 503 when the database is unreachable.
- Auth issues HS256 access and refresh tokens, and Redis holds the logout blacklist and password-reset OTPs.
- The AI assistant calls Google Gemini when `GEMINI_API_KEY` is set and answers from rules and database lookups when it is not.

## Quick start with Docker

Docker Compose brings up the API, the web app, Postgres 16 and Redis 7 from the repo root.

```bash
cp .env.example .env        # optional, every value has a default
docker compose up --build
```

| Service | URL |
|---|---|
| Web app | http://localhost:8080 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Postgres | localhost:5432, database `logistics_db` |
| Redis | localhost:6379 |

The `app` container runs `alembic upgrade head` before it starts Uvicorn.

## Running without Docker

You need Python 3.12, Node.js 20 or newer, PostgreSQL 16 and Redis 7.

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                 # set DATABASE_URL, REDIS_URL and SECRET_KEY
createdb logistics_db
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Web app

```bash
cd frontend
npm ci
cp .env.example .env                 # VITE_API_BASE_URL defaults to http://127.0.0.1:8000
npm run dev                          # http://localhost:5173
```

### Driver app

```bash
cd driver-app
npm ci --legacy-peer-deps
cp .env.example .env
npm run dev                          # browser preview
npm run cap:android                  # build, sync and open in Android Studio
```

CI builds a debug APK on every push to `main` that touches `driver-app/`.

## Tests and checks

These are the commands CI runs in `.github/workflows/ci.yml`.

| Where | Command | What it does |
|---|---|---|
| `backend/` | `pytest --cov` | 879 unit, contract, integration and flow tests, fails under 70% coverage |
| `backend/` | `ruff check .` | lint |
| `backend/` | `pip-audit -r requirements.txt --no-deps --disable-pip` | dependency audit |
| `frontend/` | `npm test` | 235 Vitest tests for the API client, the Pinia stores, composables, slips and utils |
| `frontend/` | `npm run test:coverage` | the same tests with coverage thresholds |
| `frontend/` | `npm run lint` | ESLint with the Vue plugin |
| `frontend/` | `npm run format:check` | Prettier |
| `frontend/` | `npm run build` | production bundle in `frontend/dist` |
| `frontend/` | `npm audit --audit-level=high` | dependency audit |
| repo root | `gitleaks git --config .gitleaks.toml .` | secret scan over the full history |
| repo root | `python scripts/check_file_size.py` | fails when a source file passes 800 lines or a listed long file grows |

The backend tests need a reachable Postgres database named `logistics_db_test`.
`tests/conftest.py` derives its URL from `DATABASE_URL`, creates the tables and drops them afterwards.
Redis and Gemini are mocked.

## Environment variables

`.env.example` at the root lists every variable for the Docker setup.
`backend/.env.example`, `frontend/.env.example` and `driver-app/.env.example` cover running each part on its own.

| Variable | Read by | Default | Purpose |
|---|---|---|---|
| `APP_ENV` | backend | `development` | `production` turns off SQL echo and dev-only shortcuts |
| `SECRET_KEY` | backend | `change-me` | signs JWTs, set 32 or more random characters |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | backend | `1440` | access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | backend | `7` | refresh token lifetime |
| `DATABASE_URL` | backend | local `logistics_db` | async SQLAlchemy URL, `postgresql+asyncpg://...` |
| `REDIS_URL` | backend | `redis://localhost:6379/0` | token blacklist and OTP storage |
| `ALLOWED_ORIGINS` | backend | `http://localhost:5173,http://localhost:3000` | extra CORS origins, comma separated |
| `LOG_LEVEL` | backend | `INFO` | lowest level written to stdout |
| `LOG_JSON` | backend | on in production | `true` writes one JSON object per log line |
| `GOOGLE_CLIENT_ID` | backend | empty | Google sign-in token audience |
| `GOOGLE_MAPS_API_KEY` | backend | empty | geocoding and distance lookups |
| `GEMINI_API_KEY` | backend | empty | AI assistant and room photo estimates |
| `DAILY_API_KEY` | backend | empty | Daily.co video rooms for meetings |
| `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB` | backend | `./uploads`, `10` | file uploads |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | backend | empty, `587` | outgoing email |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | docker compose | `logistics_user`, `logistics_pass`, `logistics_db` | database container |
| `VITE_API_BASE_URL` | frontend, driver app | `http://127.0.0.1:8000` | API origin, baked in at build time |
| `VITE_GOOGLE_CLIENT_ID` | frontend | empty | Google sign-in button |
| `VITE_API_BASE_URL_ANDROID` | driver app | unset | API origin override on a phone or emulator |

## Repository layout

```
backend/
  app/           FastAPI app: routers, schemas, services, models, utils, middleware
  alembic/       database migrations
  tests/         unit, contract and integration suites, plus API test reports
  requirements.in, requirements.txt          runtime dependencies, pinned
  requirements-dev.in, requirements-dev.txt  test and lint tools, pinned
frontend/
  src/           role views (IV, LWD, LWDDVI, Ai), Pinia stores, composables, API client
  tests/unit/    Vitest suites
  html-slips/    printable slip templates served at /html-slips
driver-app/      Capacitor Android app and its Gradle project
docs/            plans, meeting minutes, frontend and backend notes
docker-compose.yml, .env.example   full stack for local use
```

## Role workflow

| Step | Role | Tool | Hands over |
|---|---|---|---|
| 1 | Individual or vendor | booking UI | an order |
| 2 | Logistics manager | admin dashboard | an approved order and resources |
| 3 | Warehouse manager | inventory and floor map | a packed shipment and crew |
| 4 | Dispatcher | route map | an assigned route |
| 5 | Driver | Android app | proof of delivery |
| 6 | AI support | chat | answers, escalations and tickets |

`ROLE_FEATURES.md` describes each role's screens in detail.

## Contributing

`CONTRIBUTING.md` has the setup, branch, commit and review rules.

## License

This is an academic project, see `LICENSE` for the terms.
