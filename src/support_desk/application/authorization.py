"""Authorize authenticated actors for operator use cases."""

from pydantic import BaseModel, ConfigDict, Field

from support_desk.domain import AuthenticatedActor


class OperatorAccessDenied(Exception):
    """Report that an authenticated actor lacks operator access."""


class OperatorAuthorizer(BaseModel):
    """Require membership in the configured operator group.

    Attributes:
        required_group:
            Identity-provider group allowed to perform operator use cases.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    required_group: str = Field(
        min_length=1,
        max_length=128,
        description="Identity-provider group allowed to perform operator use cases.",
    )

    def authorize(self, actor: AuthenticatedActor) -> None:
        """Require the actor to belong to the operator group.

        Args:
            actor:
                Authenticated actor with trusted group claims.

        Raises:
            OperatorAccessDenied:
                The actor does not belong to the required group.
        """

        if self.required_group not in actor.groups:
            raise OperatorAccessDenied
