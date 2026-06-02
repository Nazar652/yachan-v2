# yachan-v2

Anonymous imageboard. **Async FastAPI backend** (strict layered architecture,
request-scoped DI via kink) + **Vue 3 SPA frontend**, backed by Postgres, Redis
and Celery, all runnable via Docker Compose.

This root file covers project-wide conventions and Docker/infra. For area detail
see the contextual guides (Claude Code auto-loads them when you work in that dir):

- **`backend/CLAUDE.md`** — layered architecture, DI, request lifecycle, domain
  model, technical decisions, CLI, backend testing.
- **`frontend/CLAUDE.md`** — Vue/Vite stack, API layer, composables, realtime,
  mod panel, frontend testing.

## Conventions (apply everywhere)

- **Full names, no abbreviations.** `redis_client`, not `r`; `derived_key`, not `dk`.
- **No leading underscores on variables / instance attributes.** Leading `_` is
  only for module-private constants, functions and methods. (Language specifics in
  each sub-guide.)
- **Comments:** sparse, only for non-obvious logic. Natural prose, lowercase, no
  decorative separators.
- **Every method / composable / component gets a unit test**, added in the same
  change as the code. Pure unit tests — mock the dependencies.
- **End every change with lint fully green:** `make lint` (ruff + pyright + pytest
  + frontend lint). Run frontend `type-check` and `test:unit` separately too — the
  `make lint` frontend step only runs `npm run lint`.

## Top-level layout

```
backend/         FastAPI app, Celery, alembic migrations, admin cli  (see backend/CLAUDE.md)
frontend/        Vue 3 SPA + its nginx edge config                   (see frontend/CLAUDE.md)
frontend/nginx.conf   serves the SPA, proxies /api (+ws) and /media
docker-compose.yml    postgres, redis, migrate, backend, celery-worker, celery-beat, nginx
.env / .env.example   compose ${VAR} interpolation (gitignored / template)
Makefile              `make lint`, `make openapi`
```

## Dependencies

Add deps via the tool, never by hand-editing manifests.

- **Backend:** Poetry targets the **root `.venv`** (`backend/poetry.toml` sets
  `virtualenvs.create = false`). Activate `.venv` first, then a single
  `poetry -C backend add <pkg>` updates `pyproject`+lock and installs into `.venv`
  — no separate `pip install`. Without activation it hits the base interpreter, so
  **always activate first**:
  ```bash
  source .venv/Scripts/activate          # Windows; .venv/bin/activate on unix
  poetry -C backend add <pkg>
  ```
- **Frontend:** `cd frontend && npm install <pkg> --legacy-peer-deps`.

## Docker / infra

```bash
docker compose up --build        # whole stack -> http://localhost (nginx :80)
docker compose down              # stop  (add -v to also drop the db + media volumes)
docker compose exec backend python -m src.cli create-admin <username>   # seed a mod
```

Services and wiring:
- **postgres** (17) + **redis** (7) with healthchecks; **postgres** is published
  on host **:5434** (this machine already runs native PostgreSQL on 5432/5433,
  which would otherwise shadow the published port). Inside the network the backend
  talks to `postgres:5432`, `redis:6379`.
- **migrate** — one-shot `alembic upgrade head`; backend/celery wait on it via
  `service_completed_successfully`, so the schema is up before any app process
  starts (race-free, runs once regardless of replicas).
- **backend** (uvicorn), **celery-worker**, **celery-beat** share the backend
  image (build sets `POETRY_VIRTUALENVS_CREATE=false`, installs into the
  container's system Python — no venv inside the image).
- **nginx** is built from `frontend/` (multi-stage: vite build → nginx). It serves
  the SPA (`try_files … /index.html`), reverse-proxies `/api/` (with WebSocket
  upgrade headers) to the backend, and serves `/media/` from the shared
  **`media_data`** volume (where the backend/worker write uploads).

### Environment variables

- Compose interpolates `${VAR}` (POSTGRES_USER/PASSWORD/DB, JWT_SECRET,
  IP_HASH_SALT) from the **root `.env`** (next to `docker-compose.yml`). Copy
  `.env.example` → `.env` and fill values; all vars have dev defaults so the stack
  also comes up without a `.env`.
- The root `.env` is **interpolation only** — values reach containers because
  `environment: <<: *app-env` forwards them. The backend `.env` file is excluded
  from the image; in Docker the backend reads pure env vars.
- `POSTGRES_PASSWORD` is applied **only at first init** of an empty `postgres_data`
  volume; change it later via `ALTER USER` or recreate the volume (`down -v`).
- `JWT_SECRET` ≥ 32 bytes in production. In production inject secrets via the
  platform/orchestrator (Vault, k8s/Swarm secrets, env), not a committed file.

`make openapi` dumps the backend OpenAPI schema and regenerates the frontend's
`src/api/schema.d.ts` — run it after any backend schema change.
