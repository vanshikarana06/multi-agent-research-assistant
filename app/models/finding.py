from datetime import datetime
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    HttpUrl,
    TypeAdapter,
    ValidationError,
)

_HTTP_URL = TypeAdapter(HttpUrl)


def _validate_http_url(value: str) -> str:
    try:
        _HTTP_URL.validate_python(value)
    except ValidationError as exc:
        raise ValueError(f"invalid http(s) url: {value!r}") from exc
    return value


class Source(BaseModel):
    url: Annotated[str, AfterValidator(_validate_http_url)]
    title: str
    domain: str
    retrieval_time: datetime


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    claim: str
    evidence: str
    source: Source
    subquestion_id: str
    confidence: Literal["high", "medium", "low"]
