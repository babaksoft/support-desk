"""Application-specific error types."""


class GenerationBusy(Exception):
    """Signal that the single generation slot is occupied."""


class GenerationFailed(Exception):
    """Signal an unavailable or invalid generation result."""


class GenerationTimedOut(Exception):
    """Signal that generation exceeded its deadline."""
