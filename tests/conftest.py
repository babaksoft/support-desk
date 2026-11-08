"""Shared deterministic question-answer fixtures."""

import pytest

from support_desk.domain import AnswerDraft, Evidence, SourceId


@pytest.fixture
def draft() -> AnswerDraft:
    """Provide a valid unreviewed answer.

    Returns:
        Authored product guidance with a versioned source.
    """

    return AnswerDraft(
        status="answered",
        answer="Free supports three boards per workspace.",
        evidence=(Evidence(source_id=SourceId.PLANS, version="1"),),
        review_status="unreviewed",
    )
