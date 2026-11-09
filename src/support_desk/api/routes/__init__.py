"""Expose the HTTP route groups."""

from support_desk.api.routes.health import router as health_router
from support_desk.api.routes.questions import router as question_router

__all__ = ["health_router", "question_router"]
