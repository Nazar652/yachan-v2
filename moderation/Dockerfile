FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction --no-ansi

RUN python -c "import urllib.request, pathlib; pathlib.Path('models').mkdir(exist_ok=True); urllib.request.urlretrieve('https://huggingface.co/OwenElliott/image-safety-classifier-xs/resolve/main/onnx/image-safety-classifier-xs.onnx', 'models/image-safety-classifier-xs.onnx')"
# multilingual distilbert toxicity classifier + its tokenizer (for text moderation)
RUN python -c "import urllib.request; base='https://huggingface.co/gravitee-io/distilbert-multilingual-toxicity-classifier/resolve/main'; urllib.request.urlretrieve(f'{base}/model.quant.onnx', 'models/toxicity.onnx'); urllib.request.urlretrieve(f'{base}/tokenizer.json', 'models/toxicity-tokenizer.json')"

COPY . .

CMD ["celery", "-A", "app.celery_app.celery", "worker", "-Q", "moderation", "--loglevel=info"]
