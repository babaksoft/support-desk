"""Verify application-owned operator authorization."""

import pytest

from support_desk.application import OperatorAccessDenied, OperatorAuthorizer
from support_desk.domain import AuthenticatedActor


def test_authorizes_actor_in_operator_group() -> None:
    """Allow an authenticated actor assigned to the required group."""

    actor = AuthenticatedActor(
        subject="synthetic-operator",
        groups=frozenset({"operators"}),
    )

    OperatorAuthorizer(required_group="operators").authorize(actor)


def test_rejects_actor_outside_operator_group() -> None:
    """Reject an authenticated actor without required group membership."""

    actor = AuthenticatedActor(
        subject="synthetic-viewer",
        groups=frozenset({"viewers"}),
    )

    with pytest.raises(OperatorAccessDenied):
        OperatorAuthorizer(required_group="operators").authorize(actor)
