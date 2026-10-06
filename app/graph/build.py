from langgraph.checkpoint.redis import RedisSaver

from langgraph.graph import END, START, StateGraph

from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.writer import WriterAgent
from app.graph.nodes import (
    make_plan_node,
    make_research_node,
    make_write_node,
    review_node,
    route_after_review,
)
from app.graph.state import ResearchState
from app.services.llm_client import LLMClient
from app.services.search_client import SearchClient


def build_graph():
    llm_client = LLMClient()
    search_client = SearchClient()

    planner = PlannerAgent(llm_client)
    researcher = ResearcherAgent(llm_client, search_client)
    writer = WriterAgent(llm_client)

    graph_builder = StateGraph(ResearchState)

    graph_builder.add_node("plan", make_plan_node(planner))
    graph_builder.add_node("research", make_research_node(researcher))
    graph_builder.add_node("write", make_write_node(writer))
    graph_builder.add_node("review", review_node)

    graph_builder.add_edge(START, "plan")
    graph_builder.add_edge("plan", "research")
    graph_builder.add_edge("research", "review")
    graph_builder.add_conditional_edges("review", route_after_review)
    graph_builder.add_edge("write", END)

    checkpointer = RedisSaver(redis_url="redis://localhost:6379")
    checkpointer.setup()

    return graph_builder.compile(checkpointer=checkpointer)
