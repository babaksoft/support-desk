"""Define authenticated actor values and token-verification contracts."""

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedActor(BaseModel):
    """Identify an authenticated actor and assigned access groups.

    Attributes:
        subject:
            Stable identity-provider subject.
        groups:
            Identity-provider groups assigned to the actor.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    subject: str = Field(
        min_length=1,
        max_length=256,
        description="Stable identity-provider subject.",
    )
    groups: frozenset[str] = Field(
        description="Identity-provider groups assigned to the actor."
    )


class AccessTokenRejected(Exception):
    """Report that an access token cannot authenticate an actor."""


class AccessTokenAuthenticator(Protocol):
    """Authenticate an optional bearer token into a trusted actor."""

    async def authenticate(self, access_token: str | None) -> AuthenticatedActor:
        """Authenticate one bearer token.

        Args:
            access_token:
                Encoded bearer token, if the request supplied one.

        Returns:
            Authenticated actor with trusted group claims.

        Raises:
            AccessTokenRejected:
                The token is missing or invalid.
        """

        ...
