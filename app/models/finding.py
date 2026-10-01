# app/models/finding.py
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl


class Source(BaseModel):
    url: HttpUrl
    title: str
    domain: str
    retrieval_time: datetime


class Finding(BaseModel):
    claim: str
    evidence: str
    source: Source
    subquestion_id: str
    confidence: Literal["high", "medium", "low"]
