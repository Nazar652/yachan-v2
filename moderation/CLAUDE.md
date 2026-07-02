# yachan-v2 — moderation service

Stateless AI moderation microservice. A **separate member** of the yachan-v2
monorepo: its own deps, image and venv, no shared code with `backend/`, no
database. It shares only the Redis broker with yachan. See the repo-root
`CLAUDE.md` for the monorepo layout and `docs/moderation-contract.md` for the
message contract (the only coupling to yachan).

## What it does

Consumes `moderate_image` off the `moderation` queue, fetches the media by URL as
an external http client, classifies it, and replies with `apply_moderation_verdict`
on the `moderation_results` queue. Tasks are addressed by **string name** — the
service never imports yachan code, and holds no db/storage credentials.

Failure is fail-safe: a fetch or classifier error replies `flagged` (human review)
rather than dropping the attachment.

## Layout

```
moderation/
  app/
    celery_app.py   Celery("moderation") — broker only, no result backend
    config.py       env settings (REDIS_URL, fetch timeout)
    tasks.py        moderate_image (by name); module-level classifier instance
    classifier.py   Classifier Protocol + status_from_labels() + StubClassifier
    fetch.py        httpx media fetch
  tests/            mirrors app/, pure unit tests (mock fetch/classifier)
  Dockerfile        python:3.12-slim, poetry install, celery worker -Q moderation
  pyproject.toml    own deps; in-project venv (poetry.toml)
```

## Classifier

`classify(data, mode) -> Verdict` behind a `Protocol`. `status_from_labels()` is the
pure tier mapping (`porn`/`hentai` → blocked, `sexy` → flagged, else safe). The real
multi-class NSFW model replaces `StubClassifier` in step 3b — it plugs into the same
Protocol and the module-level `classifier` in `tasks.py`, loaded once per process.

## Commands

```bash
poetry install                                              # into ./.venv (in-project)
poetry run celery -A app.celery_app.celery worker -Q moderation --loglevel=info
```

Lint from the repo root: `make lint-moderation` (ruff + pyright + pytest). End every
change lint-green, same as the rest of the repo.
