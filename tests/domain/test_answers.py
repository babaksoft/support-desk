"""Verify domain answer-draft invariants."""

import pytest
from pydantic import ValidationError

from support_desk.domain import AnswerDraft, Evidence, SourceId


def test_answered_draft_requires_evidence() -> None:
    """Reject an answered draft without supporting evidence."""

    with pytest.raises(ValidationError, match="requires evidence"):
        AnswerDraft(
            status="answered",
            answer="Unsupported answer.",
            evidence=(),
            review_status="unreviewed",
        )


def test_draft_rejects_duplicate_evidence() -> None:
    """Reject repeated source revisions."""

    evidence = Evidence(source_id=SourceId.PLANS, version="1")
    with pytest.raises(ValidationError, match="must be unique"):
        AnswerDraft(
            status="answered",
            answer="Free supports three boards.",
            evidence=(evidence, evidence),
            review_status="unreviewed",
        )
