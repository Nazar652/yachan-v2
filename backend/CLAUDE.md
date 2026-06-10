# yachan-v2 — backend

Async FastAPI backend for an anonymous imageboard, with a strict layered
architecture and request-scoped dependency injection via **kink**. Read this
before changing backend code; see the repo-root `CLAUDE.md` for project-wide
conventions and Docker/infra, and `frontend/CLAUDE.md` for the SPA.

## Conventions (backend specifics)

Project-wide rules (full names, no leading underscores, sparse comments, a unit
test for every method, lint green at the end) live in the root `CLAUDE.md`.
Python specifics:

- **Full names, no abbreviations.** `redis_client`, not `r`; `derived_key`, not `dk`.
- **No leading underscores on variables or instance attributes.** `self.session`,
  not `self._s`. Leading `_` is allowed only on module-private constants
  (`_ALPHABET`), private functions (`_prompt_password`), and private methods
  (`_full_path`).
  - Exception: a name dictated by an external typed API stays as required, e.g.
    the mistune plugin parameter must be `md` (see `src/utils/markup.py`).

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
    utils/                 standalone helpers: clock, ip, names, tripcode, sequences,
                           markup, captcha, auth, rate_limit, events
    models/                SQLModel tables, pure data, no logic
    repositories/          all SQL, one class per model, @inject
    schemas/               pydantic request/response, no db awareness
    services/              all business logic, @inject
    views/                 class-based http entrypoints, @inject
    routers/               FastAPI routers, Depends(_view) bridge
    tasks/                 Celery tasks (ScopedTask), thin wrappers over services
    cli/                   argparse admin cli (create-admin, dump-openapi)
  alembic/                 async migrations
  tests/                   mirrors src/, pure unit tests
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
  `Storage`, `Redis`, `RateLimiter`. `di[Storage]` is built by
  `build_storage(settings)` — `LocalStorage` or `S3Storage` per `STORAGE_BACKEND`.
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

`CORSMiddleware` is added last so it is the **outermost** middleware — cors
preflight is answered before a db scope is opened. Allowed origins come from
`Settings.cors_origins` (comma-separated env `CORS_ORIGINS`), exposed as the
`cors_origin_list` property.

## Domain model

Anonymous imageboard — no user accounts for posters.

- `Board` — `slug` (unique, `^[a-z0-9_]{1,20}$`), `title`, `bump_limit`.
  Each board owns a Postgres sequence `post_number_seq_{slug}` for per-board post
  numbering (see `utils/sequences.py`, created in `BoardService.create_board`).
- `Thread` — belongs to a board; `is_locked`, `is_sticky`, `reply_count`,
  `bump_at` (catalog ordering). `reply_count` is incremented on every reply
  (`thread_repo.increment_reply_count`), independent of `sage`.
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
  `bearer_token` dependency (`views/dependencies.py`) extracts the token; mod
  views validate it and load the `ModAccount`.

## Auditing

Every change to the domain tables is recorded by **Postgres triggers**, not the
ORM — so it captures *all* writes, including raw SQL / `psql`, not just app
traffic. That's deliberate: an ORM-level audit would miss a stray manual `DELETE`,
which is exactly the kind of thing we want to catch.

