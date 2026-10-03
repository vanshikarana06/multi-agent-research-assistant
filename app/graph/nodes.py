from datetime import UTC, datetime

from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.writer import WriterAgent
from app.graph.state import ResearchState
from app.services.dedup import deduplicate_findings

MAX_RESEARCH_PASSES = 2
MAX_TOTAL_SEARCHES: int = 15  # acc to real Tavily budget
MAX_RUN_DURATION_SECONDS = 180


def make_plan_node(planner: PlannerAgent):
    def plan_node(state: ResearchState) -> dict:
        plan = planner.create_plan(state.research_question)
        return {"plan": plan, "status": "researching"}

    return plan_node


def make_research_node(researcher: ResearcherAgent):
    def research_node(state: ResearchState) -> dict:
        all_findings = []
        searches_this_pass = 0
        for subquestion in state.plan.subquestions:
            all_findings.extend(researcher.research(subquestion))
            searches_this_pass += 1
        return {
            "findings": all_findings,
            "status": "writing",
            "total_searches_used": state.total_searches_used + searches_this_pass,
        }

    return research_node


def make_write_node(writer: WriterAgent):
    def write_node(state: ResearchState) -> dict:
        deduplicated = deduplicate_findings(state.findings)
        report = writer.write_report(state.plan, deduplicated)
        return {"final_report": report, "status": "done"}

    return write_node


def review_node(state: ResearchState) -> dict:
    return {
        "research_pass_count": state.research_pass_count + 1,
    }


def route_after_review(state: ResearchState) -> str:
    elapsed = (datetime.now(UTC) - state.started_at).total_seconds()
    if elapsed >= MAX_RUN_DURATION_SECONDS:
        return "write"
    if len(state.findings) == 0:
        if state.research_pass_count >= MAX_RESEARCH_PASSES:
            return "write"  # give up, write whatever we have (even if empty)
        if state.total_searches_used >= MAX_TOTAL_SEARCHES:
            return "write"
        return "research"
    return "write"
