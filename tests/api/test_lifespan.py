"""Verify API resource lifecycle management."""

from types import TracebackType

from fastapi.testclient import TestClient

from support_desk.api import create_app


class _ManagedResource:
    """Record entry and exit of a synthetic asynchronous resource."""

    def __init__(self, name: str, events: list[str]) -> None:
        """Set the resource name and shared event record.

        Args:
            name:
                Synthetic resource name.
            events:
                Shared lifecycle event record.
        """

        self._name = name
        self._events = events

    async def __aenter__(self) -> object:
        """Record resource entry.

        Returns:
            Entered resource value.
        """

        self._events.append(f"enter:{self._name}")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Record resource exit.

        Args:
            exc_type:
                Exception type raised during application execution.
            exc:
                Exception raised during application execution.
            traceback:
                Exception traceback.
        """

        del exc_type, exc, traceback
        self._events.append(f"exit:{self._name}")


def test_enters_resources_and_releases_them_in_reverse_order() -> None:
    """Manage configured resources for the application lifetime."""

    events: list[str] = []
    resources = (
        _ManagedResource("first", events),
        _ManagedResource("second", events),
    )

    with TestClient(create_app(managed_resources=resources)):
        assert events == ["enter:first", "enter:second"]

    assert events == [
        "enter:first",
        "enter:second",
        "exit:second",
        "exit:first",
    ]
