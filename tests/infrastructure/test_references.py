"""Verify bounded reference lookup behavior."""

import pytest

from support_desk.domain import SourceId
from support_desk.infrastructure import ReferenceLookup


def test_tool_budget_is_enforced() -> None:
    """Stop reference execution after two calls."""

    lookup = ReferenceLookup()
    lookup.lookup([SourceId.PLANS])
    lookup.lookup([SourceId.UPGRADES])
    with pytest.raises(ValueError, match="limit"):
        lookup.lookup([SourceId.ACCESS])
    assert SourceId.ACCESS not in lookup.seen
