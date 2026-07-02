from functools import lru_cache

from app.celery_app import celery
from app.classifier import OnnxClassifier
from app.config import settings
from app.fetch import fetch_bytes


@lru_cache(maxsize=1)
def get_classifier() -> OnnxClassifier:
    # built once per process; loading the onnx session is expensive
    return OnnxClassifier.from_path(settings.onnx_model_path)


@celery.task(name="moderate_image")
def moderate_image(attachment_id: int, image_url: str, mode: str) -> None:
    try:
        data = fetch_bytes(image_url)
        verdict = get_classifier().classify(data, mode)
    except Exception:
        # fail safe: flag for human review rather than dropping the attachment
        verdict = {"status": "flagged", "nsfw_score": None, "labels": None}
    celery.send_task(
        "apply_moderation_verdict",
        args=[attachment_id, verdict],
        queue="moderation_results",
    )