- **`audit_log`** (`models/audit_log.py`) — one row per change: `table_name`,
  `op` (INSERT/UPDATE/DELETE), `row_data` (the new row, or the old row on delete),
  `old_data` (the pre-image on update), `txid` (`txid_current()`, groups a
  transaction's changes), `at` (tz-aware UTC, written by the trigger as `now()`).
  The trigger writes the rows; the model
  exists only so Alembic owns the table and the app can read the trail. The table
  is **not** audited itself (would recurse). No actor/"who" column by design — it
  answers *what changed, when, in which transaction*.
- **`audit_log_changes()`** — one generic `plpgsql` function, attached as an
  `AFTER INSERT OR UPDATE OR DELETE … FOR EACH ROW` trigger named `audit_<table>`
  on each domain table.
- **`audit_new_tables`** — a DDL **event trigger** on `CREATE TABLE` that
  auto-attaches `audit_<table>` to any new table (excluding `audit_log` and
  `alembic_version`). So a new `op.create_table` is audited **automatically** — do
  **not** add `CREATE TRIGGER audit_*` by hand in migrations (you'd get "already
  exists"). Creating an event trigger needs a **superuser** role: the local docker
  `yachan` user is one; in production run that DDL as a superuser.
- Two migrations own this: `…add_audit_log_table_and_triggers` (table + function +
  the initial per-table triggers) and `…auto_attach_audit_trigger_to_new_tables…`
  (the event trigger). Neither is autogenerated — triggers/functions aren't tracked
  by Alembic, so they live in hand-written `op.execute` bodies.

Read the trail with plain SQL, e.g.
`SELECT op, table_name, at FROM audit_log WHERE table_name = 'board' ORDER BY id DESC`.

## API surface

```
GET    /api/boards                                   -> BoardResponse[]
GET    /api/{slug}/threads                           -> ThreadResponse[]
POST   /api/{slug}/threads                           -> ThreadDetailResponse (201)
       headers X-Captcha-Token, X-Captcha-Answer; multipart title?,name?,body?,sage,files[]
GET    /api/{slug}/threads/{id}                       -> ThreadDetailResponse
POST   /api/{slug}/threads/{id}/posts                 -> PostResponse (201)
       headers X-Captcha-Token, X-Captcha-Answer; multipart name?,body?,sage,files[]
PATCH  /api/{slug}/posts/{post_number}                -> PostResponse (edit window)
GET    /api/{slug}/posts/{post_number}/history        -> PostEditResponse | null
POST   /api/{slug}/posts/{post_number}/report
GET    /api/captcha                                   -> CaptchaChallengeResponse

POST   /api/mod/login                                 -> TokenResponse
POST   /api/mod/boards                                -> BoardResponse (201)
GET    /api/mod/reports[?board_id=]                   -> ReportResponse[]
POST   /api/mod/reports/{id}/resolve                  (204)
DELETE /api/mod/{slug}/posts/{post_number}            (204)
POST   /api/mod/{slug}/threads/{id}/lock[?locked=]    (204, query bool)
POST   /api/mod/{slug}/threads/{id}/sticky[?sticky=]  (204, query bool)
POST   /api/mod/{slug}/posts/{post_number}/ban        -> BanResponse (201, body BanCreate)

WS     /api/{slug}/threads/{id}/ws                    (not in OpenAPI)
WS     /api/{slug}/ws                                 (not in OpenAPI)
```

## Important technical decisions

- **Timestamps are tz-aware UTC.** Columns are `TIMESTAMP WITH TIME ZONE`
  (timestamptz) — declared via the shared `utils/types.TZDateTime` SA type, which
  every datetime column passes as `sa_type`. asyncpg round-trips tz-aware values,
  so the offset reaches clients (pydantic serializes `…+00:00`) and the browser
  renders local time. Always use `utils/clock.utcnow()` (aware UTC,
  `datetime.now(UTC)`) for defaults and comparisons, never `datetime.utcnow()`
  (deprecated) or a naive datetime — comparing aware vs naive raises `TypeError`.
- **Every table model carries `created_at` + `updated_at`** via `TimestampMixin`
  (`models/timestamp_mixin.py`); `updated_at` is bumped on each ORM update through
  the column's `onupdate=utcnow`.
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
- **Required settings** `JWT_SECRET` and `IP_HASH_SALT` have no defaults. Locally
  they live in `backend/.env` (absolute path resolution via
  `Path(__file__).parents[2]/.env`, so any cwd works); in Docker they come from
  env vars (the file is excluded from the image). Tests set them in
  `tests/conftest.py` before importing `src`.
- **Celery + async:** `ScopedTask.__call__` runs the async `run()` via
  `asyncio.run`. Therefore task tests must be **synchronous** (calling a task from
  an async test would nest event loops). Each task gets its **own** `asyncio.run`
  loop, and asyncpg connections are loop-bound — so `ScopedTask` calls
  `get_engine().dispose()` after a task that used a session; otherwise the next
  task reuses a pooled connection from a dead loop and raises *"got Future attached
  to a different loop"* (the symptom that broke `process_attachment` in prod).
- **Per-board sequence names** are built only via
  `utils/sequences.post_number_sequence_name(slug)`, which validates the slug
  because it is interpolated into raw DDL.

## Observability (Sentry)

`core/sentry.py` `init_sentry(settings)` is a **no-op unless `SENTRY_DSN` is set**,
so local and test runs never touch Sentry. It is called **once per OS process**:
`create_app()` (web), the `worker_process_init` signal (Celery worker) and
`beat_init` (beat) — the prefork model forks *after* the parent starts, so each
child must init its own client (init-before-fork breaks the transport). The
FastAPI/Starlette, Celery and Redis integrations auto-enable. Every error carries a
stacktrace automatically; tracing (`SENTRY_TRACES_SAMPLE_RATE`, default `1.0`) adds
performance transactions/spans. PII stays off (Sentry default) — poster IPs are
hashed and must never reach Sentry.

## Realtime (websocket)

- `utils/events.py` — `EventPublisher` publishes JSON envelopes
  (`{"type", "data"}`) to redis pub/sub. Channels: `ws:thread:{thread_id}` and
  `ws:board:{board_slug}`. Event types: `new_post`, `post_edited` (carry
  `PostResponse`), `new_thread` (carries `ThreadDetailResponse`).
- Publishing happens in the **views** (presentation side-effect) right after the
  service call, using the response schema as the payload.
- `WsView` (`views/ws_view.py`) subscribes a socket to a channel and forwards
  messages; a drain task detects client disconnect. Endpoints:
  `GET /api/{board_slug}/threads/{thread_id}/ws` and `GET /api/{board_slug}/ws`.
- nginx passes the `Upgrade`/`Connection` headers for ws (see `frontend/nginx.conf`).

## Attachments (uploads)

- Threads and replies are created with **multipart** requests: form fields map to
  `ThreadCreate`/`PostCreate` via `Annotated[Model, Form()]`, files come as
  `files: list[UploadFile]`. Up to 10 attachments per post (`MAX_ATTACHMENTS`).
- `views/uploads.py` — `read_uploads` reads non-empty files and validates type
  (`FileService.media_type_for`) and count up front, before any db write;
  `contains_image` decides the OP-image rule; `store_uploads` stores each via
  `FileService` and enqueues `process_attachment.delay`.
- `views/serializers.py` — builds `AttachmentResponse`/`PostResponse` with public
  URLs from `Storage.public_url` (`storage_base_url` = `/media`; nginx proxies
  `/media/` to the minio bucket, or in prod set it to the bucket/CDN url).
- **Storage backends** (`core/storage.py`): `Storage` (ABC) defines
  `save/read/delete/exists/public_url`. `LocalStorage` writes to the filesystem;
  `S3Storage` (boto3, path-style addressing) targets any s3-compatible store —
  minio in docker, AWS S3 in prod. The backend is selected once in DI via
  `build_storage`; `FileService` and the views depend only on the `Storage`
  abstraction.
- Rule: a **new thread's OP must include an image** (`ThreadService` raises
  `OpRequiresImageError` when `has_image` is false). Replies may have no image.
- `create_thread` returns a `ThreadDetailResponse` (the OP post + its attachments);
  `create_reply` returns the `PostResponse` with attachments.

## Admin CLI

`src/cli/` is a small argparse package: `__main__.py` registers command modules
(each exposes `COMMAND`, `HELP`, `configure(parser)`, `handle(args)`),
`scope.py` provides `run_in_scope()` (opens a di scope, commits/rolls back/closes
like the http middleware), and one file per command (e.g. `create_admin.py`,
`dump_openapi.py`). Add a command by creating a module and listing it in
`__main__.COMMANDS`. Account creation logic lives in `ModService.create_account`
(hashes the password, rejects duplicate usernames), not in the cli.

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

## Commands

Backend tooling runs in the **root `.venv`** (used by `make lint`/pyright/hooks),
which Poetry is also pointed at (`backend/poetry.toml` → `virtualenvs.create =
false`). Activate `.venv` first, then `poetry` installs into it — see the root
`CLAUDE.md` for the dependency workflow.

```bash
cd backend && poetry run pytest tests/                       # tests only
cd backend && poetry run alembic revision --autogenerate -m "msg"
cd backend && poetry run alembic upgrade head
cd backend && poetry run python -m src.cli create-admin <username>   # prompts for password
celery -A src.celery_app.celery worker --loglevel=info       # from backend/
celery -A src.celery_app.celery beat   --loglevel=info
make openapi                                                  # dump openapi.json + regen frontend types
```

`JWT_SECRET` should be **at least 32 bytes** in production (pyjwt warns otherwise).

## Not yet built

- Files are written to storage inside the request; on a later rollback they are
  **not** cleaned up (orphaned blobs). Acceptable today; add a sweep task if needed.
- Events are published **before** the request transaction commits (a rolled-back
  write would still have notified). Acceptable today because services validate
  before writing; revisit if writes can fail post-validation.
- No integration tests against a real database/redis — units only so far.
