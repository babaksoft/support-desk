"""Verify application question-answer policy."""

from unittest.mock import AsyncMock

import pytest

from support_desk.application import AnswerService


@pytest.mark.parametrize("timeout_seconds", [0, -1, float("inf"), float("nan")])
def test_rejects_invalid_generation_timeout(timeout_seconds: float) -> None:
    """Reject non-positive and non-finite generation deadlines.

    Args:
        timeout_seconds:
            Invalid generation deadline.
    """

    with pytest.raises(ValueError, match="positive and finite"):
        AnswerService(AsyncMock(), timeout_seconds=timeout_seconds)
