from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check API liveness")
async def health_check() -> dict[str, str]:
    """Report that the API process is running; dependency checks come later."""
    return {"status": "ok"}
