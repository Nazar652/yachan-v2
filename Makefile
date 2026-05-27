.PHONY: lint

lint:
	cd backend && ruff check --force-exclude src/
	cd backend && pyright src/
	cd backend && pytest tests/
	cd frontend && npm run lint

