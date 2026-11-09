"""Expose process health endpoints."""

from fastapi import APIRouter, Request

from support_desk.api.dependencies import require_generation
from support_desk.api.schemas import ErrorResponse, HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse, name="live")
async def live() -> HealthResponse:
    """Report that the HTTP process is alive.

    Returns:
        Process liveness status.
    """

    return HealthResponse(status="alive")


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={503: {"model": ErrorResponse}},
    name="ready",
)
async def ready(request: Request) -> HealthResponse:
    """Report that generation dependencies are configured.

    Args:
        request:
            Current HTTP request.

    Returns:
        Process readiness status.
    """

    require_generation(request)
    return HealthResponse(status="ready")
