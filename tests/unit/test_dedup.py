from app.models.finding import Finding, Source
from app.services.dedup import deduplicate_findings, normalize_url


def test_normalize_url_strips_query_fragment_and_trailing_slash():
    url = "https://arxiv.org/abs/1234/?utm_source=twitter#section2"
    assert normalize_url(url) == "https://arxiv.org/abs/1234"


def _make_finding(url: str) -> Finding:
    source = Source(url=url, title="t", domain="example.com", retrieval_time="2026-01-01T00:00:00Z")
    return Finding(claim="c", evidence="e", source=source, subquestion_id="q1", confidence="high")


def test_deduplicate_findings_removes_duplicate_urls():
    findings = [
        _make_finding("https://arxiv.org/abs/1234"),
        _make_finding("https://arxiv.org/abs/1234/"),  # same, just trailing slash
        _make_finding("https://arxiv.org/abs/5678"),   # genuinely different
    ]
    result = deduplicate_findings(findings)
    assert len(result) == 2