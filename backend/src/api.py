from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {"message": "yachan-v2 backend is running"}


@router.get("/health", tags=["meta"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

