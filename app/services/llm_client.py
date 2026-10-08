import time
from typing import TypeVar

from groq import BadRequestError, Groq, RateLimitError
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.exceptions import (
    LLMInvalidJSONError,
    LLMRateLimitError,
    LLMValidationError,
)

T = TypeVar("T", bound=BaseModel)


def _failed_generation(exc: BadRequestError) -> str | None:
    """Return the failed output if this 400 is json_validate_failed, else None."""
    body = exc.body
    if not isinstance(body, dict):
        return None
    error = body.get("error", body)
    if not isinstance(error, dict) or error.get("code") != "json_validate_failed":
        return None
    return str(error.get("failed_generation", ""))


class LLMClient:
    """
    Wraps the raw Groq SDK client with reliability behaviour:
    rate-limit retry, and validation retry with feedback (including provider-side
    json_validate_failed rejections).
    """

    def __init__(self, model: str = "openai/gpt-oss-120b") -> None:
        self._client = Groq(api_key=settings.groq_api_key, timeout=20.0)
        self._model = model

    def _call_with_rate_limit_retry(self, messages: list[dict], max_retries: int = 3) -> str:
        attempt = 0
        while True:
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    response_format={"type": "json_object"},
                )
                return response.choices[0].message.content
            except RateLimitError as exc:
                attempt += 1
                if attempt > max_retries:
                    raise LLMRateLimitError(f"Rate limited after {max_retries} retries") from exc
                retry_after_header = exc.response.headers.get("retry-after")
                retry_after = int(retry_after_header) if retry_after_header else 2**attempt
                print(f"Rate limited, retrying in {retry_after}s (attempt {attempt})")
                time.sleep(retry_after)
            except BadRequestError as exc:
                failed = _failed_generation(exc)
                if failed is None:
                    raise  # some other 400 (bad model, context too long): don't retry
                raise LLMInvalidJSONError(
                    "Provider rejected model output as invalid JSON", raw_output=failed
                ) from exc

    def generate(
        self,
        schema: type[T],
        system_prompt: str,
        user_prompt: str,
        max_validation_retries: int = 2,
    ) -> T:
        json_schema = schema.model_json_schema()
        full_system_prompt = (
            f"{system_prompt}\n\n"
            f"Respond with a JSON object matching this schema exactly: {json_schema}"
        )
        messages: list[dict] = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_raw_output = ""
        for attempt in range(max_validation_retries + 1):
            try:
                raw_output = self._call_with_rate_limit_retry(messages)
                last_raw_output = raw_output
                return schema.model_validate_json(raw_output)
            except ValidationError as exc:
                if attempt >= max_validation_retries:
                    raise LLMValidationError(
                        f"Validation failed after {max_validation_retries} retries: {exc}",
                        raw_output=last_raw_output,
                    ) from exc
                messages.append({"role": "assistant", "content": raw_output})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"That response failed validation with this error: {exc}. "
                            "Please correct it and respond again with valid "
                            "JSON matching the schema."
                        ),
                    }
                )
            except LLMInvalidJSONError as exc:
                last_raw_output = exc.raw_output
                if attempt >= max_validation_retries:
                    raise LLMValidationError(
                        f"Invalid JSON after {max_validation_retries} retries",
                        raw_output=exc.raw_output,
                    ) from exc
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response was not valid JSON. Escape any double "
                            "quotes inside string values, or paraphrase instead of quoting. "
                            "Respond again with valid JSON matching the schema."
                        ),
                    }
                )
        raise LLMValidationError("Validation failed", raw_output=last_raw_output)
