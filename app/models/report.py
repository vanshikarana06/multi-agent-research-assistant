from pydantic import BaseModel


class Citation(BaseModel):
    finding_id: str


class ReportSection(BaseModel):
    heading: str
    content: str
    citations: list[Citation]


class ResearchReport(BaseModel):
    title: str
    executive_summary: str
    sections: list[ReportSection]
