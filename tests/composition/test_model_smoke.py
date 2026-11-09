"""Verify recoverable evidence from the paid model smoke runner."""

import json
from types import TracebackType
from typing import Self

import pytest
from pytest import CaptureFixture, MonkeyPatch

from support_desk.composition import model_smoke
from support_desk.domain import AnswerDraft, Evidence, SourceId
from support_desk.infrastructure import GenerationDiagnostics


class FakeAsyncOpenAI:
    """Provide an asynchronous client context without provider access."""

    def __init__(self, **_: object) -> None:
        """Accept the production client settings."""

    async def __aenter__(self) -> Self:
        """Enter the fake client context.

        Returns:
            Active fake client.
        """

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the fake client context.

        Args:
            exc_type:
                Exception type raised within the context.
            exc_value:
                Exception raised within the context.
            traceback:
                Traceback associated with the exception.
        """


class FakeAnswerGenerator:
    """Return a completed result that fails an authored postcondition."""

    def __init__(self, client: object, model: str) -> None:
        """Accept the production adapter dependencies.

        Args:
            client:
                Fake provider client.
            model:
                Explicit model identifier.
        """

    async def generate_with_diagnostics(self, question: str) -> GenerationDiagnostics:
        """Return evidence that intentionally contradicts the refund expectation.

        Args:
            question:
                Authored product question.

        Returns:
            Completed generation diagnostics with an unexpected citation.
        """

        return GenerationDiagnostics(
            draft=AnswerDraft(
                status="insufficient_evidence",
                answer="The policy is unavailable.",
                evidence=(Evidence(source_id=SourceId.PLANS, version="1"),),
                review_status="unreviewed",
            ),
            model_calls=2,
            input_tokens=1_000,
            cached_input_tokens=200,
            output_tokens=100,
            reasoning_tokens=20,
            response_ids=("resp_synthetic_1", "resp_synthetic_2"),
            source_ids=(SourceId.PLANS,),
            lookup_calls=1,
        )


@pytest.mark.asyncio
async def test_emits_completed_case_before_postcondition_failure(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Preserve paid case evidence when an authored expectation fails.

    Args:
        monkeypatch:
            Replace provider dependencies and settings.
        capsys:
            Capture the sanitized JSON Lines output.
    """

    monkeypatch.setenv("SUPPORT_DESK_ENABLE_INFERENCE", "1")
    monkeypatch.setenv("SUPPORT_DESK_MODEL", model_smoke.MODEL_ID)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    monkeypatch.setattr(model_smoke, "AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setattr(model_smoke, "AgentsAnswerGenerator", FakeAnswerGenerator)

    with pytest.raises(RuntimeError, match="draft evidence"):
        await model_smoke.run_smoke("refund-policy")

    record = json.loads(capsys.readouterr().out)
    assert record["event"] == "case_completed"
    assert record["result"]["response_ids"] == [
        "resp_synthetic_1",
        "resp_synthetic_2",
    ]
    assert record["result"]["estimated_cost_usd"] == "0.00106500"
