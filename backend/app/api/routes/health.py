from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthcheck() -> dict:
    return {"status": "ok"}
