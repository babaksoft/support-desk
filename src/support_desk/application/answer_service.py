"""Bound and durably record question generation."""

import asyncio
import math
from uuid import UUID

from support_desk.application.errors import (
    GenerationBusy,
    GenerationFailed,
    GenerationPersistenceFailed,
    GenerationRetryRejected,
    GenerationSubmissionConflict,
    GenerationTimedOut,
)
from support_desk.domain import (
    AnswerDraft,
    AnswerGenerator,
    AttemptOutcome,
    DuplicateSubmissionConflict,
    GenerationRepository,
    GenerationRequest,
    InvalidGenerationRetry,
)

MAX_QUESTION_LENGTH = 2048


class AnswerService:
    """Generate one answer at a time and durably record its outcome."""

    def __init__(
        self,
        generator: AnswerGenerator,
        repository: GenerationRepository,
        model_id: str,
        timeout_seconds: float = 45,
    ) -> None:
        """Set generation, persistence, provenance, and deadline dependencies.

        Args:
            generator:
                Evidence-based generation capability.
            repository:
                Durable interaction and attempt repository.
            model_id:
                Configured generation model identifier.
            timeout_seconds:
                Maximum elapsed generation time.

        Raises:
            ValueError:
                The model identity or generation deadline is invalid.
        """

        if not model_id.strip() or len(model_id) > 256:
            raise ValueError("Model ID must contain at most 256 characters.")
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Generation timeout must be positive and finite.")

        self._generator = generator
        self._repository = repository
        self._model_id = model_id
        self._timeout_seconds = timeout_seconds
        self._busy = False

    async def execute(
        self,
        question: str,
        operator_subject: str,
        submission_id: UUID,
        retry_of_attempt_id: UUID | None = None,
    ) -> AnswerDraft:
        """Admit, execute, and record a bounded generation request.

        Args:
            question:
                Product question that needs validation.
            operator_subject:
                Authenticated operator identity.
            submission_id:
                Client-generated idempotency key.
            retry_of_attempt_id:
                Failed attempt explicitly retried by this request.

        Returns:
            New or idempotently replayed unreviewed answer draft.

        Raises:
            GenerationBusy:
                Another request occupies the generation slot or the attempt is active.
            GenerationTimedOut:
                Generation exceeds the deadline.
            GenerationFailed:
                Generation fails or produces invalid output.
            GenerationSubmissionConflict:
                The submission identity was reused with different input.
            GenerationRetryRejected:
                The retry target is not eligible.
        """

        if self._busy:
            raise GenerationBusy
        if len(question) > MAX_QUESTION_LENGTH:
            raise ValueError(
                f"Question cannot be longer than {MAX_QUESTION_LENGTH} characters."
            )

        request = GenerationRequest(
            submission_id=submission_id,
            operator_subject=operator_subject,
            question=question,
            model_id=self._model_id,
            retry_of_attempt_id=retry_of_attempt_id,
        )
        try:
            admission = await self._repository.begin_attempt(request)
        except DuplicateSubmissionConflict as exc:
            raise GenerationSubmissionConflict from exc
        except InvalidGenerationRetry as exc:
            raise GenerationRetryRejected from exc
        except Exception as exc:
            raise GenerationPersistenceFailed from exc

        if admission.replayed:
            if admission.outcome is AttemptOutcome.SUCCEEDED:
                if admission.draft is None:
                    raise RuntimeError("Successful replay lost its draft.")
                return admission.draft
            if admission.outcome is AttemptOutcome.STARTED:
                raise GenerationBusy
            if admission.outcome is AttemptOutcome.TIMED_OUT:
                raise GenerationTimedOut
            raise GenerationFailed

        self._busy = True
        try:
            async with asyncio.timeout(self._timeout_seconds):
                draft = await self._generator.generate(question)
        except TimeoutError as exc:
            await self._finish_attempt(admission.attempt_id, AttemptOutcome.TIMED_OUT)
            raise GenerationTimedOut from exc
        except asyncio.CancelledError:
            await self._finish_attempt(admission.attempt_id, AttemptOutcome.CANCELLED)
            raise
        except Exception as exc:
            await self._finish_attempt(admission.attempt_id, AttemptOutcome.FAILED)
            raise GenerationFailed from exc
        else:
            await self._finish_attempt(
                admission.attempt_id, AttemptOutcome.SUCCEEDED, draft
            )
            return draft
        finally:
            self._busy = False

    async def _finish_attempt(
        self,
        attempt_id: UUID,
        outcome: AttemptOutcome,
        draft: AnswerDraft | None = None,
    ) -> None:
        """Finalize an attempt and hide persistence implementation failures.

        Args:
            attempt_id:
                Durable attempt to finalize.
            outcome:
                Safe terminal attempt outcome.
            draft:
                Successful draft, when present.

        Raises:
            GenerationPersistenceFailed:
                The durable outcome cannot be stored.
        """

        try:
            await self._repository.finish_attempt(attempt_id, outcome, draft)
        except Exception as exc:
            raise GenerationPersistenceFailed from exc
