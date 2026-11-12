"""Verify deterministic Cognito access-token authentication."""

import time
from collections.abc import Mapping

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK

from support_desk.domain import AccessTokenRejected
from support_desk.infrastructure.authentication import CognitoAccessTokenAuthenticator

ISSUER = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_synthetic"
CLIENT_ID = "synthetic-client"


class _StaticSigningKeys:
    """Return one synthetic public signing key."""

    def __init__(self, signing_key: PyJWK) -> None:
        """Store the synthetic signing key.

        Args:
            signing_key:
                Public key returned for every token.
        """

        self._signing_key = signing_key

    def get_signing_key_from_jwt(self, token: str) -> PyJWK:
        """Return the configured public signing key.

        Args:
            token:
                Encoded token requesting a key.

        Returns:
            Configured synthetic public key.
        """

        del token
        return self._signing_key


@pytest.fixture(scope="module")
def signing_material() -> tuple[rsa.RSAPrivateKey, PyJWK]:
    """Create one synthetic RSA signing pair.

    Returns:
        Private signing key and matching public JSON Web Key.
    """

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    jwk["kid"] = "synthetic-key"
    return private_key, PyJWK.from_dict(jwk)


@pytest.mark.asyncio
async def test_authenticates_valid_cognito_access_token(
    signing_material: tuple[rsa.RSAPrivateKey, PyJWK],
) -> None:
    """Return trusted subject and groups from a valid access token.

    Args:
        signing_material:
            Synthetic signing pair.
    """

    private_key, public_key = signing_material
    authenticator = _authenticator(public_key)

    actor = await authenticator.authenticate(_token(private_key))

    assert actor.subject == "synthetic-subject"
    assert actor.groups == frozenset({"operators", "auditors"})


@pytest.mark.asyncio
async def test_accepts_valid_actor_without_groups(
    signing_material: tuple[rsa.RSAPrivateKey, PyJWK],
) -> None:
    """Represent absent Cognito groups as an empty authorization set.

    Args:
        signing_material:
            Synthetic signing pair.
    """

    private_key, public_key = signing_material
    actor = await _authenticator(public_key).authenticate(
        _token(private_key, {"cognito:groups": None})
    )

    assert actor.groups == frozenset()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claims",
    [
        {"client_id": "other-client"},
        {"iss": "https://example.invalid/user-pool"},
        {"token_use": "id"},
        {"exp": 1},
        {"sub": ""},
        {"cognito:groups": "operators"},
    ],
)
async def test_rejects_invalid_cognito_claims(
    signing_material: tuple[rsa.RSAPrivateKey, PyJWK],
    claims: Mapping[str, object],
) -> None:
    """Reject a token outside the configured authentication contract.

    Args:
        signing_material:
            Synthetic signing pair.
        claims:
            Invalid claim override.
    """

    private_key, public_key = signing_material

    with pytest.raises(AccessTokenRejected):
        await _authenticator(public_key).authenticate(_token(private_key, claims))


@pytest.mark.asyncio
async def test_rejects_missing_access_token(
    signing_material: tuple[rsa.RSAPrivateKey, PyJWK],
) -> None:
    """Reject a request without bearer credentials.

    Args:
        signing_material:
            Synthetic signing pair.
    """

    _, public_key = signing_material

    with pytest.raises(AccessTokenRejected):
        await _authenticator(public_key).authenticate(None)


def _authenticator(public_key: PyJWK) -> CognitoAccessTokenAuthenticator:
    """Build a Cognito authenticator with no network dependency.

    Args:
        public_key:
            Synthetic public signing key.

    Returns:
        Cognito authenticator backed by the static key.
    """

    return CognitoAccessTokenAuthenticator(
        issuer=ISSUER,
        client_id=CLIENT_ID,
        signing_keys=_StaticSigningKeys(public_key),
    )


def _token(
    private_key: rsa.RSAPrivateKey,
    overrides: Mapping[str, object] | None = None,
) -> str:
    """Sign a synthetic Cognito access token.

    Args:
        private_key:
            Private RSA signing key.
        overrides:
            Claim replacements for a test case.

    Returns:
        Encoded RS256 access token.
    """

    now = int(time.time())
    claims: dict[str, object] = {
        "client_id": CLIENT_ID,
        "cognito:groups": ["operators", "auditors"],
        "exp": now + 300,
        "iat": now,
        "iss": ISSUER,
        "sub": "synthetic-subject",
        "token_use": "access",
    }
    if overrides is not None:
        for name, value in overrides.items():
            if value is None:
                claims.pop(name, None)
            else:
                claims[name] = value

    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": "synthetic-key"},
    )
