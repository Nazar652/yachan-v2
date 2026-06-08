import sentry_sdk

from src.core.config import Settings


def init_sentry(settings: Settings) -> None:
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=settings.app_version,
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )
