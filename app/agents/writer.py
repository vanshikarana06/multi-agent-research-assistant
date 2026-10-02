# app/agents/writer.py
from pydantic import BaseModel

from app.models.finding import Finding
from app.models.plan import ResearchPlan
from app.models.report import ResearchReport
from app.services.citation_validator import validate_citations
from app.services.llm_client import LLMClient

WRITER_SYSTEM_PROMPT = """You are a research report writer. Given a research plan \
and a list of findings (each with an id), write a structured report that answers \
the research objective. Every factual claim in the report must be supported by a \
citation referencing a finding's exact id. Do not invent citations or use any \
finding id not provided to you."""


class WriterAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def write_report(self, plan: ResearchPlan, findings: list[Finding]) -> ResearchReport:
        findings_text = "\n\n".join(
            f"[id: {f.id}] {f.claim} (evidence: {f.evidence}, source: {f.source.url})"
            for f in findings
        )
        user_prompt = f"Research objective: {plan.research_objective}\n\nFindings:\n{findings_text}"

        report = self._llm_client.generate(
            schema=ResearchReport,
            system_prompt=WRITER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        validate_citations(report, findings)
        return report
