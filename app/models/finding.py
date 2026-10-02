# app/models/finding.py
from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class Source(BaseModel):
    url: HttpUrl
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
