"""Provide deterministic persistence fakes for application tests."""

from datetime import datetime
from uuid import UUID, uuid4

from support_desk.application import AnswerService
from support_desk.domain import (
    AnswerDraft,
    AnswerGenerator,
    AttemptOutcome,
    DuplicateSubmissionConflict,
    GenerationAdmission,
    GenerationRequest,
    InvalidGenerationRetry,
)


class FakeGenerationRepository:
    """Record generation requests and outcomes in process for deterministic tests."""

    def __init__(self) -> None:
        """Initialize empty request and outcome records."""

        self.requests: dict[UUID, GenerationRequest] = {}
        self.attempt_ids: dict[UUID, UUID] = {}
        self.outcomes: dict[UUID, tuple[AttemptOutcome, AnswerDraft | None]] = {}

    async def begin_attempt(self, request: GenerationRequest) -> GenerationAdmission:
        """Create an attempt or replay a matching prior request.

        Args:
            request:
                Authenticated idempotent generation request.

        Returns:
            New admission or stored attempt outcome.

        Raises:
            DuplicateSubmissionConflict:
                The submission identity was reused with different input.
            InvalidGenerationRetry:
                The retry target is not an eligible failed attempt.
        """

        existing = self.requests.get(request.submission_id)
        if existing is not None:
            if existing != request:
                raise DuplicateSubmissionConflict
            attempt_id = self.attempt_ids[request.submission_id]
            outcome, draft = self.outcomes[attempt_id]
            return GenerationAdmission(
                attempt_id=attempt_id,
                outcome=outcome,
                draft=draft,
                replayed=True,
            )

        if request.retry_of_attempt_id is not None:
            prior = self.outcomes.get(request.retry_of_attempt_id)
            if prior is None or prior[0] not in {
                AttemptOutcome.FAILED,
                AttemptOutcome.TIMED_OUT,
                AttemptOutcome.CANCELLED,
            }:
                raise InvalidGenerationRetry

        attempt_id = uuid4()
        self.requests[request.submission_id] = request
        self.attempt_ids[request.submission_id] = attempt_id
        self.outcomes[attempt_id] = (AttemptOutcome.STARTED, None)
        return GenerationAdmission(
            attempt_id=attempt_id,
            outcome=AttemptOutcome.STARTED,
            replayed=False,
        )

    async def finish_attempt(
        self,
        attempt_id: UUID,
        outcome: AttemptOutcome,
        draft: AnswerDraft | None = None,
    ) -> None:
        """Store a terminal outcome.

        Args:
            attempt_id:
                Attempt to finish.
            outcome:
                Terminal attempt outcome.
            draft:
                Successful draft, when present.
        """

        self.outcomes[attempt_id] = (outcome, draft)

    async def purge_expired(self, before: datetime) -> int:
        """Return zero because the fake has no retention timestamps.

        Args:
            before:
                Unused retention cutoff.

        Returns:
            Zero deleted interactions.
        """

        del before
        return 0


def build_answer_service(
    generator: AnswerGenerator,
    timeout_seconds: float = 45,
    repository: FakeGenerationRepository | None = None,
) -> AnswerService:
    """Build a deterministic answer service with fake persistence.

    Args:
        generator:
            Deterministic answer generator.
        timeout_seconds:
            Application generation deadline.
        repository:
            Optional observable persistence fake.

    Returns:
        Answer service configured with test provenance.
    """

    return AnswerService(
        generator,
        repository or FakeGenerationRepository(),
        "test-model",
        timeout_seconds,
    )
