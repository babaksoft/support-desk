"""Load the packaged, bounded Boardlight reference corpus."""

from importlib.resources import files

from support_desk.domain import SourceId

SOURCE_FILES = {
    SourceId.PLANS: "plans.md",
    SourceId.UPGRADES: "upgrades.md",
    SourceId.ACCESS: "access.md",
    SourceId.TROUBLESHOOTING: "troubleshooting.md",
}


class ReferenceLookup:
    """Track sources returned during one bounded generation attempt."""

    def __init__(self) -> None:
        """Initialize the per-attempt lookup budget."""

        self.calls = 0
        self.seen: set[SourceId] = set()

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

        self.calls += 1
        if self.calls > 2:
            raise ValueError("Reference lookup call limit exceeded.")
        if not 1 <= len(source_ids) <= 4 or len(set(source_ids)) != len(source_ids):
            raise ValueError("Select one to four unique source IDs.")

        content = "\n\n".join(
            files("support_desk.infrastructure")
            .joinpath("evidence", SOURCE_FILES[source])
            .read_text(encoding="utf-8")
            for source in source_ids
        )
        self.seen.update(source_ids)

        return content
