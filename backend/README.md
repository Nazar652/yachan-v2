# yachan-v2 backend

Simple FastAPI template with two starter endpoints:

- `GET /` returns a basic service message
- `GET /health` returns health status

## Quick start

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API docs.

## Run tests

```bash
poetry run pytest
```

