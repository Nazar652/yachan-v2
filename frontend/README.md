# yachan-v2 — frontend

The **Vue 3 single-page app** for the yachan imageboard: board catalog, threads,
posting with attachments, realtime updates, and a moderator panel.

For architecture and conventions see [`CLAUDE.md`](CLAUDE.md) in this folder; this
README is the human quick-start.

## Stack

Vue 3 (`<script setup lang="ts">`) · Vite · Vue Router · **Pinia** (client-only
state) · **TanStack Vue Query** (server state) · Tailwind CSS v4 ·
`openapi-typescript` + `openapi-fetch` (typed API) · Vitest + Vue Test Utils.

## Prerequisites

Node `^20.19 || >=22.12`. The backend should be running (locally on
`http://localhost:8000`, or the full stack via Docker).

## Quick start

```bash
npm install                  # .npmrc already sets legacy-peer-deps=true
cp .env.example .env         # VITE_API_BASE_URL=http://localhost:8000
npm run dev                  # Vite dev server (default http://localhost:5173)
```

In production the SPA is built and served by **nginx** (see `nginx.conf` and the
root `docker-compose.yml`); there `VITE_API_BASE_URL` is empty so the app talks to
the same origin (`/api`, `/media`, ws).

## Scripts

```bash
npm run dev          # dev server with HMR
npm run build        # type-check + production build (dist/)
npm run type-check   # vue-tsc --build
npm run lint         # oxlint + eslint (autofix)
npm run test:unit    # Vitest (watch); add `-- --run` for a single pass
```

## Typed API

Types are generated from the backend OpenAPI schema into `src/api/schema.d.ts`
(do not edit by hand). Regenerate after any backend change, from the repo root:

```bash
make openapi         # dumps openapi.json + runs gen:api here
```

Import friendly aliases from `src/api/types.ts` (`PostResponse`,
`ThreadDetailResponse`, …) rather than the generated schema directly.

## Project structure

```
src/
  api/           typed client + per-resource wrappers (boards, threads, mod, ws, …)
  composables/   Vue Query wrappers + realtime + moderation helpers
  components/     ReplyForm, layout/, ui/ (BaseButton, BaseCard, BaseInput, CaptchaWidget)
  views/          BoardList, Catalog, CreateThread, Thread, mod/(Login, Dashboard)
  stores/         auth (mod JWT, the only Pinia state)
  router/         routes + auth guard
  assets/main.css design tokens (@theme) + base styles
  main.ts         app bootstrap (Pinia + Vue Query + router)
```

## Tests

```bash
npm run test:unit -- --run
```

Every composable and component has a unit test. Server state is mocked at the
composable boundary; the typed client and `fetch` are mocked in API-wrapper tests.
See [`CLAUDE.md`](CLAUDE.md) for the test patterns.
