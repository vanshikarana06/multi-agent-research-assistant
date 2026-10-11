import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from app.graph.runner import run_research
from app.models.trace import TraceEvent
from app.storage.run_store import get_run
from app.storage.trace_store import get_trace

app = FastAPI(title="Multi-Agent Research Assistant")

MAX_ERROR_CHARS = 300


class ResearchRequest(BaseModel):
    research_question: str


class ResearchResponse(BaseModel):
    run_id: str


class TraceResponse(BaseModel):
    run_id: str
    events: list[TraceEvent]


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


def _truncate_error(event: TraceEvent) -> TraceEvent:
    if event.error is not None and len(event.error) > MAX_ERROR_CHARS:
        truncated_error = event.error[: MAX_ERROR_CHARS - 3] + "..."
        return event.model_copy(update={"error": truncated_error})
    return event


@app.get("/research/{run_id}/trace", response_model=TraceResponse)
def get_research_trace(run_id: str) -> TraceResponse:
    if get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    events = [_truncate_error(e) for e in get_trace(run_id)]
    return TraceResponse(run_id=run_id, events=events)
