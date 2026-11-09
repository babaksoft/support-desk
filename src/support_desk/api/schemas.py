"""Define HTTP-specific request and response schemas."""

from typing import Literal

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
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    question: str = Field(
        min_length=1,
        max_length=2048,
        description="Product question to draft an answer for.",
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
