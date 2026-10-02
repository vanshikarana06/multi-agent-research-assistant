from app.agents.researcher import ExtractedClaim, ExtractedClaims, ResearcherAgent
from app.models.plan import SubQuestion


def test_research_returns_findings_with_real_source_data(mocker):
    subquestion = SubQuestion(
        id="sq1", question="test question?", priority="high", expected_evidence="x"
    )

    fake_search_results = [
        {"url": "https://example.com/a", "title": "Source A", "content": "Content A"},
        {"url": "https://example.com/b", "title": "Source B", "content": "Content B"},
    ]

    fake_extracted = ExtractedClaims(
        claims=[
            ExtractedClaim(
                claim="Test claim",
                evidence="Test evidence",
                source_index=1,  # points at "Source B"
                confidence="high",
            )
        ]
    )

    # TODO: create mock_search_client with .search() returning fake_search_results
    mock_search_client = mocker.Mock()
    mock_search_client.search.return_value = fake_search_results

    # TODO: create mock_llm_client with .generate() returning fake_extracted
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate.return_value = fake_extracted
    # TODO: instantiate ResearcherAgent with both mocks
    agent = ResearcherAgent(llm_client=mock_llm_client, search_client=mock_search_client)

    # call .research(subquestion)
    findings = agent.research(subquestion)
    # assert exactly 1 finding returned
    assert len(findings) == 1
    finding = findings[0]
    # assert the finding's source.url is "https://example.com/b" 
    # (NOT /a — proves index 1 was used correctly)
    assert str(finding.source.url) == "https://example.com/b"
    assert finding.subquestion_id == "sq1"
    assert finding.claim == "Test claim"
    assert finding.evidence == "Test evidence"
    assert finding.confidence == "high"


def test_research_skips_claims_with_invalid_source_index(mocker):
    subquestion = SubQuestion(
        id="sq1", question="test question?", priority="high", expected_evidence="x"
    )

    fake_search_results = [
        {"url": "https://example.com/a", "title": "Source A", "content": "Content A"},
    ]

    fake_extracted = ExtractedClaims(
        claims=[
            ExtractedClaim(
                claim="Valid claim",
                evidence="Valid evidence",
                source_index=0,
                confidence="high",
            ),
            ExtractedClaim(
                claim="Invalid claim",
                evidence="Invalid evidence",
                source_index=5,  # out of range — only 1 result exists
                confidence="high",
            ),
        ]
    )

    mock_search_client = mocker.Mock()
    mock_search_client.search.return_value = fake_search_results

    mock_llm_client = mocker.Mock()
    mock_llm_client.generate.return_value = fake_extracted

    agent = ResearcherAgent(llm_client=mock_llm_client, search_client=mock_search_client)
    findings = agent.research(subquestion)

    assert len(findings) == 1
    assert findings[0].claim == "Valid claim"
