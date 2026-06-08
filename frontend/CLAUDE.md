# yachan-v2 — frontend

Vue 3 SPA for the imageboard. Read this before changing frontend code; see the
repo-root `CLAUDE.md` for project-wide conventions and Docker/infra, and
`backend/CLAUDE.md` for the API it consumes.

## Stack

- **Vue 3** with `<script setup lang="ts">` everywhere.
- **Vite** (build/dev), **Vue Router** (history mode), **Pinia** (client-only
  state — only the mod JWT), **TanStack Vue Query** (all server state).
- **Tailwind CSS v4** (`@tailwindcss/vite`), `tailwind-variants` for component
  variants, `tailwind-merge`.
- **Typed API**: `openapi-typescript` generates types from the backend OpenAPI
  schema; `openapi-fetch` is the typed HTTP client.
- **Vitest** + `@vue/test-utils` (jsdom) for unit tests.
- Node `^20.19 || >=22.12`. `.npmrc` sets `legacy-peer-deps=true`.

## Conventions

Project-wide naming/comment/test/lint rules live in the root `CLAUDE.md` and
apply here too (full names, no leading underscores, sparse lowercase comments, a
test for every composable/component, lint green at the end). Frontend specifics:

- **Server state vs client state.** Anything from the API goes through a Vue Query
  composable in `src/composables/` — never Pinia. Pinia holds only pure client
  state (the mod auth token).
- **Typed API, one source.** Types are generated into `src/api/schema.d.ts`
  (gitignored from lint). Friendly aliases live in `src/api/types.ts` — import
  those (`PostResponse`, `ThreadDetailResponse`, …), never
  `components['schemas'][...]` directly.
- **Per-resource API wrappers** in `src/api/<resource>.ts`: thin async functions
  over `apiClient.GET/POST/...` that unpack `{ data, error }`, `throw error`, and
  return `data` (so Vue Query owns loading/error/retry). For **multipart**
  endpoints use native `fetch` + `FormData` directly (openapi-fetch doesn't
  cleanly handle nested form schemas) — see `api/threads.ts` `createThread`/
  `createReply`.
- **"Change a colour in one place."** Colours/radii are design tokens in
  `src/assets/main.css` `@theme`. Reusable look lives in base components
  (`src/components/ui/Base*.vue`). Pages compose those and do **not** repeat
  tailwind colour classes.

## Design tokens (`src/assets/main.css` `@theme`)

```
--color-bg           #d6daf0    body background
--color-surface      #eef2ff    cards, inputs
--color-surface-2    #d6daf0    secondary surfaces
--color-border       #b7c5d9
--color-text         #0f0c0c
--color-text-muted   #707070    (class: text-text-muted)
--color-accent       #34345c    (text-accent / bg-accent)
--color-accent-hover #28284a
--color-danger       #af0a0f    (text-danger)
--color-greentext    #789922
--radius-card        4px
```

## Layout

