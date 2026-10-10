from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TraceEvent(BaseModel):
    step_id: str
    run_id: str
    node: str
    status: Literal["ok", "error"]
    started_at: datetime
    finished_at: datetime
    latency_ms: float
    summary: str = ""
    error: str | None = None
