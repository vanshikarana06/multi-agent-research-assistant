from datetime import UTC, datetime, timedelta

from app.graph.nodes import (
    MAX_RESEARCH_PASSES,
    MAX_RUN_DURATION_SECONDS,
    MAX_TOTAL_SEARCHES,
    route_after_review,
)
from app.graph.state import ResearchState
from app.models.finding import Finding, Source


def test_route_after_review_goes_to_research_when_no_findings_and_budget_remains():
    state = ResearchState(
        run_id="t1",
        research_question="q",
        findings=[],
        research_pass_count=0,
    )
    assert route_after_review(state) == "research"


def test_route_after_review_goes_to_write_when_budget_exhausted_even_with_no_findings():
    state = ResearchState(
        run_id="t1",
        research_question="q",
        findings=[],
        research_pass_count=MAX_RESEARCH_PASSES,
    )
    assert route_after_review(state) == "write"


def test_route_after_review_goes_to_write_when_findings_exist():
    source = Source(
        url="https://example.com",
        title="Test",
        domain="example.com",
        retrieval_time="2026-01-01T00:00:00Z",
    )
    finding = Finding(
        claim="Test claim",
        evidence="Test evidence",
        source=source,
        subquestion_id="sq1",
        confidence="high",
    )
    state = ResearchState(
        run_id="t1",
        research_question="q",
        findings=[finding],
        research_pass_count=0,
    )
    assert route_after_review(state) == "write"


def test_route_after_review_goes_to_write_when_total_search_budget_exhausted():
    state = ResearchState(
        run_id="t1",
        research_question="q",
        findings=[],
        research_pass_count=0,
        total_searches_used=MAX_TOTAL_SEARCHES,  # Set to the maximum allowed searches
    )
    assert route_after_review(state) == "write"


def test_route_after_review_goes_to_write_when_run_duration_exceeded():
    old_start_time = datetime.now(UTC) - timedelta(seconds=MAX_RUN_DURATION_SECONDS + 10)
    state = ResearchState(
        run_id="t1",
        research_question="q",
        findings=[],
        research_pass_count=0,
        started_at=old_start_time,
    )
    assert route_after_review(state) == "write"
