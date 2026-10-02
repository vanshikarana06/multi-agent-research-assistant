from app.core.exceptions import CitationValidationError
from app.models.finding import Finding
from app.models.report import ResearchReport


def validate_citations(report: ResearchReport, findings: list[Finding]) -> None:
    valid_ids = {f.id for f in findings}

    invalid_ids: set[str] = set()
    for section in report.sections:
        for citation in section.citations:
            if citation.finding_id not in valid_ids:
                invalid_ids.add(citation.finding_id)

    if invalid_ids:
        raise CitationValidationError(
            f"Report cites {len(invalid_ids)} finding_id(s) not present in findings",
            invalid_finding_ids=list(invalid_ids),
        )
