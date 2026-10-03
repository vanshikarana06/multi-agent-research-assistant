from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.finding import Finding, Source
from app.models.plan import SubQuestion
from app.services.llm_client import LLMClient
from app.services.search_client import SearchClient

RESEARCHER_SYSTEM_PROMPT = """You are a research assistant. Given a subquestion and \
a numbered list of search results, extract factual claims that help answer the \
subquestion. For each claim, cite which result index it came from. Only use \
information present in the provided results — do not use outside knowledge."""

MAX_RESULTS_PER_DOMAIN = 2


def _limit_results_per_domain(results: list[dict], max_per_domain: int) -> list[dict]:
    domain_counts: dict[str, int] = {}
    limited = []
    for result in results:
        domain = result["url"].split("/")[2]
        if domain_counts.get(domain, 0) >= max_per_domain:
            continue
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        limited.append(result)
    return limited


class ExtractedClaim(BaseModel):
    claim: str
    evidence: str
    source_index: int = Field(..., ge=0)
    confidence: Literal["high", "medium", "low"]


class ExtractedClaims(BaseModel):
    claims: list[ExtractedClaim]


class ResearcherAgent:
    def __init__(self, llm_client: LLMClient, search_client: SearchClient) -> None:
        self._llm_client = llm_client
        self._search_client = search_client

    def research(self, subquestion: SubQuestion) -> list[Finding]:
        results = self._search_client.search(subquestion.question)
        results = _limit_results_per_domain(results, MAX_RESULTS_PER_DOMAIN)

        numbered_results = "\n\n".join(
            f"[{i}] {r['title']} ({r['url']})\n{r['content']}" for i, r in enumerate(results)
        )
        user_prompt = f"Subquestion: {subquestion.question}\n\nSearch results:\n{numbered_results}"

        extracted = self._llm_client.generate(
            schema=ExtractedClaims,
            system_prompt=RESEARCHER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        findings = []
        for claim in extracted.claims:
            if claim.source_index >= len(results):
                continue  # skip claims referencing a non-existent result
            result = results[claim.source_index]
            findings.append(
                Finding(
                    claim=claim.claim,
                    evidence=claim.evidence,
                    source=Source(
                        url=result["url"],
                        title=result["title"],
                        domain=result["url"].split("/")[2],
                        retrieval_time=datetime.now(UTC),
                    ),
                    subquestion_id=subquestion.id,
                    confidence=claim.confidence,
                )
            )
        return findings
