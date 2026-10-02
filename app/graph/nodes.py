from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.writer import WriterAgent
from app.graph.state import ResearchState


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
