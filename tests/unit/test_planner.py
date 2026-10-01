from app.agents.planner import PlannerAgent
from app.models.plan import ResearchPlan, SubQuestion


def test_create_plan_returns_valid_research_plan(mocker):
    fake_plan = ResearchPlan(
        research_objective="Test objective",
        subquestions=[
            SubQuestion(id="q1", question="Q1?", priority="high", expected_evidence="x")
        ],
        search_strategy="Test strategy",
    )

    mock_llm_client = mocker.Mock()
    mock_llm_client.generate.return_value = fake_plan

    agent = PlannerAgent(llm_client=mock_llm_client)
    result = agent.create_plan("some research question")

    assert result == fake_plan
    mock_llm_client.generate.assert_called_once()