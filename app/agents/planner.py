from app.models.plan import ResearchPlan
from app.services.llm_client import LLMClient

PLANNER_SYSTEM_PROMPT = """You are a research planning assistant. Given a research \
question, break it down into a structured research plan with at most 5 focused \
subquestions. Each subquestion should be independently researchable. Assign a \
priority (high/medium/low) and note what kind of evidence would best answer it."""


class PlannerAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def create_plan(self, research_question: str) -> ResearchPlan:
        return self._llm_client.generate(
            schema=ResearchPlan,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=research_question,
        )
