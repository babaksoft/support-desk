"""Verify API authentication and operator authorization failures."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from support_desk.api import create_app
from support_desk.application import AnswerService
from support_desk.domain import (
    AccessTokenRejected,
    AnswerDraft,
    AuthenticatedActor,
)


class _StaticAuthenticator:
    """Return one configured authenticated actor."""

    def __init__(self, actor: AuthenticatedActor) -> None:
        """Store the authenticated actor.

        Args:
            actor:
                Actor returned for each request.
        """

        self._actor = actor

    async def authenticate(self, access_token: str | None) -> AuthenticatedActor:
        """Return the configured actor.

        Args:
            access_token:
                Bearer token supplied by the request.

        Returns:
            Configured authenticated actor.
        """

        del access_token
        return self._actor


class _RejectingAuthenticator:
    """Reject every bearer token."""

    async def authenticate(self, access_token: str | None) -> AuthenticatedActor:
        """Reject the supplied bearer token.

        Args:
            access_token:
                Bearer token supplied by the request.

        Raises:
            AccessTokenRejected:
                Every request is rejected.
        """

        del access_token
        raise AccessTokenRejected


def test_fails_closed_without_authentication_configuration() -> None:
    """Reject question access when no authenticator is configured."""

    with TestClient(create_app(AnswerService(AsyncMock()))) as client:
        response = client.post("/questions", json={"question": "Hi"})

    assert response.status_code == 503
    assert response.json() == {
        "code": "authentication_unavailable",
        "message": "Authentication is not configured.",
    }


def test_rejects_missing_or_invalid_access_token() -> None:
    """Return a bearer challenge without exposing token-validation details."""

    with TestClient(
        create_app(
            AnswerService(AsyncMock()),
            authenticator=_RejectingAuthenticator(),
        )
    ) as client:
        response = client.post("/questions", json={"question": "Hi"})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Bearer error="invalid_token"'
    assert response.json() == {
        "code": "invalid_access_token",
        "message": "A valid operator access token is required.",
    }


def test_rejects_authenticated_actor_outside_operator_group() -> None:
    """Deny an authenticated actor without application operator access."""

    authenticator = _StaticAuthenticator(
        AuthenticatedActor(
            subject="synthetic-viewer",
            groups=frozenset({"viewers"}),
        )
    )
    with TestClient(
        create_app(AnswerService(AsyncMock()), authenticator=authenticator)
    ) as client:
        response = client.post(
            "/questions",
            headers={"Authorization": "Bearer synthetic-token"},
            json={"question": "Hi"},
        )

    assert response.status_code == 403
    assert response.json() == {
        "code": "operator_access_required",
        "message": "Operator access is required.",
    }


def test_allows_authenticated_operator(
    draft: AnswerDraft,
) -> None:
    """Allow an authenticated actor in the operator group.

    Args:
        draft:
            Valid authored draft fixture.
    """

    generator = AsyncMock()
    generator.generate.return_value = draft
    authenticator = _StaticAuthenticator(
        AuthenticatedActor(
            subject="synthetic-operator",
            groups=frozenset({"operators"}),
        )
    )
    with TestClient(
        create_app(AnswerService(generator), authenticator=authenticator)
    ) as client:
        response = client.post(
            "/questions",
            headers={"Authorization": "Bearer synthetic-token"},
            json={"question": "Hi"},
        )

    assert response.status_code == 200
    assert response.json() == draft.model_dump(mode="json")
