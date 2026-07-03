import httpx

from app.config import settings


def fetch_bytes(url: str) -> bytes:
    response = httpx.get(url, timeout=settings.fetch_timeout_seconds, follow_redirects=True)
    response.raise_for_status()
    return response.content
