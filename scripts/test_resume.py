import uuid

from app.graph.build import build_graph
from app.graph.state import ResearchState

QUESTION = "What are the major evaluation challenges in LLM-based multi-agent systems?"

run_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": run_id}}

graph = build_graph()
initial_state = ResearchState(run_id=run_id, research_question=QUESTION)

# Run only the first node, then abandon this graph object
for step in graph.stream(initial_state, config=config):
    print("Ran before crash:", list(step.keys()))
    break

saved = graph.get_state(config)
print("Next node per checkpoint:", saved.next)
saved_objective = saved.values["plan"].research_objective
print("--- SIMULATED CRASH ---")

fresh_graph = build_graph()
executed = []
for step in fresh_graph.stream(None, config=config):
    executed.append(next(iter(step)))
print("Nodes run after resume:", executed)

final = fresh_graph.get_state(config).values
print("plan node re-ran:", "plan" in executed)
print("Plan unchanged:", final["plan"].research_objective == saved_objective)
print("Final status:", final["status"])
