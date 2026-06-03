.PHONY: openapi lint-backend lint-frontend lint-all

# dump the backend openapi schema (pretty json) and regenerate frontend types
openapi:
	cd backend && poetry run python -m src.cli dump-openapi -o ../openapi.json
	cd frontend && npm run gen:api

lint-backend:
	cd backend && ruff check --force-exclude src/
	cd backend && pyright
	cd backend && pytest tests/

lint-frontend:
	cd frontend && npm run lint
	cd frontend && npm run test:unit -- --run

lint-all: lint-backend lint-frontend
