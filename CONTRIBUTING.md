# Contributing to CargoCore

This guide covers local setup, the checks every change must pass, and how to land a change.
Follow `CODE_OF_CONDUCT.md` in issues, pull requests and reviews.

## Set up

Follow "Running without Docker" in `README.md` for the backend and the web app.
Use `docker compose up --build` from the repo root when you only need the stack running.

## Before you open a pull request

Run the same checks CI runs.
A pull request with a red check does not merge.

```bash
# backend/
ruff check .
pytest --cov
pip-audit -r requirements.txt --no-deps --disable-pip

# frontend/
npm run lint
npm run format:check
npm run test:coverage
npm run build
```

The backend suite needs Postgres with a `logistics_db_test` database, as `README.md` describes.

## Tests

- A change that alters behavior lands with a test that fails without it.
- Backend unit tests live in `backend/tests/unit/`, API-level tests in `backend/tests/integration/` and response-shape checks in `backend/tests/contract/`.
- Frontend tests live in `frontend/tests/unit/` as `*.test.js` files and run on Vitest with jsdom.
- Mock network calls in frontend tests with `vi.stubGlobal('fetch', ...)` or by mocking `@/utils/aiApi`, as the existing suites do.
- Do not lower a coverage floor in `backend/pyproject.toml` or `frontend/vitest.config.js` to get a change through.

## Code style

- Python follows the ruff rules in `backend/pyproject.toml`.
- JavaScript and Vue follow `frontend/eslint.config.js`.
- New frontend files follow `frontend/.prettierrc.json`.
  `frontend/.prettierignore` keeps the older `src/` tree out of the format check for now.
  Format a `src/` file with `npx prettier --write <file>` in its own commit when you next change it, so the reformat stays out of the behavior diff.
- Keep new files under 500 lines.
  Split a view or service by feature before it grows past that.
- CI runs `python scripts/check_file_size.py`, which fails when a source file passes 800 lines.
  Files that were already longer are listed in `scripts/file_size_baseline.json` and may shrink but not grow.
  After you split one, run the script with `--update` and commit the lower baseline.

## Dependencies

- Backend dependencies go in `backend/requirements.in`, or `requirements-dev.in` for test and lint tools.
  Regenerate the pinned files with the `uv pip compile` commands in `backend/README.md` and commit both.
- Frontend dependencies go through `npm install` in `frontend/`, and `package-lock.json` is committed with the change.
- Dependabot opens weekly update pull requests, and each one must pass CI like any other change.

## Database changes

Change the SQLAlchemy model, then generate a migration from `backend/`.

```bash
alembic revision --autogenerate -m "short description"
alembic upgrade head
```

Read the generated file before committing it, since autogenerate misses renames and some constraint changes.

## Commits and pull requests

- Branch from `main` and open a pull request back into it.
- Write commit subjects as `type(scope): summary`, for example `fix(orders): keep COD payments idempotent`.
  Types are `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`, `chore`, `style` and `perf`.
- Keep each commit to one change that builds and passes tests on its own.
- Never commit `.env` files, API keys or tokens.
  The `secret-scan` CI job runs gitleaks over the full history.
- Use the bug report or feature request template in `.github/ISSUE_TEMPLATE/` when you open an issue.
