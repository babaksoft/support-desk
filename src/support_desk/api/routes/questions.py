"""Expose product-question generation endpoints."""

from fastapi import APIRouter, Request

from support_desk.api.dependencies import require_generation
from support_desk.api.errors import ApiError
from support_desk.api.schemas import AnswerRequest, ErrorResponse
from support_desk.application import (
    GenerationBusy,
    GenerationFailed,
    GenerationTimedOut,
)
from support_desk.domain import AnswerDraft

router = APIRouter(tags=["questions"])


@router.post(
    "/questions",
    response_model=AnswerDraft,
    responses={
        413: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
    name="answer",
)
async def answer(question: AnswerRequest, request: Request) -> AnswerDraft:
    """Draft a product answer for operator review.

    Args:
        question:
            Validated operator question.
        request:
            Current HTTP request.

    Returns:
        Unreviewed answer and source references.

    Raises:
        ApiError:
            Generation is busy, timed out, or failed.
    """

    service = require_generation(request)
    try:
        return await service.execute(question.question)
    except GenerationBusy as exc:
        raise ApiError(
            status_code=429,
            code="generation_busy",
            message="Generation is busy; please try again later.",
            headers={"Retry-After": "5"},
        ) from exc
    except GenerationTimedOut as exc:
        raise ApiError(
            status_code=504,
            code="generation_timed_out",
            message="Generation timed out; please retry explicitly.",
        ) from exc
    except GenerationFailed as exc:
        raise ApiError(
            status_code=502,
            code="generation_failed",
            message="Generation failed; please retry explicitly.",
        ) from exc
