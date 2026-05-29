# yachan-v2 backend

FastAPI application powering the yachan imageboard. All endpoints are served
under the `/api` prefix:

- `/api/boards` – board listing and details
- `/api/{board_slug}/threads` – thread management
- `/api/{board_slug}` – posts, reports, and WebSocket connections
- `/api/captcha` – CAPTCHA generation/validation
- `/api/mod` – moderator authentication and actions

## Quick start

```bash
poetry install
poetry run uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API docs.

## Run tests

```bash
poetry run pytest
```

