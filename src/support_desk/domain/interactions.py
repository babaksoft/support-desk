"""Define durable support-interaction and generation-attempt values."""

from datetime import datetime
from enum import StrEnum
from typing import Protocol, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from support_desk.domain.answers import AnswerDraft


class AttemptOutcome(StrEnum):
    """Identify the durable outcome of one generation attempt."""

    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class GenerationRequest(BaseModel):
    """Describe one idempotent request for generated guidance.

    Attributes:
        submission_id:
            Client-generated idempotency key for this attempt.
        operator_subject:
            Authenticated operator identity that owns the request.
        question:
            Operator-authored product question.
        model_id:
            Configured generation model identifier.
        retry_of_attempt_id:
            Failed attempt explicitly retried by this request.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    submission_id: UUID = Field(description="Idempotency key for this attempt.")
    operator_subject: str = Field(
        min_length=1,
        max_length=256,
        description="Authenticated operator identity that owns the request.",
    )
    question: str = Field(
        min_length=1,
        max_length=2048,
        description="Product question submitted for generation.",
    )
    model_id: str = Field(
        min_length=1,
        max_length=256,
        description="Configured generation model identifier.",
    )
    retry_of_attempt_id: UUID | None = Field(
        default=None,
        description="Failed attempt explicitly retried by this request.",
    )


class GenerationAdmission(BaseModel):
    """Report a new attempt or the outcome of an idempotent replay.

    Attributes:
        attempt_id:
            Durable generation-attempt identity.
        outcome:
            Current durable attempt outcome.
        draft:
            Stored successful draft for an idempotent replay.
        replayed:
            Whether the submission already existed.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    attempt_id: UUID = Field(description="Durable generation-attempt identity.")
    outcome: AttemptOutcome = Field(description="Current durable attempt outcome.")
    draft: AnswerDraft | None = Field(
        default=None,
        description="Stored successful draft for an idempotent replay.",
    )
    replayed: bool = Field(description="Whether the submission already existed.")

    @model_validator(mode="after")
    def validate_draft(self) -> Self:
        """Keep stored drafts consistent with successful outcomes.

        Returns:
            Validated admission result.

        Raises:
            ValueError:
                Draft presence does not match the attempt outcome.
        """

        if (self.outcome is AttemptOutcome.SUCCEEDED) != (self.draft is not None):
            raise ValueError("Only successful attempts contain a draft.")
        return self


class DuplicateSubmissionConflict(Exception):
    """Report reuse of an idempotency key for a different request."""


class InvalidGenerationRetry(Exception):
    """Report a retry that does not name an eligible failed attempt."""


class GenerationRepository(Protocol):
    """Persist support interactions and generation-attempt outcomes."""

    async def begin_attempt(self, request: GenerationRequest) -> GenerationAdmission:
        """Create an attempt or return its previously stored outcome.

        Args:
            request:
                Authenticated idempotent generation request.

        Returns:
            New attempt admission or existing durable outcome.

        Raises:
            DuplicateSubmissionConflict:
                The submission identity was reused with different input.
            InvalidGenerationRetry:
                The requested retry target is absent or ineligible.
        """

        ...

    async def finish_attempt(
        self,
        attempt_id: UUID,
        outcome: AttemptOutcome,
        draft: AnswerDraft | None = None,
    ) -> None:
        """Store one terminal attempt outcome.

        Args:
            attempt_id:
                Durable attempt to finish.
            outcome:
                Terminal success or safe failure category.
            draft:
                Successful generated draft, when available.
        """

        ...

    async def purge_expired(self, before: datetime) -> int:
        """Delete interactions whose retention deadline has passed.

        Args:
            before:
                Inclusive retention cutoff.

        Returns:
            Number of deleted interactions.
        """

        ...
