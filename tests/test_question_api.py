"""Verify the API contract and bounded application execution."""

import asyncio
from functools import partial
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from support_desk.api import create_app
from support_desk.application import AnswerQuestion, GenerationBusy, QuestionRequest
from support_desk.domain import AnswerDraft


def test_returns_unreviewed_draft(draft: AnswerDraft) -> None:
    """Return typed guidance and evidence through the endpoint.

    Args:
        draft:
            Valid authored draft fixture.
    """

    generator = AsyncMock()
    generator.generate.return_value = draft
    with TestClient(create_app(AnswerQuestion(generator))) as client:
        response = client.post("/questions", json={"question": " How many boards? "})
        assert response.status_code == 200
        assert response.json() == draft.model_dump(mode="json")
        assert client.get("/health/ready").status_code == 200
    generator.generate.assert_awaited_once_with("How many boards?")


@pytest.mark.parametrize("question", ["", "   ", "x" * 2049])
def test_rejects_invalid_question(question: str) -> None:
    """Reject empty and oversized questions before generation.

    Args:
        question:
            Invalid authored input.
    """

    generator = AsyncMock()
    with TestClient(create_app(AnswerQuestion(generator))) as client:
        assert client.post("/questions", json={"question": question}).status_code == 422
    generator.generate.assert_not_awaited()


def test_bounds_body_and_rejects_unknown_fields() -> None:
    """Reject excessive JSON and undeclared request fields."""

    with TestClient(create_app()) as client:
        assert client.post("/questions", content=b"x" * 16385).status_code == 413
        assert (
            client.post(
                "/questions", json={"question": "Hi", "model": "other"}
            ).status_code
            == 422
        )


def test_unconfigured_api_is_live_but_unready() -> None:
    """Expose configuration failure without requiring provider access."""

    with TestClient(create_app()) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
        assert client.post("/questions", json={"question": "Hi"}).status_code == 503


@pytest.mark.parametrize(
    "failure, status",
    [(ValueError("secret-provider-detail"), 502), (TimeoutError(), 504)],
)
def test_sanitizes_generation_failures(failure: Exception, status: int) -> None:
    """Map provider failures to safe HTTP errors.

    Args:
        failure:
            Simulated provider exception.
        status:
            Expected HTTP status.
    """

    generator = AsyncMock()
    generator.generate.side_effect = failure
    with TestClient(create_app(AnswerQuestion(generator))) as client:
        response = client.post("/questions", json={"question": "Hi"})
        assert response.status_code == status
        assert "secret-provider-detail" not in response.text


def test_deadline_releases_generation_slot(draft: AnswerDraft) -> None:
    """Cancel a slow generation and admit a subsequent request.

    Args:
        draft:
            Valid authored draft fixture.
    """

    generator = AsyncMock()

    generator.generate.side_effect = partial(_slow_generate, draft)
    with TestClient(
        create_app(AnswerQuestion(generator, timeout_seconds=0.01))
    ) as client:
        assert client.post("/questions", json={"question": "Hi"}).status_code == 504
        generator.generate.side_effect = None
        generator.generate.return_value = draft
        assert client.post("/questions", json={"question": "Hi"}).status_code == 200


def test_rejects_concurrent_generation(draft: AnswerDraft) -> None:
    """Reject an overlapping call and restore admission after cancellation.

    Args:
        draft:
            Valid authored draft fixture.
    """

    asyncio.run(_exercise_concurrent_generation(draft))


async def _slow_generate(draft: AnswerDraft, question: str) -> AnswerDraft:
    """Simulate a provider call longer than the deadline.

    Args:
        draft:
            Draft returned after the simulated delay.
        question:
            Operator question.

    Returns:
        Draft after a simulated delay.
    """

    await asyncio.sleep(1)
    return draft


async def _exercise_concurrent_generation(draft: AnswerDraft) -> None:
    """Coordinate two calls against the single admission slot.

    Args:
        draft:
            Valid authored draft fixture.
    """

    started = asyncio.Event()

    generator = AsyncMock()
    generator.generate.side_effect = partial(_blocking_generate, started, draft)
    service = AnswerQuestion(generator)
    request = QuestionRequest(question="Hi")
    task = asyncio.create_task(service.execute(request))
    await started.wait()
    with pytest.raises(GenerationBusy):
        await service.execute(request)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    generator.generate.side_effect = None
    generator.generate.return_value = draft
    assert await service.execute(request) == draft


async def _blocking_generate(
    started: asyncio.Event, draft: AnswerDraft, question: str
) -> AnswerDraft:
    """Hold the generation slot until cancellation.

    Args:
        started:
            Event signaling that the generation slot is occupied.
        draft:
            Draft returned after release.
        question:
            Operator question.

    Returns:
        Draft after release.
    """

    started.set()
    await asyncio.Event().wait()
    return draft
