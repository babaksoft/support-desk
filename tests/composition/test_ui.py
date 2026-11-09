"""Verify explicit Streamlit process settings."""

import pytest
from pydantic import ValidationError

from support_desk.composition.ui import UiSettings


def test_defaults_to_local_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the local API when no override is configured.

    Args:
        monkeypatch:
            Pytest environment patching helper.
    """

    monkeypatch.delenv("SUPPORT_DESK_API_URL", raising=False)
    assert str(UiSettings.from_environment().api_url) == "http://127.0.0.1:8000/"


def test_reads_valid_api_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Accept an explicit Compose service URL.

    Args:
        monkeypatch:
            Pytest environment patching helper.
    """

    monkeypatch.setenv("SUPPORT_DESK_API_URL", "http://api:8000")
    assert str(UiSettings.from_environment().api_url) == "http://api:8000/"


def test_rejects_non_http_api_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an API setting outside the HTTP transport contract.

    Args:
        monkeypatch:
            Pytest environment patching helper.
    """

    monkeypatch.setenv("SUPPORT_DESK_API_URL", "api:8000")
    with pytest.raises(ValidationError):
        UiSettings.from_environment()
