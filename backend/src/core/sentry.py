import sentry_sdk
from sentry_sdk.types import Event, Hint

from src.core.config import Settings


def _is_websocket_keepalive_noise(event: Event) -> bool:
    # a dropped ws client makes the websockets library close with code 1011
    # "keepalive ping timeout"; asyncio logs that shielded-future exception as an
    # error, which the logging integration turns into a benign sentry event.
    if event.get("logger") != "asyncio":
        return False
    logentry = event.get("logentry") or {}
    candidates = [logentry.get("message"), logentry.get("formatted")]
    for value in (event.get("exception") or {}).get("values", []):
        candidates.append(value.get("value"))
    return any(
        isinstance(text, str) and "keepalive ping timeout" in text
        for text in candidates
    )


def _drop_websocket_keepalive_noise(event: Event, hint: Hint) -> Event | None:
    return None if _is_websocket_keepalive_noise(event) else event


def init_sentry(settings: Settings) -> None:
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=settings.app_version,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        before_send=_drop_websocket_keepalive_noise,
    )
