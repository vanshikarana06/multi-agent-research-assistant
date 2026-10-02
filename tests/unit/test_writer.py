import pytest

from app.agents.writer import WriterAgent
from app.core.exceptions import CitationValidationError
from app.models.finding import Finding, Source
from app.models.plan import ResearchPlan, SubQuestion
from app.models.report import ResearchReport, ReportSection, Citation


def _make_finding(finding_id: str) -> Finding:
    source = Source(
        url="https://example.com",
        title="Test Source",
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
    finding.id = finding_id
    return finding


def _make_plan() -> ResearchPlan:
    return ResearchPlan(
        research_objective="Test objective",
        subquestions=[
            SubQuestion(id="sq1", question="Q1?", priority="high", expected_evidence="x")
        ],
        search_strategy="Test strategy",
    )


def test_write_report_returns_report_when_citations_are_valid(mocker):
    finding = _make_finding("finding-1")

    fake_report = ResearchReport(
        title="Test Report",
        executive_summary="Summary",
        sections=[
            ReportSection(
                heading="Section 1",
                content="Content",
                citations=[Citation(finding_id="finding-1")],
            )
        ],
    )

    mock_llm_client = mocker.Mock()
    mock_llm_client.generate.return_value = fake_report

    writer = WriterAgent(llm_client=mock_llm_client)
    result = writer.write_report(plan=_make_plan(), findings=[finding])

    assert result == fake_report
    mock_llm_client.generate.assert_called_once()


def test_write_report_raises_when_citation_references_unknown_finding(mocker):
    finding = _make_finding("finding-1")

    fake_report_with_bad_citation = ResearchReport(
        title="Test Report",
        executive_summary="Summary",
        sections=[
            ReportSection(
                heading="Section 1",
                content="Content",
                citations=[Citation(finding_id="finding-DOES-NOT-EXIST")],
            )
        ],
    )

    mock_llm_client = mocker.Mock()
    mock_llm_client.generate.return_value = fake_report_with_bad_citation

    writer = WriterAgent(llm_client=mock_llm_client)

    with pytest.raises(CitationValidationError):
        writer.write_report(plan=_make_plan(), findings=[finding])
