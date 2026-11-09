"""Verify the API contract and bounded application execution."""

import asyncio
from functools import partial
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from support_desk.api import create_app
from support_desk.api.schemas import AnswerRequest
from support_desk.application import AnswerService, GenerationBusy
from support_desk.domain import AnswerDraft


def test_returns_unreviewed_draft(draft: AnswerDraft) -> None:
    """Return typed guidance and evidence through the endpoint.

    Args:
        draft:
            Valid authored draft fixture.
    """

    generator = AsyncMock()
    generator.generate.return_value = draft
    with TestClient(create_app(AnswerService(generator))) as client:
        response = client.post("/questions", json={"question": " How many boards? "})
        assert response.status_code == 200
        assert response.json() == draft.model_dump(mode="json")
    generator.generate.assert_awaited_once_with("How many boards?")


@pytest.mark.parametrize("question", ["", "   ", "x" * 2049])
def test_rejects_invalid_question(question: str) -> None:
    """Reject empty and oversized questions before generation.

    Args:
        question:
            Invalid authored input.
    """

    generator = AsyncMock()
    with TestClient(create_app(AnswerService(generator))) as client:
        assert client.post("/questions", json={"question": question}).status_code == 422
    generator.generate.assert_not_awaited()


def test_bounds_body_and_rejects_unknown_fields() -> None:
    """Reject excessive JSON and undeclared request fields."""

    with TestClient(create_app()) as client:
        response = client.post("/questions", content=b"x" * 16385)
        assert response.status_code == 413
        assert response.json() == {
            "code": "request_too_large",
            "message": "Request body exceeds 16384 bytes.",
        }
        assert (
            client.post(
                "/questions", json={"question": "Hi", "model": "other"}
            ).status_code
            == 422
        )


def test_unconfigured_api_rejects_generation() -> None:
    """Expose unavailable generation without requiring provider access."""

    with TestClient(create_app()) as client:
        question = client.post("/questions", json={"question": "Hi"})
        assert question.status_code == 503
        assert question.json() == {
            "code": "generation_unavailable",
            "message": "Generation is not configured.",
        }


def test_reports_busy_generation_with_retry_guidance() -> None:
    """Return a stable busy response and retry delay."""

    service = AsyncMock(spec=AnswerService)
    service.execute.side_effect = GenerationBusy
    with TestClient(create_app(service)) as client:
        response = client.post("/questions", json={"question": "Hi"})
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "5"
    assert response.json() == {
        "code": "generation_busy",
        "message": "Generation is busy; please try again later.",
    }


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
    with TestClient(create_app(AnswerService(generator))) as client:
        response = client.post("/questions", json={"question": "Hi"})
        assert response.status_code == status
        assert response.json()["code"] in {
            "generation_failed",
            "generation_timed_out",
        }
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
        create_app(AnswerService(generator, timeout_seconds=0.01))
    ) as client:
        assert client.post("/questions", json={"question": "Hi"}).status_code == 504
        generator.generate.side_effect = None
        generator.generate.return_value = draft
        assert client.post("/questions", json={"question": "Hi"}).status_code == 200


@pytest.mark.asyncio
async def test_rejects_concurrent_generation(draft: AnswerDraft) -> None:
    """Reject an overlapping call and restore admission after cancellation.

    Args:
        draft:
            Valid authored draft fixture.
    """

    started = asyncio.Event()

    generator = AsyncMock()
    generator.generate.side_effect = partial(_blocking_generate, started, draft)
    service = AnswerService(generator)
    request = AnswerRequest(question="Hi")
    task = asyncio.create_task(service.execute(request.question))
    await started.wait()
    with pytest.raises(GenerationBusy):
        await service.execute(request.question)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    generator.generate.side_effect = None
    generator.generate.return_value = draft
    assert await service.execute(request.question) == draft


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