```
frontend/src/
  api/
    client.ts          apiClient = createClient<paths>({ baseUrl: VITE_API_BASE_URL });
                       authMiddleware injects `Authorization: Bearer <token>`
    schema.d.ts        generated — do not edit (run `make openapi`)
    types.ts           friendly aliases over components['schemas']
    boards.ts          listBoards()
    captcha.ts         fetchCaptcha()
    threads.ts         listThreads, getThread, createThread (multipart), createReply (multipart)
    mod.ts             modLogin, listReports, resolveReport, deletePost,
                       setThreadLocked, setThreadSticky, banPoster
    ws.ts              toWsBase(), wsUrl(), WS_EVENT, WsEnvelope (ws is not in OpenAPI)
    __tests__/         boards, captcha, threads, mod, client, ws
  composables/
    useBoards.ts            useBoards + boardsQueryKey
    useCaptcha.ts           useCaptcha (staleTime 0, gcTime 0 — single-use images)
    useThreads.ts           useThreads(slug) + threadsQueryKey
    useThread.ts            useThread(slug, id) + threadQueryKey + appendPostToThread()
    useThreadWs.ts          per-thread realtime: merges new_post/post_edited into cache
    useBoardWs.ts           per-board realtime: prepends new_thread into the catalog cache
    useReports.ts           useReports + reportsQueryKey
    useModeration.ts        thread-scoped mod actions (setLocked/setSticky/removePost/ban)
    useCatalogModeration.ts catalog-scoped mod actions (setLocked/setSticky)
    __tests__/              useThread, useThreadWs, useBoardWs, useModeration, useCatalogModeration
  components/
    ReplyForm.vue           reply form mounted at the bottom of ThreadView
    layout/AppHeader.vue    logo + mod login/panel link
    ui/                     BaseButton, BaseCard, BaseInput, CaptchaWidget
    __tests__/              component specs
  views/
    BoardListView.vue       GET /api/boards
    CatalogView.vue         GET /api/{slug}/threads + board realtime + catalog mod actions
    CreateThreadView.vue    multipart create-thread form (OP image required)
    ThreadView.vue          GET /api/{slug}/threads/{id} + thread realtime + reply form + mod actions
    mod/ModLoginView.vue    login form -> modLogin -> auth.login -> /mod
    mod/ModDashboardView.vue reports list + resolve + logout
    __tests__/              view specs
  stores/
    auth.ts                 useAuthStore: token (localStorage), isAuthenticated, login, logout
    __tests__/auth.spec.ts
  router/index.ts           routes + exported authGuard (redirects requiresAuth -> /mod/login)
  assets/main.css           @theme design tokens + body styles
  main.ts                   createPinia + VueQueryPlugin (staleTime 30s, retry 1) + router
  App.vue                   AppHeader + <main><RouterView /></main>
```

Env: `VITE_API_BASE_URL` (`.env.example` → `http://localhost:8000` for dev).
In the Docker image it is built **empty**, so the SPA talks to the same origin
(`/api`, `/media`, ws) behind nginx.

## API layer

- `client.ts` — the single typed `apiClient`. `authMiddleware` (exported for
  tests) resolves `useAuthStore()` lazily inside `onRequest` and sets the bearer
  header when a token exists. JSON mod endpoints go through `apiClient` so the
  token is injected; the multipart create endpoints use native `fetch` and stay
  public.
- Wrapper pattern: `const { data, error } = await apiClient.GET(path, ...); if
  (error) throw error; return data`. Multipart wrapper builds `FormData` and
  `fetch`es `${VITE_API_BASE_URL}/api/...` with the captcha headers, throwing the
  parsed error body on `!response.ok`.

## Server state (composables)

Thin `useQuery` wrappers that each export a canonical query key (so cache
invalidation references one place), mirroring `useBoards`/`useThreads`.

- `useThread.ts` also exports **`appendPostToThread(thread, post)`** — a pure
  helper that appends a post to a cached `ThreadDetailResponse`, **deduped by
  `post.id`** and bumping `reply_count` (matching the server). Shared by the
  optimistic reply append (`ReplyForm`) and the live `new_post` event
  (`useThreadWs`) so neither doubles the other.

## Realtime (websocket)

WS routes are **not** in the OpenAPI schema, so `api/ws.ts` declares them by hand:
- `toWsBase(apiBase)` rewrites `http→ws` / `https→wss`; `wsUrl(path)` prefixes
  `/api` under the ws base. Base derives from `VITE_WS_BASE_URL` or
  `VITE_API_BASE_URL`.
- Envelope `{ type, data }`; `WS_EVENT` = `new_post` / `post_edited` /
  `new_thread`.
- `useThreadWs(slug, threadId)` (called in `ThreadView`): `new_post` →
  `appendPostToThread`; `post_edited` → replace the post by id. Reconnects on
  param change (`watch`), closes on `onScopeDispose`, ignores malformed frames.
- `useBoardWs(slug)` (called in `CatalogView`): `new_thread` → prepend to the
  threads-list cache (deduped by id).
- No auto-reconnect on drop yet (only on slug/threadId change).

