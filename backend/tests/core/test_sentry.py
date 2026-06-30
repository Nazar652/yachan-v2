from unittest.mock import patch

from src.core.config import Settings
from src.core.sentry import _drop_websocket_keepalive_noise, init_sentry


@patch("src.core.sentry.sentry_sdk")
def test_init_sentry_skips_when_dsn_empty(sentry_sdk):
    init_sentry(Settings(sentry_dsn=""))
    sentry_sdk.init.assert_not_called()


@patch("src.core.sentry.sentry_sdk")
def test_init_sentry_initialises_when_dsn_set(sentry_sdk):
    settings = Settings(
        sentry_dsn="https://public@sentry.example/1",
        sentry_environment="production",
        sentry_traces_sample_rate=0.5,
    )
    init_sentry(settings)

    sentry_sdk.init.assert_called_once()
    kwargs = sentry_sdk.init.call_args.kwargs
    assert kwargs["dsn"] == "https://public@sentry.example/1"
    assert kwargs["environment"] == "production"
    assert kwargs["traces_sample_rate"] == 0.5
    assert kwargs["before_send"] is _drop_websocket_keepalive_noise


def test_drop_websocket_keepalive_noise_drops_asyncio_ping_timeout():
    event = {
        "logger": "asyncio",
        "exception": {
            "values": [
                {"value": "sent 1011 (internal error) keepalive ping timeout"}
            ]
        },
    }
    assert _drop_websocket_keepalive_noise(event, {}) is None


def test_drop_websocket_keepalive_noise_drops_when_only_in_logentry():
    event = {
        "logger": "asyncio",
        "logentry": {"message": "ConnectionClosedError: keepalive ping timeout"},
    }
    assert _drop_websocket_keepalive_noise(event, {}) is None


def test_drop_websocket_keepalive_noise_keeps_other_asyncio_events():
    event = {"logger": "asyncio", "logentry": {"message": "some other failure"}}
    assert _drop_websocket_keepalive_noise(event, {}) is event


def test_drop_websocket_keepalive_noise_keeps_non_asyncio_events():
    event = {
        "logger": "uvicorn.error",
        "exception": {"values": [{"value": "keepalive ping timeout"}]},
    }
    assert _drop_websocket_keepalive_noise(event, {}) is event
