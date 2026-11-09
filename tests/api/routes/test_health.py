"""Verify API health contracts."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from support_desk.api import create_app
from support_desk.application import AnswerService


def test_configured_api_is_live_and_ready() -> None:
    """Report liveness and readiness when generation is configured."""

    with TestClient(create_app(AnswerService(AsyncMock()))) as client:
        assert client.get("/health/live").json() == {"status": "alive"}
        assert client.get("/health/ready").json() == {"status": "ready"}


def test_unconfigured_api_is_live_but_unready() -> None:
    """Expose configuration failure without requiring provider access."""

    with TestClient(create_app()) as client:
        assert client.get("/health/live").status_code == 200
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {
        "code": "generation_unavailable",
        "message": "Generation is not configured.",
    }
