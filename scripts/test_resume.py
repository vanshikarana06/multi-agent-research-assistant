# quick script, not permanent code - just to prove the mechanism
import uuid

from app.graph.build import build_graph
from app.graph.state import ResearchState

run_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": run_id}}

graph = build_graph()
initial_state = ResearchState(
    run_id=run_id,
    research_question="What are the major evaluation challenges in LLM-based multi-agent systems?",
)

# Run only ONE step, then stop - simulating a crash right after planning
step_count = 0
for step in graph.stream(initial_state, config=config):
    step_count += 1
    print(f"Step {step_count}:", list(step.keys()))
    if step_count >= 1:
        break  # simulate crash here, after just the plan node

print("--- SIMULATED CRASH: stopping here, 'killing' this graph object ---")

# Now: brand NEW graph object, same config, resume with None
fresh_graph = build_graph()
result = fresh_graph.invoke(None, config=config)
print("Resumed run status:", result["status"])
print(
    "Did it have to re-plan? subquestions count:",
    len(result["plan"].subquestions) if result.get("plan") else 0,
)
