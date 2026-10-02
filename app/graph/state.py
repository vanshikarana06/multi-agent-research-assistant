# app/graph/state.py
from operator import add
from typing import Annotated, Literal

from pydantic import BaseModel

from app.models.finding import Finding
from app.models.plan import ResearchPlan
from app.models.report import ResearchReport


class ResearchState(BaseModel):
    run_id: str
    research_question: str
    plan: ResearchPlan | None = None
    findings: Annotated[list[Finding], add] = []
    status: Literal["planning", "researching", "writing", "done", "failed"] = "planning"
    research_pass_count: int = 0
    final_report: ResearchReport | None = None
