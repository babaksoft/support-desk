"""Implement PostgreSQL repositories for generation persistence."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from support_desk.domain import (
    AnswerDraft,
    AttemptOutcome,
    DuplicateSubmissionConflict,
    GenerationAdmission,
    GenerationRequest,
    InvalidGenerationRetry,
)
from support_desk.infrastructure.db.models import (
    DbAttemptEvidence,
    DbGenerationAttempt,
    DbInteraction,
)

INTERACTION_RETENTION_DAYS = 30
_RETRYABLE_OUTCOMES = {
    AttemptOutcome.FAILED,
    AttemptOutcome.TIMED_OUT,
    AttemptOutcome.CANCELLED,
}
_TERMINAL_OUTCOMES = _RETRYABLE_OUTCOMES | {AttemptOutcome.SUCCEEDED}


class DbGenerationRepository:
    """Persist support interactions through independent short transactions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Store the asynchronous session factory.

        Args:
            session_factory:
                Factory creating one session per repository operation.
        """

        self._session_factory = session_factory

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

        try:
            return await self._begin_attempt_once(request)
        except IntegrityError:
            async with self._session_factory() as session:
                existing = await self._get_by_submission(session, request.submission_id)
                if existing is not None:
                    return self._replay(existing, request)

                if request.retry_of_attempt_id is not None:
                    duplicate_retry = await session.scalar(
                        select(DbGenerationAttempt.id).where(
                            DbGenerationAttempt.retry_of_attempt_id
                            == request.retry_of_attempt_id
                        )
                    )
                    if duplicate_retry is not None:
                        raise InvalidGenerationRetry from None
            raise

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

        Raises:
            ValueError:
                The outcome and draft are inconsistent or non-terminal.
            RuntimeError:
                The attempt is absent or already terminal.
        """

        if outcome not in _TERMINAL_OUTCOMES:
            raise ValueError("Attempt outcome must be terminal.")
        if (outcome is AttemptOutcome.SUCCEEDED) != (draft is not None):
            raise ValueError("Only successful attempts contain a draft.")

        async with self._session_factory.begin() as session:
            attempt = await self._get_attempt(session, attempt_id)
            if attempt is None or attempt.outcome != AttemptOutcome.STARTED.value:
                raise RuntimeError("Generation attempt is absent or already terminal.")

            attempt.outcome = outcome.value
            attempt.finished_at = datetime.now(UTC)
            if draft is not None:
                attempt.answer_status = draft.status
                attempt.answer = draft.answer
                attempt.review_status = draft.review_status
                attempt.evidence = [
                    DbAttemptEvidence(
                        source_id=evidence.source_id.value,
                        source_version=evidence.version,
                    )
                    for evidence in draft.evidence
                ]

    async def purge_expired(self, before: datetime) -> int:
        """Delete interactions whose retention deadline has passed.

        Args:
            before:
                Inclusive retention cutoff.

        Returns:
            Number of deleted interactions.

        Raises:
            ValueError:
                The cutoff lacks timezone information.
        """

        if before.tzinfo is None:
            raise ValueError("Retention cutoff must include a timezone.")

        async with self._session_factory.begin() as session:
            result = await session.execute(
                delete(DbInteraction).where(DbInteraction.expires_at <= before)
            )

        return result.rowcount  # type: ignore[attr-defined, no-any-return]

    async def _begin_attempt_once(
        self, request: GenerationRequest
    ) -> GenerationAdmission:
        """Try to create or replay an attempt in one transaction.

        Args:
            request:
                Authenticated idempotent generation request.

        Returns:
            New attempt admission or existing durable outcome.
        """

        async with self._session_factory.begin() as session:
            existing = await self._get_by_submission(session, request.submission_id)
            if existing is not None:
                return self._replay(existing, request)

            now = datetime.now(UTC)
            if request.retry_of_attempt_id is None:
                interaction = DbInteraction(
                    id=uuid4(),
                    operator_subject=request.operator_subject,
                    question=request.question,
                    created_at=now,
                    expires_at=now + timedelta(days=INTERACTION_RETENTION_DAYS),
                )
                session.add(interaction)
            else:
                retried = await self._get_attempt(session, request.retry_of_attempt_id)
                if retried is None or not self._eligible_retry(retried, request):
                    raise InvalidGenerationRetry

                duplicate_retry = await session.scalar(
                    select(DbGenerationAttempt.id).where(
                        DbGenerationAttempt.retry_of_attempt_id
                        == request.retry_of_attempt_id
                    )
                )
                if duplicate_retry is not None:
                    raise InvalidGenerationRetry

                interaction = retried.interaction

            attempt = DbGenerationAttempt(
                id=uuid4(),
                interaction=interaction,
                submission_id=request.submission_id,
                retry_of_attempt_id=request.retry_of_attempt_id,
                model_id=request.model_id,
                outcome=AttemptOutcome.STARTED.value,
                answer_status=None,
                answer=None,
                review_status=None,
                started_at=now,
                finished_at=None,
            )
            session.add(attempt)

        return GenerationAdmission(
            attempt_id=attempt.id,
            outcome=AttemptOutcome.STARTED,
            replayed=False,
        )

    async def _get_by_submission(
        self, session: AsyncSession, submission_id: UUID
    ) -> DbGenerationAttempt | None:
        """Load an attempt and replayable draft by submission identity.

        Args:
            session:
                Current repository transaction.
            submission_id:
                Client idempotency key.

        Returns:
            Matching attempt or None.
        """

        return await session.scalar(
            select(DbGenerationAttempt)
            .where(DbGenerationAttempt.submission_id == submission_id)
            .options(
                selectinload(DbGenerationAttempt.evidence),
                selectinload(DbGenerationAttempt.interaction),
            )
        )

    async def _get_attempt(
        self, session: AsyncSession, attempt_id: UUID
    ) -> DbGenerationAttempt | None:
        """Load an attempt with its interaction and evidence.

        Args:
            session:
                Current repository transaction.
            attempt_id:
                Durable attempt identity.

        Returns:
            Matching attempt or None.
        """

        return await session.scalar(
            select(DbGenerationAttempt)
            .where(DbGenerationAttempt.id == attempt_id)
            .options(
                selectinload(DbGenerationAttempt.evidence),
                selectinload(DbGenerationAttempt.interaction),
            )
        )

    def _replay(
        self, attempt: DbGenerationAttempt, request: GenerationRequest
    ) -> GenerationAdmission:
        """Validate and translate an existing idempotent submission.

        Args:
            attempt:
                Previously persisted attempt.
            request:
                Repeated request using its submission identity.

        Returns:
            Existing durable attempt outcome.

        Raises:
            DuplicateSubmissionConflict:
                Stable request fields differ.
        """

        if (
            attempt.interaction.operator_subject != request.operator_subject
            or attempt.interaction.question != request.question
            or attempt.retry_of_attempt_id != request.retry_of_attempt_id
        ):
            raise DuplicateSubmissionConflict

        outcome = AttemptOutcome(attempt.outcome)
        draft = self._to_draft(attempt) if outcome is AttemptOutcome.SUCCEEDED else None
        return GenerationAdmission(
            attempt_id=attempt.id,
            outcome=outcome,
            draft=draft,
            replayed=True,
        )

    def _eligible_retry(
        self, attempt: DbGenerationAttempt, request: GenerationRequest
    ) -> bool:
        """Check retry ownership, input, and terminal outcome.

        Args:
            attempt:
                Attempt named as the retry target.
            request:
                Proposed retry request.

        Returns:
            Whether the retry may create a new attempt.
        """

        return (
            attempt.interaction.operator_subject == request.operator_subject
            and attempt.interaction.question == request.question
            and AttemptOutcome(attempt.outcome) in _RETRYABLE_OUTCOMES
        )

    def _to_draft(self, attempt: DbGenerationAttempt) -> AnswerDraft:
        """Reconstruct a successful draft from normalized records.

        Args:
            attempt:
                Successful persisted attempt.

        Returns:
            Validated domain draft.

        Raises:
            RuntimeError:
                Required successful values are absent.
        """

        if (
            attempt.answer_status is None
            or attempt.answer is None
            or attempt.review_status is None
        ):
            raise RuntimeError("Successful generation attempt is incomplete.")

        return AnswerDraft.model_validate(
            {
                "status": attempt.answer_status,
                "answer": attempt.answer,
                "review_status": attempt.review_status,
                "evidence": [
                    {"source_id": item.source_id, "version": item.source_version}
                    for item in attempt.evidence
                ],
            }
        )
