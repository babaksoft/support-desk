"""Verify application question-answer policy."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from support_desk.application import AnswerService, GenerationFailed
from support_desk.domain import AnswerDraft, AttemptOutcome
from tests.fakes import FakeGenerationRepository, build_answer_service


@pytest.mark.parametrize("timeout_seconds", [0, -1, float("inf"), float("nan")])
def test_rejects_invalid_generation_timeout(timeout_seconds: float) -> None:
    """Reject non-positive and non-finite generation deadlines.

    Args:
        timeout_seconds:
            Invalid generation deadline.
    """

    with pytest.raises(ValueError, match="positive and finite"):
        AnswerService(
            AsyncMock(),
            FakeGenerationRepository(),
            "test-model",
            timeout_seconds=timeout_seconds,
        )


@pytest.mark.asyncio
async def test_replays_successful_duplicate_without_generating_again(
    draft: AnswerDraft,
) -> None:
    """Return a stored outcome when an identical submission is repeated.

    Args:
        draft:
            Valid authored draft fixture.
    """

    generator = AsyncMock()
    generator.generate.return_value = draft
    repository = FakeGenerationRepository()
    service = build_answer_service(generator, repository=repository)
    submission_id = uuid4()

    assert await service.execute("Question", "operator", submission_id) == draft
    assert await service.execute("Question", "operator", submission_id) == draft
    generator.generate.assert_awaited_once_with("Question")


@pytest.mark.asyncio
async def test_records_safe_failure_and_links_explicit_retry(
    draft: AnswerDraft,
) -> None:
    """Persist a safe failure category before admitting its explicit retry.

    Args:
        draft:
            Valid authored draft fixture.
    """

    generator = AsyncMock()
    generator.generate.side_effect = RuntimeError("provider-secret-detail")
    repository = FakeGenerationRepository()
    service = build_answer_service(generator, repository=repository)
    failed_submission = uuid4()

    with pytest.raises(GenerationFailed):
        await service.execute("Question", "operator", failed_submission)

    failed_attempt = repository.attempt_ids[failed_submission]
    assert repository.outcomes[failed_attempt] == (AttemptOutcome.FAILED, None)

    generator.generate.side_effect = None
    generator.generate.return_value = draft
    retry_submission = uuid4()
    assert (
        await service.execute("Question", "operator", retry_submission, failed_attempt)
        == draft
    )
    assert repository.requests[retry_submission].retry_of_attempt_id == failed_attempt
