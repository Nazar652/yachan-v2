from functools import lru_cache

from app.celery_app import celery
from app.classifier import OnnxClassifier
from app.config import settings
from app.fetch import fetch_bytes
from app.text_classifier import OnnxTextClassifier


@lru_cache(maxsize=1)
def get_classifier() -> OnnxClassifier:
    return OnnxClassifier.from_path(settings.onnx_model_path)


@lru_cache(maxsize=1)
def get_text_classifier() -> OnnxTextClassifier:
    return OnnxTextClassifier.from_paths(
        settings.toxicity_model_path,
        settings.toxicity_tokenizer_path,
        settings.toxicity_threshold,
    )


@celery.task(name="moderate_image")
def moderate_image(attachment_id: int, image_url: str, mode: str) -> None:
    try:
        data = fetch_bytes(image_url)
        verdict = get_classifier().classify(data, mode)
    except Exception:
        verdict = {"status": "flagged", "nsfw_score": None, "labels": None}

    celery.send_task(
        "apply_moderation_verdict",
        args=[attachment_id, verdict],
        queue="moderation_results",
    )


@celery.task(name="moderate_text")
def moderate_text(post_id: int, text: str) -> None:
    # fail-safe here is the opposite of images: an error must NOT flag, so a broken
    # classifier can't flood the report queue with false auto-reports
    try:
        verdict = get_text_classifier().classify(text)
    except Exception:
        verdict = {"toxic": False, "spam": False, "scores": None}

    celery.send_task(
        "apply_text_verdict",
        args=[post_id, verdict],
        queue="moderation_results",
    )
