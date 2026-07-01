from src.celery_app import celery

# temporary step-2 transport stub: stands in for the moderation microservice on the
# `moderation` queue, echoing a safe verdict straight back on `moderation_results`.
# lets us exercise the three-queue flow without torch. removed in step 3.


@celery.task(name="moderate_image")
def moderate_image(attachment_id: int, image_url: str, mode: str) -> None:
    verdict = {"status": "safe", "nsfw_score": 0.0, "labels": None}
    celery.send_task(
        "apply_moderation_verdict",
        args=[attachment_id, verdict],
        queue="moderation_results",
    )
