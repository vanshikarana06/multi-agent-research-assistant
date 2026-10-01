from typing import Literal

from pydantic import BaseModel, Field


class SubQuestion(BaseModel):
    id: str
    question: str
    priority: Literal["low", "medium", "high"]
    expected_evidence: str


class ResearchPlan(BaseModel):
    research_objective: str
    subquestions: list[SubQuestion] = Field(..., max_length=5)
    search_strategy: str
