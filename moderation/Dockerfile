FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction --no-ansi

# bake the small onnx model into the image (kept out of the build context by .dockerignore)
RUN python -c "import urllib.request, pathlib; pathlib.Path('models').mkdir(exist_ok=True); urllib.request.urlretrieve('https://huggingface.co/OwenElliott/image-safety-classifier-xs/resolve/main/onnx/image-safety-classifier-xs.onnx', 'models/image-safety-classifier-xs.onnx')"

COPY . .

CMD ["celery", "-A", "app.celery_app.celery", "worker", "-Q", "moderation", "--loglevel=info"]
