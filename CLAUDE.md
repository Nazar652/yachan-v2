# yachan-v2

Anonymous imageboard. Async FastAPI backend with a strict layered architecture
and request-scoped dependency injection via **kink**. This file is the working
guide for agents — read it before changing code.

## Conventions (read first)

- **Full names, no abbreviations.** `redis_client`, not `r`; `derived_key`, not `dk`.
- **No leading underscores on variables or instance attributes.** `self.session`,
  not `self._s`. Leading `_` is allowed only on module-private constants
  (`_ALPHABET`), private functions (`_post_ref_plugin`), and private methods
  (`_full_path`).
  - Exception: a name dictated by an external typed API stays as required, e.g.
    the mistune plugin parameter must be `md` (see `utils/markup.py`).
- **Comments:** sparse, only for non-obvious logic. Natural prose, lowercase, no
  decorative separators.
- **Every method gets a unit test.** Tests are pure unit tests — mock the
  dependencies, exercise one method. Add tests in the same change as the code.
- **End of every change:** run `make lint` until fully green (ruff, pyright,
  pytest, frontend lint).

## Layout

```
backend/
  main.py                  app entrypoint: app = create_app()
  src/
    __init__.py            create_app(): setup_di, middleware, exception handlers, routers
    celery_app.py          Celery instance + beat schedule
    bootstrap/
      scope.py             ContextVar request scope + resolve_scoped()
      container.py         setup_di(): all di registrations (called once at startup)
    middleware/
      scope.py             ScopeMiddleware: opens scope, commits/rolls back/closes per request
    core/                  infrastructure: config, database, redis, storage, exceptions
    utils/                  standalone helpers: clock, ip, names, tripcode, sequences,
                           markup, captcha, auth, rate_limit, events
    models/                SQLModel tables, pure data, no logic
    repositories/          all SQL, one class per model, @inject
    schemas/               pydantic request/response, no db awareness
    services/              all business logic, @inject
    views/                 class-based http entrypoints, @inject
    routers/               FastAPI routers, Depends(_view) bridge
    tasks/                 Celery tasks (ScopedTask), thin wrappers over services
  alembic/                 async migrations
  tests/                   mirrors src/, pure unit tests
frontend/                  (separate, not covered here)
nginx/nginx.conf           reverse proxy -> backend
docker-compose.yml         postgres, redis, backend, celery-worker, celery-beat, nginx
```

## Layer rules (do not violate)

```
views/        -> services/                  (never repositories, models, or SQL)
services/     -> repositories/, other services/, models/, core/, utils/
                 (never HTTP, never raises HTTPException — raises domain errors)
repositories/ -> models/, core/database, utils/  (only AsyncSession; all SQL lives here)
tasks/        -> services/                   (same rules as views)
core/         -> config/connections/exceptions (infrastructure, no domain logic)
utils/        -> stdlib + a single resource at most (pure, reusable helpers)
models/       -> nothing but their own fields (pure data)
```

Domain exceptions live in `core/exceptions.py`. Services raise them; FastAPI
exception handlers in `create_app()` map them to status codes:
`NotFoundError`→404, `ForbiddenError`→403, `ConflictError`→409,
`RateLimitedError`→429, `BadRequestError`→400, `UnauthorizedError`→401.

## Dependency injection

- Global kink `di` is configured once by `setup_di()` (in `create_app()` and in
  the Celery worker via the `worker_process_init` signal).
- **Singletons** are registered as instances: `Settings`, `MarkupRenderer`,
  `LocalStorage`, `Redis`, `RateLimiter`.
- **Scoped** deps (`AsyncSession`, every repository, every service) are
  registered as `lambda container: resolve_scoped(Cls, Cls)`. Within one request
  (or one task) they resolve to the same instance, so all repositories share one
  `AsyncSession` and therefore one transaction.
