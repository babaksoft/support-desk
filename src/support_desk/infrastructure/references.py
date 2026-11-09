"""Load the packaged, bounded Boardlight reference corpus."""

from importlib.resources import files

from support_desk.domain import SourceId

SOURCE_FILES = {
    SourceId.PLANS: "plans.md",
    SourceId.UPGRADES: "upgrades.md",
    SourceId.ACCESS: "access.md",
    SourceId.TROUBLESHOOTING: "troubleshooting.md",
}
MAX_LOOKUP_CALLS = 2


class ReferenceLookup:
    """Track sources returned during one bounded generation attempt."""

    def __init__(self) -> None:
        """Initialize the per-attempt lookup budget."""

        self._calls = 0
        self._seen: set[SourceId] = set()

    @property
    def calls(self) -> int:
        """Return the number of accepted lookup calls.

        Returns:
            Number of accepted lookup calls.
        """

        return self._calls

    @property
    def seen(self) -> frozenset[SourceId]:
        """Return source identifiers provided during this attempt.

        Returns:
            Immutable set of returned source identifiers.
        """

        return frozenset(self._seen)

    def lookup(self, source_ids: list[SourceId]) -> str:
        """Return up to four authored sources within two tool calls.

        Args:
            source_ids:
                Stable source identifiers to read.

        Returns:
            Versioned authored Markdown evidence.

        Raises:
            ValueError:
                The call budget or source selection is invalid.
        """

        if not 1 <= len(source_ids) <= 4 or len(set(source_ids)) != len(source_ids):
            raise ValueError("Select one to four unique source IDs.")
        if self._calls >= MAX_LOOKUP_CALLS:
            raise ValueError("Reference lookup call limit exceeded.")
        self._calls += 1

        content = "\n\n".join(
            files("support_desk.infrastructure")
            .joinpath("evidence", SOURCE_FILES[source])
            .read_text(encoding="utf-8")
            for source in source_ids
        )
        self._seen.update(source_ids)

        return content
