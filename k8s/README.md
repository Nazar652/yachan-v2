# yachan-v2 — Kubernetes (k3s)

Kubernetes manifests for the whole stack, as an alternative to `docker-compose`.
The real target is a **single-node k3s on Hetzner**; local iteration uses **k3d**
(k3s-in-Docker), so the same manifests port over 1:1.

**Two independent manifest sets that share only Redis:**

- **yachan set** — `base/` + `overlays/{dev,prod}` (namespace `yachan`): postgres,
  redis, minio, backend, celery worker/beat, nginx + ingress.
- **moderation set** — `moderation/` (namespace `moderation`): the stateless
  moderation worker. Reaches the broker cross-namespace at
  `redis.yachan.svc.cluster.local`.

They are applied separately (`kubectl apply -k …` each). No GPU anywhere — the ML
is CPU onnx (baked into the images) plus Gemini via API.

## Layout

```
k8s/
  base/                       yachan set — shared across dev/prod
    namespaces.yaml           namespace: yachan
    redis.yaml                Deployment + Service (broker; in-cluster in dev and prod)
    backend.yaml              migrate Job + backend Deployment (initContainer waits on migrations) + Service
    celery.yaml               celery-worker (-Q celery,moderation_results) + celery-beat
    nginx.yaml                edge Deployment (SPA + /api + /media proxy) + Service
    ingress.yaml              Traefik Ingress → nginx:80
    secret.example.yaml       documented template for the yachan Secret (NOT applied)
  overlays/
    dev/                      in-cluster postgres + minio + createbucket, dev config + secret
    prod/                     Neon/R2 config template; secret injected out-of-band
  moderation/                 moderation set — namespace, config, worker Deployment
```

## Prerequisites

- Docker (k3d runs the k3s node as a container).
- [`k3d`](https://k3d.io) ≥ 5.9 and `kubectl` (Docker Desktop ships one; it bundles
  Kustomize, so `kubectl apply -k` works with no extra tools).

## Local quickstart (k3d)

```bash
# 1. cluster — publish host :8081 → Traefik :80 (fixed at create time)
k3d cluster create yachan --servers 1 --port "8081:80@loadbalancer" --wait

# 2. build the three images and import them into the cluster (no registry locally)
docker build -t yachan-backend:dev ./backend
docker build -t yachan-moderation:dev ./moderation
docker build -t yachan-nginx:dev ./frontend
k3d image import yachan-backend:dev yachan-moderation:dev yachan-nginx:dev -c yachan

# 3. apply both sets
kubectl apply -k k8s/overlays/dev
kubectl apply -k k8s/moderation

# 4. open the app
#    http://localhost:8081

# 5. seed a mod account (interactive password prompt)
kubectl -n yachan exec -it deploy/backend -- python -m src.cli create-admin <username>
```

Images use `imagePullPolicy: IfNotPresent` and a fixed `:dev` tag, so k3d serves the
imported image and never tries to pull. After rebuilding an image, re-run
`k3d image import …` and delete the pods (`kubectl -n yachan delete pod -l app=backend`)
so the new image is picked up (the tag does not change, so pods don't auto-roll).

## How it maps from docker-compose

- **Startup ordering** (`depends_on: service_completed_successfully`) → one-shot
  **Jobs** (`migrate`, `createbucket`) plus an **initContainer** on backend/worker/beat
  that blocks until migrations are applied (a small Python `asyncpg` loop that polls
  `alembic_version` via `DATABASE_URL` — works identically against in-cluster postgres
  and Neon, no kubectl/RBAC needed). `migrate` uses `backoffLimit`, so if the DB is not
  up yet the Job just retries.
- **Service discovery** — compose service names become Services. nginx keeps the bare
  names `backend:8000` / `minio:9000` from `nginx.conf`, so nginx, backend and minio must
  stay in the same namespace (`yachan`).
- **Config vs secrets** — `x-app-env` is split into a ConfigMap (URLs, bucket,
  `STORAGE_BACKEND`) and a Secret (`DATABASE_URL`, `JWT_SECRET`, `IP_HASH_SALT`, S3 keys,
  `GEMINI_API_KEY`). See `base/secret.example.yaml`.
- **Storage** — postgres/minio use PVCs on the k3s `local-path` StorageClass. In k3d the
  bytes live inside the node container (`/var/lib/rancher/k3s/storage/…`); they survive pod
  restarts and `k3d cluster stop/start`, but not `k3d cluster delete`.

## Production (Hetzner)

Same images, `overlays/prod` swaps the in-cluster data layer for managed services (mirrors
`docker-compose.prod.yml`):

- postgres/minio/createbucket are **not** deployed — `DATABASE_URL` points at Neon,
  S3 vars at Cloudflare R2. `overlays/prod/yachan-config.yaml` carries the non-secret prod
  values (fill the `REPLACE_WITH_…` placeholders); the Secret is injected out-of-band, e.g.
  `kubectl create secret generic yachan-secret -n yachan --from-env-file=prod-secret.env`
  (that file is gitignored — see `k8s/.gitignore`).
- Still TODO for the real deploy: image distribution (a registry / GHCR, or
  `k3s ctr images import`), TLS on the Traefik Ingress, and a prod nginx config
  (`nginx.prod.conf`, no `/media` proxy).

## Resource notes

k3s + the full stack wants more than a ~2 GiB Docker VM — below that the node flaps
`NodeNotReady` and probes time out. Give Docker Desktop **≥4 GiB** (Settings → Resources on
the Hyper-V backend; `.wslconfig` on WSL2). The celery worker runs `--concurrency=1` and all
probes carry generous `timeoutSeconds`/`failureThreshold` to tolerate a busy single node.
