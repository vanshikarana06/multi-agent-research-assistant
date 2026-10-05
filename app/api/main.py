import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from app.graph.runner import run_research
from app.storage.run_store import get_run

app = FastAPI(title="Multi-Agent Research Assistant")


class ResearchRequest(BaseModel):
    research_question: str


class ResearchResponse(BaseModel):
    run_id: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
def start_research(request: ResearchRequest, background_tasks: BackgroundTasks) -> ResearchResponse:
    run_id = str(uuid.uuid4())
    background_tasks.add_task(run_research, run_id, request.research_question)
    return ResearchResponse(run_id=run_id)


@app.get("/research/{run_id}")
def get_research_status(run_id: str) -> dict:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
