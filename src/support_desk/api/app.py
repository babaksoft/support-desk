"""Construct the FastAPI application from configured dependencies."""

from collections.abc import Iterable

from fastapi import FastAPI

from support_desk.api.errors import ApiError, api_error_handler
from support_desk.api.lifespan import ApiLifespan, ManagedResource
from support_desk.api.middleware import BodyLimitMiddleware
from support_desk.api.routes import health_router, question_router
from support_desk.application import AnswerService


def create_app(
    service: AnswerService | None = None,
    managed_resources: Iterable[ManagedResource] = (),
) -> FastAPI:
    """Construct HTTP routes around a configured application service.

    Args:
        service:
            Configured answer generation service, if available.
        managed_resources:
            Asynchronous resources owned by the API process.

    Returns:
        FastAPI application with health and question routes.
    """

    app = FastAPI(
        title="Support Desk",
        version="0.1.0",
        lifespan=ApiLifespan(managed_resources),
    )
    app.state.generation_service = service

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_middleware(BodyLimitMiddleware)

    app.include_router(health_router)
    app.include_router(question_router)

    return app
