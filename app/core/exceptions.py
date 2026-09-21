class LLMError(Exception):
    """Base exception for all LLM-related failures."""


class LLMRateLimitError(LLMError):
    """Raised when the LLM provider rate-limits us and retries are exhausted."""


class LLMValidationError(LLMError):
    """Raised when the LLM's output fails to validate against the expected schema,
    after all retry attempts are exhausted."""

    def __init__(self, message: str, raw_output: str) -> None:
        super().__init__(message)
        self.raw_output = raw_output
