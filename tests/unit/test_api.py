from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.main import MAX_ERROR_CHARS, app
from app.models.trace import TraceEvent

client = TestClient(app)

BASE = datetime(2026, 1, 1, tzinfo=UTC)


def _event(step_id: str, node: str, offset: int = 0, error: str | None = None) -> TraceEvent:
    started = BASE + timedelta(seconds=offset)
    return TraceEvent(
        step_id=step_id,
        run_id="run-1",
        node=node,
        status="error" if error else "ok",
        started_at=started,
        finished_at=started + timedelta(seconds=1),
        latency_ms=1000.0,
        summary="",
        error=error,
    )


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_start_research_returns_run_id(mocker):
    mocker.patch("app.api.main.run_research")  # prevent real background execution

    response = client.post("/research", json={"research_question": "What is X?"})

    assert response.status_code == 200
    assert "run_id" in response.json()


def test_get_research_status_returns_404_for_unknown_run(mocker):
    # Patched so this test never reads the real research_runs.db.
    mocker.patch("app.api.main.get_run", return_value=None)

    response = client.get("/research/nonexistent-run-id")

    assert response.status_code == 404


def test_trace_returns_404_for_unknown_run(mocker):
    mocker.patch("app.api.main.get_run", return_value=None)
    assert client.get("/research/missing/trace").status_code == 404


def test_trace_returns_events_in_order_for_known_run(mocker):
    mocker.patch("app.api.main.get_run", return_value={"run_id": "run-1"})
    mocker.patch(
        "app.api.main.get_trace",
        return_value=[_event("s1", "plan"), _event("s2", "research", offset=5)],
    )

    response = client.get("/research/run-1/trace")

    assert response.status_code == 200
    assert [e["node"] for e in response.json()["events"]] == ["plan", "research"]


def test_trace_truncates_long_error_text(mocker):
    mocker.patch("app.api.main.get_run", return_value={"run_id": "run-1"})
    mocker.patch(
        "app.api.main.get_trace",
        return_value=[_event("s1", "research", error="x" * 1000)],
    )

    response = client.get("/research/run-1/trace")

    error = response.json()["events"][0]["error"]
    assert len(error) <= MAX_ERROR_CHARS
