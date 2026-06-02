# yachan-v2 — backend

Async **FastAPI** application powering the yachan imageboard: REST + WebSocket
API, Celery background tasks, and Alembic migrations.

For the full architecture and conventions see [`CLAUDE.md`](CLAUDE.md) in this
folder; this README is the human quick-start.

## Stack

FastAPI · SQLModel · asyncpg / PostgreSQL · Redis · Celery · kink (request-scoped
DI) · Alembic · Pillow (thumbnails) · PyJWT.

## Architecture in one breath

A strict layered design — **views → services → repositories** — with one
`AsyncSession` (and transaction) per request, wired by request-scoped dependency
injection. Views never touch SQL; services hold all business logic and raise
domain errors that FastAPI maps to HTTP status codes; repositories own every
query. See [`CLAUDE.md`](CLAUDE.md) for layer rules, the request lifecycle and the
domain model.

## API

All endpoints are under the `/api` prefix:

| Group | Path | Purpose |
|-------|------|---------|
| Boards   | `/api/boards`                         | list boards |
| Threads  | `/api/{slug}/threads`                 | catalog, create, detail |
| Posts    | `/api/{slug}/posts/...`               | edit, history, report |
| Captcha  | `/api/captcha`                        | image challenge |
| Mod      | `/api/mod/...`                        | login, reports, delete/ban/lock/sticky |
| Realtime | `/api/{slug}/ws`, `/api/{slug}/threads/{id}/ws` | WebSocket feeds |

Interactive docs at **http://127.0.0.1:8000/docs** when running locally.

## Quick start (local)

Uses the repo-root `.venv` (Poetry is configured to install into it). From the
repo root:

```bash
source .venv/Scripts/activate          # Windows; .venv/bin/activate on unix
poetry -C backend install

# infra (Docker): postgres on :5434, redis on :6379
docker compose up -d postgres redis

cd backend
poetry run alembic upgrade head        # create the schema
poetry run uvicorn main:app --reload   # http://127.0.0.1:8000
```

Required settings `JWT_SECRET` and `IP_HASH_SALT` (and `DATABASE_URL`,
`REDIS_URL`) come from `backend/.env` — see `.env.example`.

Background workers (separate terminals, from `backend/`):

```bash
celery -A src.celery_app.celery worker --loglevel=info
celery -A src.celery_app.celery beat   --loglevel=info
```

## Tests

```bash
poetry run pytest                      # from backend/
```

Pure unit tests mirroring `src/` under `tests/` — dependencies are mocked, no real
DB or Redis is needed.

## Migrations

```bash
poetry run alembic revision --autogenerate -m "describe change"
poetry run alembic upgrade head
```

## Admin CLI

```bash
poetry run python -m src.cli create-admin <username>   # prompts for a password
poetry run python -m src.cli dump-openapi -o ../openapi.json
```

## Project structure

```
main.py            app = create_app()
src/
  bootstrap/       DI container + request scope
  middleware/      ScopeMiddleware (per-request session/transaction)
  core/            config, database, redis, storage, exceptions
  utils/           clock, ip, names, tripcode, sequences, markup, captcha, auth, events
  models/          SQLModel tables
  repositories/    all SQL (one per model)
  schemas/         pydantic request/response
  services/        business logic
  views/           class-based HTTP entrypoints
  routers/         FastAPI routers
  tasks/           Celery tasks
  cli/             admin commands
alembic/           migrations
tests/             unit tests (mirror of src/)
```
