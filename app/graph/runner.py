import uuid

from app.graph.build import build_graph
from app.graph.state import ResearchState
from app.storage.run_store import create_run, mark_run_completed, mark_run_failed


def run_research(research_question: str) -> dict:
    run_id = str(uuid.uuid4())
    create_run(run_id, research_question)

    graph = build_graph()
    initial_state = ResearchState(run_id=run_id, research_question=research_question)

    try:
        result = graph.invoke(initial_state)
        mark_run_completed(run_id, result["final_report"])
        return {"run_id": run_id, **result}
    except Exception as exc:
        mark_run_failed(run_id, str(exc))
        raise
