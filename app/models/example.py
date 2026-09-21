from pydantic import BaseModel, Field


class MovieRecommendation(BaseModel):
    title: str
    year: int = Field(..., ge=1888)
    genre: str
    one_line_reason: str
