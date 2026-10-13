import uuid

from app.graph.runner import run_research
from app.storage.trace_store import get_trace

run_id = str(uuid.uuid4())
run_research(
    run_id,
    "What are the major evaluation challenges in LLM-based multi-agent systems?",
)

print("run_id:", run_id)
for e in get_trace(run_id):
    print(e.node, e.status, round(e.latency_ms), "ms", "|", e.summary, "|", e.error)
