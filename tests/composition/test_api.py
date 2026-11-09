"""Verify API composition from environment settings."""

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from support_desk.composition.api import InferenceSettings, build_app


def test_builds_disabled_api_without_provider_settings(
    monkeypatch: MonkeyPatch,
) -> None:
    """Build the default live but unready API without provider access.

    Args:
        monkeypatch:
            Environment isolation fixture.
    """

    for name in (
        "SUPPORT_DESK_ENABLE_INFERENCE",
        "SUPPORT_DESK_MODEL",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    with TestClient(build_app()) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503


@pytest.mark.parametrize("enable_value", ["true", "yes", "2"])
def test_rejects_invalid_inference_flag(
    monkeypatch: MonkeyPatch, enable_value: str
) -> None:
    """Reject ambiguous inference enablement values.

    Args:
        monkeypatch:
            Environment isolation fixture.
        enable_value:
            Unsupported enablement value.
    """

    monkeypatch.setenv("SUPPORT_DESK_ENABLE_INFERENCE", enable_value)
    with pytest.raises(ValueError, match="must be 0 or 1"):
        InferenceSettings.from_environment()


@pytest.mark.parametrize(
    ("model", "api_key"),
    [("", "synthetic-key"), ("synthetic-model", "")],
)
def test_rejects_incomplete_enabled_inference(
    monkeypatch: MonkeyPatch, model: str, api_key: str
) -> None:
    """Reject enabled inference without both required provider settings.

    Args:
        monkeypatch:
            Environment isolation fixture.
        model:
            Synthetic model setting.
        api_key:
            Synthetic provider credential setting.
    """

    monkeypatch.setenv("SUPPORT_DESK_ENABLE_INFERENCE", "1")
    monkeypatch.setenv("SUPPORT_DESK_MODEL", model)
    monkeypatch.setenv("OPENAI_API_KEY", api_key)
    with pytest.raises(ValueError, match="requires a model and API key"):
        InferenceSettings.from_environment()


def test_builds_enabled_api_without_contacting_provider(
    monkeypatch: MonkeyPatch,
) -> None:
    """Build a ready API while keeping the provider credential out of repr.

    Args:
        monkeypatch:
            Environment isolation fixture.
    """

    monkeypatch.setenv("SUPPORT_DESK_ENABLE_INFERENCE", "1")
    monkeypatch.setenv("SUPPORT_DESK_MODEL", "synthetic-model")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-key")

    settings = InferenceSettings.from_environment()
    assert settings.enabled is True
    assert settings.model == "synthetic-model"
    assert "synthetic-key" not in repr(settings)
    with TestClient(build_app()) as client:
        assert client.get("/health/ready").status_code == 200
