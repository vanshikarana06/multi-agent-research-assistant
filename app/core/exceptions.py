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


class CitationValidationError(Exception):
    """Raised when a report cites a finding_id that doesn't exist in the provided findings."""

    def __init__(self, message: str, invalid_finding_ids: list[str]) -> None:
        super().__init__(message)
        self.invalid_finding_ids = invalid_finding_ids


class LLMInvalidJSONError(LLMError):
    """Raised when the provider rejects the model's output as invalid JSON."""

    def __init__(self, message: str, raw_output: str) -> None:
        super().__init__(message)
        self.raw_output = raw_output