- `resolve_scoped(cls, factory, force_new=False)` — returns the scope-cached
  instance, creating it once; with no active scope it calls the factory every
  time; `force_new=True` builds a fresh instance without touching the cache.
- The request scope is a `ContextVar` dict (`bootstrap/scope.py`).
  `ScopeMiddleware` opens it, commits on success, rolls back on exception, then
  closes the session and clears the scope. `ScopedTask` does the same around
  Celery tasks.
- Classes that need injection are decorated `@inject` and take their deps as
  typed `__init__` params. Construct them with no args (`PostService()`); kink
  fills the params. In tests, pass mocks explicitly (`PostService(post_repo=...)`).

## Request lifecycle

```
ScopeMiddleware opens scope
  -> router calls _view() -> View() (kink injects the service)
  -> view computes ip_hash, runs cross-cutting checks (captcha, rate limit)
  -> view calls service method (business logic, raises domain errors)
  -> service calls repositories (SQL) sharing one AsyncSession
  -> view maps the result to a *Response schema
ScopeMiddleware commits, closes session, clears scope
```

Note: FastAPI's exception middleware sits *inside* ScopeMiddleware, so handled
domain errors become responses and the middleware then **commits**. Services
validate before writing, so a domain error means nothing was written. Keep that
ordering: validate first, write last.

## Domain model

Anonymous imageboard — no user accounts for posters.

- `Board` — `slug` (unique, `^[a-z0-9_]{1,20}$`), `title`, `bump_limit`.
  Each board owns a Postgres sequence `post_number_seq_{slug}` for per-board post
  numbering (see `utils/sequences.py`, created in `BoardService.create_board`).
- `Thread` — belongs to a board; `is_locked`, `is_sticky`, `reply_count`,
  `bump_at` (catalog ordering).
- `Post` — `post_number` (unique per board), `name`, `tripcode`, `ip_hash`
  (never exposed), `body` (raw markdown) + `body_html` (rendered), `sage`,
  `is_op`, soft-delete via `deleted`/`deleted_by`. Edit window: 30 min, once,
  same ip.
- `PostEdit` — original body kept before the single allowed edit.
- `PostBacklink` — `>>N` references; `source_post_id` links to `target_post_id`.
- `Attachment` — storage-agnostic `file_path`, `md5` (dedup), `media_type`;
  thumbnail/dimensions filled asynchronously by the `process_attachment` task.
- `Ban` — by `ip_hash`, optional `board_id` (null = global), `expires_at`.
- `Report`, `ModAccount` (role admin/moderator, JWT auth).

Identity:
- **Poster IP** is hashed (`utils/ip.hash_ip`, salted) and never returned.
- **Tripcode**: a `#password` suffix in the name field becomes a tripcode
  (`utils/names.parse_name` + `utils/tripcode`).
- **Mod auth**: username/password (PBKDF2 in `utils/auth`) -> JWT bearer token.

## Important technical decisions

- **Timestamps are naive UTC.** Columns are `TIMESTAMP WITHOUT TIME ZONE`;
  asyncpg rejects tz-aware values for them. Always use `utils/clock.utcnow()`
  (naive UTC) for defaults and comparisons, never `datetime.utcnow()` (deprecated)
  or tz-aware `datetime.now(UTC)`.
- **Model primary keys are typed `id: int`** (not `int | None`) even though the
  default is `None`. `Field(...)` returns `Any`, so the type checker is satisfied
  and `obj.id` flows as `int`. The db column is still a not-null autoincrement PK.
- **SQLModel + pyright:** at class level `Post.id` is seen as `int`, so
  `where(Post.id == x)`, `.is_()`, `.asc()`, `.desc()` look like type errors.
  Wrap column references in `sqlmodel.col(...)` in repositories — it keeps type
  safety. This is why every repository query uses `col(...)`.
- **Lazy config/db.** `get_settings()`, `get_engine()`, `get_sessionmaker()`,
  `get_redis()` are `@lru_cache`d. Nothing is built at import, so importing
  `src...` never reads `.env` or builds an engine — unit tests stay isolated.
