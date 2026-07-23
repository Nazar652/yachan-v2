import httpx

from app.config import settings


def fetch_bytes(url: str) -> bytes:
    # media urls are backend-generated and internal; do not follow redirects, which a
    # hostile host could use to steer the fetch at an unintended (e.g. internal) target
    response = httpx.get(url, timeout=settings.fetch_timeout_seconds, follow_redirects=False)
    response.raise_for_status()
    return response.content
