# yachan-v2

> A modern, full-stack **anonymous imageboard** — async FastAPI backend + Vue 3
> SPA, with realtime updates, moderation, and one-command Docker deployment.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-v4-06B6D4?logo=tailwindcss&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

## Features

- **Anonymous posting** — no accounts for posters; per-board sequential post
  numbers.
- **Threads & replies** with image/video attachments (async thumbnailing),
  markdown rendering, greentext and `>>N` backlinks.
- **Tripcodes** — a `#password` suffix in the name field yields a stable tripcode.
- **Realtime** — new posts, edits and threads stream over WebSocket (Redis
  pub/sub) into the open page.
- **Anti-spam** — image CAPTCHA and Redis-backed rate limiting.
- **Moderation** — JWT mod login, reports queue, delete posts, lock/sticky
  threads, ban by IP hash (per-board or global).
- **Privacy** — poster IPs are salted-hashed and never exposed.

## Tech stack

| Area      | Technologies |
|-----------|--------------|
| Backend   | FastAPI · SQLModel · asyncpg / PostgreSQL · Redis · Celery · kink (DI) · Alembic |
| Frontend  | Vue 3 (`<script setup>`) · Vite · Vue Router · Pinia · TanStack Vue Query · Tailwind CSS v4 · openapi-fetch |
| Infra     | Docker Compose · nginx (edge: SPA + reverse proxy) |
| Tests     | pytest (backend) · Vitest + Vue Test Utils (frontend) |

## Architecture

```
   browser ──▶ nginx (:80) ──┬─▶ SPA static assets
                             ├─▶ FastAPI         (REST + WebSocket)
                             └─▶ /media          (shared volume)

   FastAPI       ──▶ PostgreSQL    (data)
   FastAPI       ──▶ Redis         (ws pub/sub · rate limiting · Celery broker)
   FastAPI       ──▶ Celery        (enqueues process_attachment)

   Celery worker ──▶ PostgreSQL + media   (thumbnails, dimensions)
   Celery beat   ──▶ Redis                (periodic schedule)
```

Uploads written by the backend/worker land in a shared `media_data` volume that
nginx serves at `/media`. Realtime events are fan-outed via Redis pub/sub (FastAPI
publishes, then forwards to subscribed sockets). A one-shot `migrate` service runs
Alembic migrations before the app starts.

## Quick start (Docker)

```bash
git clone <repo> && cd yachan-v2
cp .env.example .env          # fill in secrets (or keep dev defaults)
docker compose up --build     # builds the SPA + backend images and starts everything
```

Then open **http://localhost**. Create a moderator account:

```bash
docker compose exec backend python -m src.cli create-admin <username>
```

> Note: the dockerized PostgreSQL is published on host port **5434** (5432/5433
> are assumed to be taken by a native install). See the root `CLAUDE.md` for the
> full infra/`.env` reference.

## Repository structure

```
backend/     FastAPI app, Celery tasks, Alembic migrations, admin CLI   → backend/README.md
frontend/    Vue 3 SPA + its nginx edge config                          → frontend/README.md
docker-compose.yml   postgres, redis, migrate, backend, celery×2, nginx
Makefile             make lint-all · make openapi
```

## Local development

Run the pieces natively for a fast inner loop — see the per-area guides:

- **[backend/README.md](backend/README.md)** — Poetry, uvicorn, pytest, migrations.
- **[frontend/README.md](frontend/README.md)** — npm, Vite dev server, Vitest.

Lint everything from the repo root:

```bash
make lint-all        # ruff + pyright + pytest + frontend lint
```

## Contributing / AI agents

Architecture and working conventions are documented for contributors (and coding
agents) in `CLAUDE.md` files: a project-wide one at the root, plus detailed
`backend/CLAUDE.md` and `frontend/CLAUDE.md`.