- **Required settings** `JWT_SECRET` and `IP_HASH_SALT` have no defaults. They
  live in `backend/.env` (absolute path resolution, so any cwd works). Tests set
  them in `tests/conftest.py` before importing `src`.
- **Celery + async:** `ScopedTask.__call__` runs the async `run()` via
  `asyncio.run`. Therefore task tests must be **synchronous** (calling a task from
  an async test would nest event loops).
- **Per-board sequence names** are built only via
  `utils/sequences.post_number_sequence_name(slug)`, which validates the slug
  because it is interpolated into raw DDL.

## Commands

All backend tooling runs in the **root `.venv`** (used by `make lint`/pyright/
hooks). Poetry manages a *separate* env under `backend/`. When you add a
dependency:

```bash
cd backend && poetry add <pkg>          # updates pyproject + lock
.venv/bin/pip install <pkg>             # keep the root venv in sync (lint uses it)
```

```bash
make lint                               # ruff + pyright + pytest + frontend lint (run from repo root)
cd backend && poetry run pytest tests/  # tests only
cd backend && poetry run alembic revision --autogenerate -m "msg"
cd backend && poetry run alembic upgrade head
docker compose up -d postgres redis     # local infra (postgres published on :5433)
docker compose up --build               # full stack behind nginx on :80
celery -A src.celery_app.celery worker --loglevel=info   # from backend/
celery -A src.celery_app.celery beat   --loglevel=info
```

Local dev DB URL uses port **5433** (host has another Postgres on 5432). Inside
docker the backend talks to `postgres:5432`.

## Testing

- Layout mirrors `src/` under `tests/` (packages have `__init__.py` so duplicate
  filenames like `test_scope.py` don't clash).
- `tests/conftest.py` provides `session` (mock `AsyncSession`: io methods are
  `AsyncMock`, `add`/`add_all` are sync) and `make_result` (factory for mock
  `execute(...)` results). It also sets test secrets in the environment.
- Repositories: mock the session, assert the method returns the unwrapped result
  and calls the right session io. Real SQL is not exercised by unit tests.
- Services/views: mock repositories and other services; assert delegation, schema
  mapping, and that secrets (`ip_hash`, `password_hash`) never leak into responses.
- `asyncio_mode = "auto"` (pytest-asyncio) — `async def test_*` runs directly.
- Tooling friction is handled centrally: ruff `flake8-bugbear.extend-immutable-calls`
  whitelists FastAPI `Depends/Header/Query/Path/File`; pyright
  `executionEnvironments` relax DI-only diagnostics for `routers`/`views`/`tasks`.
  Prefer these over scattering `# type: ignore`.

## Realtime (websocket)

- `utils/events.py` — `EventPublisher` publishes JSON envelopes
  (`{"type", "data"}`) to redis pub/sub. Channels: `ws:thread:{thread_id}` and
  `ws:board:{board_slug}`. Event types: `new_post`, `post_edited`, `new_thread`.
- Publishing happens in the **views** (presentation side-effect) right after the
  service call, using the response schema as the payload.
- `WsView` (`views/ws_view.py`) subscribes a socket to a channel and forwards
  messages; a drain task detects client disconnect. Endpoints:
  `GET /api/{board_slug}/threads/{thread_id}/ws` and `GET /api/{board_slug}/ws`.
- nginx already passes the `Upgrade`/`Connection` headers for ws.

## Not yet built

- File uploads are a **separate endpoint**
  (`POST /api/{board_slug}/posts/{post_number}/attachments`), not part of the
  JSON post/thread create bodies. The OP-must-have-image rule is not enforced yet.
- Events are published **before** the request transaction commits (a rolled-back
  write would still have notified). Acceptable today because services validate
  before writing; revisit if writes can fail post-validation.
- No integration tests against a real database/redis — units only so far.
