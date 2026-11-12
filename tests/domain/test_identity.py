"""Verify authenticated actor values."""

import pytest
from pydantic import ValidationError

from support_desk.domain import AuthenticatedActor


def test_freezes_authenticated_actor() -> None:
    """Preserve the trusted subject and group claims after construction."""

    actor = AuthenticatedActor(
        subject=" synthetic-operator ",
        groups=frozenset({"operators"}),
    )

    assert actor.subject == "synthetic-operator"
    with pytest.raises(ValidationError):
        actor.subject = "changed"


def test_rejects_empty_authenticated_subject() -> None:
    """Reject an actor without a stable identity-provider subject."""

    with pytest.raises(ValidationError):
        AuthenticatedActor(subject=" ", groups=frozenset())
