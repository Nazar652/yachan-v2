# yachan-v2 — Kubernetes (k3s), production only

These manifests run the stack on a **single-node k3s on Hetzner**. They are the
**production** deployment — local development uses `docker compose` (k8s on one node
duplicates Docker and costs RAM for no gain, so it is not used locally).

**Two independent manifest sets that share only Redis:**

- **yachan set** — `base/` + `overlays/prod` (namespace `yachan`): redis, backend,
  celery worker/beat, nginx edge. Postgres and object storage are **external**
  (Neon + Cloudflare R2), same as `docker-compose.prod.yml`.
- **moderation set** — `moderation/` (namespace `moderation`): the stateless
  moderation worker. Reaches the broker cross-namespace at
  `redis.yachan.svc.cluster.local`.

Applied separately (`kubectl apply -k` each). No GPU — the ML is CPU onnx (baked
into the images) plus Gemini via API.

## Layout

```
k8s/
  base/                       yachan set — deployment-agnostic app
    namespaces.yaml           namespace: yachan
    redis.yaml                Deployment + Service (broker)
    backend.yaml              migrate Job + backend Deployment (initContainer waits on migrations) + Service
    celery.yaml               celery-worker (-Q celery,moderation_results) + celery-beat
    nginx.yaml                edge Deployment + Service (ClusterIP; prod overlay turns it into a LoadBalancer)
    secret.example.yaml       documented template for the yachan Secret (NOT applied)
  overlays/
    prod/
      kustomization.yaml      ../../base + config + nginx patch + GHCR images
      yachan-config.yaml      non-secret prod env (R2 bucket/endpoint, CORS, domain)
      nginx.yaml              patch: Service -> LoadBalancer :80/:443, mount the origin-cert
      tls-secret.example.yaml documented template for the Cloudflare origin-cert Secret
  moderation/                 moderation set — namespace, config, worker Deployment (concurrency=1)
```

## Images & CI/CD

Images live in **GHCR** (`ghcr.io/nazar652/yachan-{backend,nginx,moderation}`) and are
built by CI — never on the 4 GB server (the ML image would OOM). The nginx image is
built with `--build-arg NGINX_CONF=nginx.prod.conf` (Cloudflare real-ip + origin-cert,
no `/media` proxy — media is served straight from R2).

Pipeline (`.github/workflows/deploy.yml`, triggered by a green `CI` run on `master`):

1. **build-push** — build the three images, push `:latest` + `:<sha>` to GHCR.
2. **deploy** — SSH to the server, `git reset --hard <sha>`, `kustomize edit set image`
   to pin the sha (immutable + rollback-able), recreate the `migrate` Job, `kubectl
   apply -k` both sets, wait for the migration, then `rollout status` everything.

Rollback: re-run the deploy for an older commit, or
`kubectl -n yachan rollout undo deploy/backend`.

## Server bring-up (one-time)

Hetzner CX22 (2 vCPU / 4 GB / 40 GB), Ubuntu. All commands run on the server unless noted.

```bash
# 1. swap (headroom against RAM spikes on 4 GB)
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 2. firewall (Cloudflare reaches :80/:443; keep ssh)
sudo ufw allow 22 && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable

# 3. k3s — no Traefik (nginx is the edge), no metrics-server (save RAM),
#    world-readable kubeconfig so the SSH user can run kubectl
curl -sfL https://get.k3s.io | \
  INSTALL_K3S_EXEC="--disable traefik --disable metrics-server --write-kubeconfig-mode 644" sh -
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# 4. standalone kustomize (the deploy uses `kustomize edit set image`)
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/

# 5. repo checkout (the deploy git-resets this)
git clone https://github.com/nazar652/yachan-v2 ~/yachan-v2 && cd ~/yachan-v2
```

# 6. Cloudflare origin cert — the one manual secret (same as the compose ./certs mount).
#    Put origin.pem + origin.key on the server, then create it once; the deploy never
#    touches yachan-tls afterward.
kubectl create namespace yachan --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic yachan-tls -n yachan \
  --from-file=origin.pem=./certs/origin.pem --from-file=origin.key=./certs/origin.key
```

Everything else is automatic: the deploy workflow (re)creates the `yachan` namespace and
the app Secret `yachan-secret` from GitHub Secrets on every run (idempotent
`create --dry-run | apply`), so no other secret is created by hand.

One-time, off the server:
- **GitHub Secrets** the deploy needs (Settings -> Secrets -> Actions): `SSH_HOST`
  `SSH_USER` `SSH_KEY` `SSH_PORT`, plus the config/secrets it writes into `yachan-secret`
  — `DATABASE_URL` (Neon url with `?ssl=require`), `JWT_SECRET`, `IP_HASH_SALT`,
  `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `STORAGE_BASE_URL`,
  `CORS_ORIGINS`, `GEMINI_API_KEY`, `BACKEND_SENTRY_DSN` — and the nginx build arg
  `FRONTEND_SENTRY_DSN`. (All already exist from the compose deploy.)
- **GHCR packages -> public** after the first CI push (GitHub package settings), so k3s
  pulls without an imagePullSecret.
- **Cloudflare DNS**: an `A` record for the domain -> server IP, **proxied** (orange
  cloud); SSL/TLS mode **Full (strict)**. Origin cert: dashboard -> SSL/TLS -> Origin
  Server -> Create Certificate (this is the origin.pem/key used above).

## First deploy

Trigger the `Deploy` workflow (via `workflow_dispatch`, or by merging to `master`). It
builds+pushes the images, creates the namespace + secrets, applies both sets and waits for
the rollout. Then seed a mod on the server:

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl -n yachan get pods
kubectl -n yachan exec -it deploy/backend -- python -m src.cli create-admin <username>
```

After this, every merge to `master` deploys itself.

## Resource notes

Prod is much lighter than in-cluster dev (no postgres/minio pods, no Docker-Desktop
overhead — native k3s on Linux). Budget on 4 GB: ~0.5-0.6 GB k3s system, the rest split
across backend / celery-worker / moderation-worker (each loads onnx) plus redis / nginx /
beat. The 2 GB swap and `--concurrency=1` on both workers keep it inside 4 GB. If it gets
tight, moderation is the first thing to move to its own node.
