"""Resolve configured application services for HTTP handlers."""

from typing import cast

from fastapi import Request

from support_desk.api.errors import ApiError
from support_desk.application import AnswerService


def require_generation(request: Request) -> AnswerService:
    """Resolve the configured answer generation service from the application.

    Args:
        request:
            Current HTTP request.

    Returns:
        Configured answer generation service.

    Raises:
        ApiError:
            Generation is unavailable in this process.
    """

    service = cast(AnswerService | None, request.app.state.generation_service)
    if service is None:
        raise ApiError(
            status_code=503,
            code="generation_unavailable",
            message="Generation is not configured.",
        )

    return service
