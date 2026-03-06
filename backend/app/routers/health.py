from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "app-l5x-backend",
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "offline-only",
    }