## Mod panel & auth (Pinia)

- `stores/auth.ts` — `useAuthStore` (setup store): `token` initialised from
  `localStorage`, `isAuthenticated` getter, `login(token)`/`logout()` persist to
  `localStorage` (`yachan_mod_token`).
- `router/index.ts` — `/mod/login` (public) and `/mod` (`meta.requiresAuth`);
  exported `authGuard(to)` redirects unauthenticated visitors to `/mod/login`,
  registered via `router.beforeEach`.
- `ModLoginView` → `modLogin` → `auth.login(access_token)` → `/mod`.
  `ModDashboardView` → `useReports` list + per-row Resolve (`resolveReport` then
  invalidate `reportsQueryKey`) + logout.
- **Mod content actions**, gated by `auth.isAuthenticated`:
  - `useModeration(slug, threadId)` (ThreadView): `setLocked`/`setSticky` patch
    the thread-detail cache + invalidate the catalog; `removePost` filters the
    post out of the cache; `ban` calls `banPoster`. UI: a lock/sticky bar plus
    per-post Delete/Ban (inline reason form).
  - `useCatalogModeration(slug)` (CatalogView): `setLocked`/`setSticky` flip the
    flag on the matching item in the threads-list cache. Buttons sit **outside**
    the card's `RouterLink` so a click doesn't navigate.

## Observability (Sentry)

`src/sentry.ts` `initSentry(app, router)` (called in `main.ts` right after
`createApp`, before mount) is a **no-op unless `VITE_SENTRY_DSN` is set**. The DSN
is baked into the bundle at **build time** (Vite env), so prod passes it as a Docker
build arg — `docker-compose.prod.yml` nginx `build.args`, fed by the
`FRONTEND_SENTRY_DSN` secret. Captures Vue + global errors;
`browserTracingIntegration` adds route/performance tracing
(`tracesSampleRate: 1.0`).

## Test patterns (Vitest)

- **API wrapper test:** `vi.mock('@/api/client', () => ({ apiClient: { GET: vi.fn(), ... } }))`,
  assert success returns data and error throws. Multipart/`fetch` wrappers:
  `vi.stubGlobal('fetch', fetchMock)`.
- **View test:** `vi.mock('@/composables/use<X>', ...)` and return a minimal stub
  using `ref(...)` for `data`/`isPending`/`isError`, cast
  `as unknown as ReturnType<typeof use<X>>`. Mock any child composables that hit
  the network or a QueryClient (e.g. `useThreadWs`, `useModeration`) so the mount
  stays isolated. Views using the auth store need `setActivePinia(createPinia())`
  in `beforeEach`.
- **Component test:** pass props directly, stub child components. When a stub
  emits an event the parent listens to (`@click`, `update:modelValue`), declare it
  in the stub's `emits` so it doesn't fire twice.
- **Store test:** `setActivePinia(createPinia())` + `localStorage.clear()` per test.
- **Composable test (query/ws):** mount a tiny host `defineComponent` that calls
  the composable in `setup`, provide a real `QueryClient` via
  `[[VueQueryPlugin, { queryClient }]]`, assert cache via
  `queryClient.getQueryData(...)`. For ws, `vi.stubGlobal('WebSocket', MockWebSocket)`
  that captures instances and fire `instance.onmessage({ data })`.
- Gotcha: the `DELETE` mock in `mod.spec.ts` needs `as never` — a 204
  `FetchResponse` narrows `data` to `undefined` and still requires `response`,
  stricter than the looser GET/POST overloads.

## Commands

Run inside `frontend/`:

```bash
npm install <pkg> --legacy-peer-deps   # add a dependency
npm run dev                            # vite dev server (expects backend on :8000)
npm run type-check                     # vue-tsc --build
npm run lint                           # oxlint + eslint
npm run test:unit -- --run             # vitest once
make openapi                           # (repo root) regenerate src/api/schema.d.ts from the backend
```

`make lint` (repo root) runs `npm run lint` as its frontend step; run
`type-check` and `test:unit` separately to fully verify a change.
