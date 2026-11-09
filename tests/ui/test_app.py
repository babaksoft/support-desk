"""Verify the Streamlit question journey."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from support_desk.domain import AnswerDraft
from support_desk.ui import ApiQuestionFailure, HttpQuestionClient

UI_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "support_desk"
    / "composition"
    / "ui.py"
)


def _unexpected_ask(client: HttpQuestionClient, question: str) -> AnswerDraft:
    """Fail if the UI submits a blank question.

    Args:
        client:
            Configured HTTP client.
        question:
            Operator-authored question.

    Raises:
        AssertionError:
            The UI called the API for whitespace.
    """

    raise AssertionError("Blank question reached the API.")


def _fail_ask(client: HttpQuestionClient, question: str) -> AnswerDraft:
    """Return a declared API failure.

    Args:
        client:
            Configured HTTP client.
        question:
            Operator-authored question.

    Raises:
        ApiQuestionFailure:
            Generation is currently busy.
    """

    raise ApiQuestionFailure(
        "generation_busy", "Generation is busy; please try again later."
    )


def test_displays_unreviewed_draft_and_evidence(
    monkeypatch: pytest.MonkeyPatch, draft: AnswerDraft
) -> None:
    """Follow an authored question through the form to its evidence.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
        draft:
            Valid authored draft fixture.
    """

    questions: list[str] = []

    def ask(client: HttpQuestionClient, question: str) -> AnswerDraft:
        """Record the UI request and return deterministic guidance.

        Args:
            client:
                Configured HTTP client.
            question:
                Operator-authored question.

        Returns:
            Deterministic answer draft.
        """

        questions.append(question)
        return draft

    monkeypatch.setattr(HttpQuestionClient, "ask", ask)
    app = AppTest.from_file(UI_SCRIPT)
    app.run()
    app.text_area[0].input("  How many boards can a Free workspace have?  ")
    app.button[0].click().run()

    assert not app.exception
    assert questions == ["How many boards can a Free workspace have?"]
    assert any("Unreviewed draft" in warning.value for warning in app.warning)
    assert any(draft.answer in markdown.value for markdown in app.markdown)
    assert any("BL-PLANS" in markdown.value for markdown in app.markdown)


def test_prompts_for_nonempty_question(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject whitespace before making an API request.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
    """

    monkeypatch.setattr(HttpQuestionClient, "ask", _unexpected_ask)
    app = AppTest.from_file(UI_SCRIPT)
    app.run()
    app.text_area[0].input("   ")
    app.button[0].click().run()

    assert not app.exception
    assert app.warning[0].value == (
        "Enter a product question before generating a draft."
    )


def test_displays_safe_api_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Display useful retry guidance returned by the API.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
    """

    monkeypatch.setattr(HttpQuestionClient, "ask", _fail_ask)
    app = AppTest.from_file(UI_SCRIPT)
    app.run()
    app.text_area[0].input("How many boards?")
    app.button[0].click().run()

    assert not app.exception
    assert app.error[0].value == "Generation is busy; please try again later."
