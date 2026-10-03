from urllib.parse import urlparse, urlunparse

from app.models.finding import Finding


def normalize_url(url: str) -> str:
    parsed = urlparse(str(url))
    normalized = parsed._replace(query="", fragment="", path=parsed.path.rstrip("/"))
    return urlunparse(normalized)


def deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    seen_urls: set[str] = set()
    deduplicated = []
    for finding in findings:
        normalized = normalize_url(str(finding.source.url))
        if normalized in seen_urls:
            continue
        seen_urls.add(normalized)
        deduplicated.append(finding)
    return deduplicated
