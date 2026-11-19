"""Application-specific error types."""


class GenerationBusy(Exception):
    """Signal that the single generation slot is occupied."""


class GenerationFailed(Exception):
    """Signal an unavailable or invalid generation result."""


class GenerationTimedOut(Exception):
    """Signal that generation exceeded its deadline."""


class GenerationSubmissionConflict(Exception):
    """Signal conflicting reuse of a generation submission identity."""


class GenerationRetryRejected(Exception):
    """Signal an explicit retry that does not target an eligible attempt."""


class GenerationPersistenceFailed(Exception):
    """Signal unavailable durable generation persistence."""
