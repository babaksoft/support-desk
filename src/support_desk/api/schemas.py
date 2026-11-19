"""Define HTTP-specific request and response schemas."""

from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Report process health.

    Attributes:
        status:
            Current health state.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: Literal["alive", "ready"] = Field(
        description="Current process health state."
    )


class AnswerRequest(BaseModel):
    """Request a product answer.

    Attributes:
        question:
            Operator-authored product question.
        submission_id:
            Client-generated idempotency key for this attempt.
        retry_of_attempt_id:
            Failed attempt explicitly retried by this request.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    question: str = Field(
        min_length=1,
        max_length=2048,
        description="Product question to draft an answer for.",
    )
    submission_id: UUID = Field(
        default_factory=uuid4,
        description="Client-generated idempotency key for this attempt.",
    )
    retry_of_attempt_id: UUID | None = Field(
        default=None,
        description="Failed attempt explicitly retried by this request.",
    )


class ErrorResponse(BaseModel):
    """Report a safe API failure.

    Attributes:
        code:
            Stable machine-readable failure code.
        message:
            Safe operator-facing failure explanation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(min_length=1, max_length=64, description="Stable failure code.")
    message: str = Field(
        min_length=1,
        max_length=256,
        description="Safe operator-facing failure explanation.",
    )
