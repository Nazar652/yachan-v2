from app.celery_app import celery
from app.classifier import StubClassifier
from app.fetch import fetch_bytes

# built once per process; the real model (step 3b) is expensive to load, so it lives
# at module level and is reused across every task invocation
classifier = StubClassifier()


@celery.task(name="moderate_image")
def moderate_image(attachment_id: int, image_url: str, mode: str) -> None:
    try:
        data = fetch_bytes(image_url)
        verdict = classifier.classify(data, mode)
    except Exception:
        # fail safe: flag for human review rather than dropping the attachment
        verdict = {"status": "flagged", "nsfw_score": None, "labels": None}
    celery.send_task(
        "apply_moderation_verdict",
        args=[attachment_id, verdict],
        queue="moderation_results",
    )
