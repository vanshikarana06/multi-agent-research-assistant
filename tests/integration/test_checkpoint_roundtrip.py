import uuid

import pytest
from langgraph.graph import END, START, StateGraph
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.graph.state import ResearchState
from app.models.finding import Finding, Source
from app.models.plan import ResearchPlan, SubQuestion
from app.storage.checkpointing import make_checkpointer

REDIS_URL = "redis://localhost:6379"


def _redis_available() -> bool:
    try:
        return bool(Redis.from_url(REDIS_URL).ping())
    except RedisConnectionError:
        return False


pytestmark = pytest.mark.skipif(not _redis_available(), reason="Redis is not running")


def test_nested_models_survive_checkpoint_roundtrip():
    plan = ResearchPlan(
        research_objective="o",
        subquestions=[SubQuestion(id="q1", question="?", priority="high", expected_evidence="x")],
        search_strategy="s",
    )
    finding = Finding(
        claim="c",
        evidence="e",
        source=Source(
            url="https://example.com/a",
            title="t",
            domain="example.com",
            retrieval_time="2026-01-01T00:00:00Z",
        ),
        subquestion_id="q1",
        confidence="high",
    )

    def seed_node(state: ResearchState) -> dict:
        return {"plan": plan, "findings": [finding]}

    builder = StateGraph(ResearchState)
    builder.add_node("seed", seed_node)
    builder.add_edge(START, "seed")
    builder.add_edge("seed", END)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        graph = builder.compile(checkpointer=make_checkpointer(REDIS_URL))
        graph.invoke(ResearchState(run_id=thread_id, research_question="q"), config=config)

        # a fresh graph and checkpointer stand in for a new process
        fresh = builder.compile(checkpointer=make_checkpointer(REDIS_URL))
        values = fresh.get_state(config).values

        assert isinstance(values["plan"], ResearchPlan)
        assert isinstance(values["plan"].subquestions[0], SubQuestion)
        assert len(values["findings"]) == 1
        assert isinstance(values["findings"][0], Finding)
        assert isinstance(values["findings"][0].source, Source)
    finally:
        client = Redis.from_url(REDIS_URL)
        for key in client.scan_iter(f"*{thread_id}*"):
            client.delete(key)
