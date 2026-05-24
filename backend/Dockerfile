FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Install Poetry for dependency management.
RUN pip install --no-cache-dir poetry

# Copy dependency files first to maximize layer caching.
COPY pyproject.toml poetry.lock ./

# Install only runtime dependencies.
RUN poetry install --only main --no-root --no-interaction --no-ansi

# Copy the application code.
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
