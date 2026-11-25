"""Verify PostgreSQL generation repository behavior."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from support_desk.domain import (
    AnswerDraft,
    AttemptOutcome,
    Evidence,
    GenerationRequest,
    InvalidGenerationRetry,
    SourceId,
)
from support_desk.infrastructure.db import (
    DbGenerationRepository,
    create_database_engine,
    create_session_factory,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_persists_and_replays_success_with_provenance(
    migrated_database: str,
) -> None:
    """Round-trip a normalized successful draft without a model call.

    Args:
        migrated_database:
            Migrated disposable PostgreSQL URL.
    """

    engine = create_database_engine(migrated_database)
    repository = DbGenerationRepository(create_session_factory(engine))
    request = _request()
    draft = AnswerDraft(
        status="answered",
        answer="Free supports three boards.",
        evidence=(Evidence(source_id=SourceId.PLANS, version="1"),),
        review_status="unreviewed",
    )
    try:
        admission = await repository.begin_attempt(request)
        assert admission.replayed is False
        await repository.finish_attempt(
            admission.attempt_id, AttemptOutcome.SUCCEEDED, draft
        )

        replay = await repository.begin_attempt(request)
        assert replay.replayed is True
        assert replay.draft == draft
        assert replay.attempt_id == admission.attempt_id
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_links_retry_and_purges_expired_interaction(
    migrated_database: str,
) -> None:
    """Require a failed target, link its retry, and enforce retention deletion.

    Args:
        migrated_database:
            Migrated disposable PostgreSQL URL.
    """

    engine = create_database_engine(migrated_database)
    repository = DbGenerationRepository(create_session_factory(engine))
    request = _request()
    try:
        failed = await repository.begin_attempt(request)
        await repository.finish_attempt(failed.attempt_id, AttemptOutcome.FAILED)

        retry = _request(retry_of_attempt_id=failed.attempt_id)
        admitted_retry = await repository.begin_attempt(retry)
        assert admitted_retry.replayed is False

        with pytest.raises(InvalidGenerationRetry):
            await repository.begin_attempt(_request(retry_of_attempt_id=uuid4()))

        deleted = await repository.purge_expired(datetime.now(UTC) + timedelta(days=31))
        assert deleted == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_duplicate_creates_one_attempt(
    migrated_database: str,
) -> None:
    """Resolve an idempotency race to one new and one replayed admission.

    Args:
        migrated_database:
            Migrated disposable PostgreSQL URL.
    """

    engine = create_database_engine(migrated_database)
    repository = DbGenerationRepository(create_session_factory(engine))
    request = _request()
    try:
        admissions = await asyncio.gather(
            repository.begin_attempt(request),
            repository.begin_attempt(request),
        )
        assert {admission.replayed for admission in admissions} == {False, True}
        assert admissions[0].attempt_id == admissions[1].attempt_id
    finally:
        await engine.dispose()


def _request(retry_of_attempt_id: UUID | None = None) -> GenerationRequest:
    """Build a valid repository request.

    Args:
        retry_of_attempt_id:
            Optional attempt identity for a retry.

    Returns:
        Valid generation request.
    """

    return GenerationRequest(
        submission_id=uuid4(),
        operator_subject="synthetic-operator",
        question="How many boards?",
        model_id="synthetic-model",
        retry_of_attempt_id=retry_of_attempt_id,
    )
