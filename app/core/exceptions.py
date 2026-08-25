class ExtractionError(Exception):
    """Base exception for invoice extraction failures."""


class ExtractionRateLimitedError(ExtractionError):
    """Raised when Gemini rate-limits extraction requests."""


class ExtractionFailedError(ExtractionError):
    """Raised when extraction fails for non-rate-limit reasons."""


class IllegalStatusTransitionError(Exception):
    """Raised when an invoice status transition is not allowed."""

    def __init__(self, current_status, attempted_status):
        super().__init__(
            f"Illegal invoice status transition from {current_status} "
            f"to {attempted_status}"
        )
