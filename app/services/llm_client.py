import time
from typing import TypeVar

from groq import Groq, RateLimitError
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.exceptions import LLMRateLimitError, LLMValidationError

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """
    wraps the raw groq sdk client with reliability behaviour:
    rate-limit retry (this slice), validation retry(next slice.)"""

    def __init__(self, model: str = "openai/gpt-oss-120b") -> None:
        self._client = Groq(api_key=settings.groq_api_key)
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
            f"Respomd with a JSON object matching this schema exactly :{json_schema}"
        )
        messages: list[dict] = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_raw_output = ""
        for attempt in range(max_validation_retries + 1):
            raw_output = self._call_with_rate_limit_retry(messages)
            last_raw_output = raw_output
            try:
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
                            "Please correct it and respond again with valid"
                            " JSON matching the schema."
                        ),
                    }
                )
        raise LLMValidationError("Validation failed ", raw_output=last_raw_output)
