class ExtractionError(Exception):
    """Base exception for invoice extraction failures."""


class ExtractionRateLimitedError(ExtractionError):
    """Raised when Gemini rate-limits extraction requests."""


class ExtractionFailedError(ExtractionError):
    """Raised when extraction fails for non-rate-limit reasons."""
