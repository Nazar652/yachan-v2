.PHONY: lint openapi

lint:
	cd backend && ruff check --force-exclude src/
	cd backend && pyright
	cd backend && pytest tests/
	cd frontend && npm run lint

# dump the backend openapi schema (pretty json) and regenerate frontend types
openapi:
	cd backend && poetry run python -m src.cli dump-openapi -o ../openapi.json
	cd frontend && npm run gen:api
