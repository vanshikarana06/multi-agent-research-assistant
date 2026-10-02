from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.writer import WriterAgent
from app.graph.state import ResearchState

MAX_RESEARCH_PASSES = 2


def make_plan_node(planner: PlannerAgent):
    def plan_node(state: ResearchState) -> dict:
        plan = planner.create_plan(state.research_question)
        return {"plan": plan, "status": "researching"}

    return plan_node


def make_research_node(researcher: ResearcherAgent):
    def research_node(state: ResearchState) -> dict:
        all_findings = []
        for subquestion in state.plan.subquestions:
            all_findings.extend(researcher.research(subquestion))
        return {"findings": all_findings, "status": "writing"}

    return research_node


def make_write_node(writer: WriterAgent):
    def write_node(state: ResearchState) -> dict:
        report = writer.write_report(state.plan, state.findings)
        return {"final_report": report, "status": "done"}

    return write_node


def review_node(state: ResearchState) -> dict:
    return {"research_pass_count": state.research_pass_count + 1}


def route_after_review(state: ResearchState) -> str:
    if len(state.findings) == 0:
        if state.research_pass_count >= MAX_RESEARCH_PASSES:
            return "write"  # give up, write whatever we have (even if empty)
        return "research"
    return "write"
