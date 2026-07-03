FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root --no-interaction --no-ansi

RUN python -c "import urllib.request, pathlib; pathlib.Path('models').mkdir(exist_ok=True); base='https://huggingface.co/Xenova/paraphrase-multilingual-MiniLM-L12-v2/resolve/main'; urllib.request.urlretrieve(f'{base}/onnx/model_quantized.onnx', 'models/embedding.onnx'); urllib.request.urlretrieve(f'{base}/tokenizer.json', 'models/tokenizer.json')"

# Copy the application code.
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
