"""Authenticate local and Amazon Cognito operator access."""

import asyncio
from typing import Protocol, cast

import jwt
from jwt import PyJWK, PyJWKClient, PyJWTError

from support_desk.domain import (
    AccessTokenRejected,
    AuthenticatedActor,
)


class SigningKeyProvider(Protocol):
    """Resolve the public signing key selected by a JWT header."""

    def get_signing_key_from_jwt(self, token: str) -> PyJWK:
        """Resolve a signing key for one encoded token.

        Args:
            token:
                Encoded JSON Web Token.

        Returns:
            Public JSON Web Key matching the token key identifier.
        """

        ...


class LocalOperatorAuthenticator:
    """Authenticate a synthetic operator for explicit local development mode.

    Attributes:
        operator_group:
            Group assigned to the synthetic local actor.
    """

    def __init__(self, operator_group: str) -> None:
        """Configure the synthetic local actor.

        Args:
            operator_group:
                Group assigned to the synthetic local actor.
        """

        self.operator_group = operator_group

    async def authenticate(self, access_token: str | None) -> AuthenticatedActor:
        """Return the configured synthetic local actor.

        Args:
            access_token:
                Unused bearer token value.

        Returns:
            Synthetic actor authorized for local operator use cases.
        """

        del access_token
        return AuthenticatedActor(
            subject="local-operator",
            groups=frozenset({self.operator_group}),
        )


class CognitoAccessTokenAuthenticator:
    """Verify Cognito access-token signatures and authentication claims.

    Attributes:
        issuer:
            Exact Cognito user-pool issuer.
        client_id:
            Cognito app client allowed to authenticate operators.
    """

    def __init__(
        self,
        issuer: str,
        client_id: str,
        signing_keys: SigningKeyProvider | None = None,
    ) -> None:
        """Configure Cognito issuer, client, and signing-key resolution.

        Args:
            issuer:
                Exact Cognito user-pool issuer.
            client_id:
                Cognito app client allowed to authenticate operators.
            signing_keys:
                Signing-key provider override for deterministic tests.
        """

        self.issuer = issuer.rstrip("/")
        self.client_id = client_id
        self._signing_keys = signing_keys or PyJWKClient(
            f"{self.issuer}/.well-known/jwks.json",
            cache_keys=True,
            cache_jwk_set=True,
            lifespan=300,
            timeout=5.0,
        )

    async def authenticate(self, access_token: str | None) -> AuthenticatedActor:
        """Verify a Cognito access token without blocking the event loop.

        Args:
            access_token:
                Encoded bearer token, if supplied.

        Returns:
            Actor authenticated by the configured Cognito user pool.

        Raises:
            AccessTokenRejected:
                The token is missing, malformed, expired, incorrectly signed, or
                issued for another user pool, app client, or token use.
        """

        if access_token is None or not access_token.strip():
            raise AccessTokenRejected

        return await asyncio.to_thread(self._authenticate, access_token)

    def _authenticate(self, access_token: str) -> AuthenticatedActor:
        """Verify one token and convert its trusted claims.

        Args:
            access_token:
                Encoded Cognito access token.

        Returns:
            Actor authenticated by the configured Cognito user pool.

        Raises:
            AccessTokenRejected:
                Token verification or trusted-claim validation fails.
        """

        try:
            signing_key = self._signing_keys.get_signing_key_from_jwt(access_token)
            claims = cast(
                dict[str, object],
                jwt.decode(
                    access_token,
                    signing_key.key,
                    algorithms=["RS256"],
                    issuer=self.issuer,
                    options={
                        "require": [
                            "client_id",
                            "exp",
                            "iat",
                            "iss",
                            "sub",
                            "token_use",
                        ],
                        "verify_aud": False,
                    },
                ),
            )
        except (PyJWTError, TypeError, ValueError) as exc:
            raise AccessTokenRejected from exc

        if claims.get("token_use") != "access":
            raise AccessTokenRejected
        if claims.get("client_id") != self.client_id:
            raise AccessTokenRejected

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise AccessTokenRejected

        groups = _parse_groups(claims.get("cognito:groups"))
        return AuthenticatedActor(subject=subject, groups=groups)


def _parse_groups(value: object) -> frozenset[str]:
    """Parse an optional trusted Cognito group claim.

    Args:
        value:
            Decoded `cognito:groups` claim.

    Returns:
        Unique Cognito group names.

    Raises:
        AccessTokenRejected:
            The claim is not an array of bounded non-empty strings.
    """

    if value is None:
        return frozenset()
    if not isinstance(value, list):
        raise AccessTokenRejected
    if any(
        not isinstance(group, str) or not group.strip() or len(group) > 128
        for group in value
    ):
        raise AccessTokenRejected

    return frozenset(value)
