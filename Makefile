.PHONY: openapi lint-backend lint-frontend lint-moderation lint-all

# dump the backend openapi schema (pretty json) and regenerate frontend types
openapi:
	cd backend && poetry run python -m src.cli dump-openapi -o ../openapi.json
	cd frontend && npm run gen:api

lint-backend:
	cd backend && ruff check src/
	cd backend && pyright
	cd backend && pytest tests/

lint-frontend:
	cd frontend && npm run lint
	cd frontend && npm run test:unit -- --run
	cd frontend && npm run type-check

lint-moderation:
	cd moderation && poetry run ruff check .
	cd moderation && poetry run pyright
	cd moderation && poetry run pytest tests/

lint-all: lint-backend lint-frontend lint-moderation
