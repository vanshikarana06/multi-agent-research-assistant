import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from app.models.trace import TraceEvent
from app.storage.trace_store import get_trace, record_event

BASE_TIME = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "trace_test.db")


def _make_event(
    run_id: str,
    step_id: str,
    node: str = "plan",
    offset_seconds: int = 0,
    status: str = "ok",
    error: str | None = None,
) -> TraceEvent:
    started = BASE_TIME + timedelta(seconds=offset_seconds)
    return TraceEvent(
        step_id=step_id,
        run_id=run_id,
        node=node,
        status=status,
        started_at=started,
        finished_at=started + timedelta(milliseconds=250),
        latency_ms=250.0,
        summary=f"{node} finished",
        error=error,
    )


def test_get_trace_returns_empty_list_for_run_with_no_events(db_path):
    # Also covers a brand-new database where the table doesn't exist yet.
    assert get_trace("no-such-run", db_path=db_path) == []


def test_get_trace_orders_events_by_started_at_not_insertion_order(db_path):
    # Inserted out of order on purpose: a missing ORDER BY would fail this test.
    record_event(_make_event("run-1", "s3", node="write", offset_seconds=20), db_path)
    record_event(_make_event("run-1", "s1", node="plan", offset_seconds=0), db_path)
    record_event(_make_event("run-1", "s2", node="research", offset_seconds=10), db_path)

    trace = get_trace("run-1", db_path=db_path)

    assert [e.node for e in trace] == ["plan", "research", "write"]
    assert [e.step_id for e in trace] == ["s1", "s2", "s3"]


def test_get_trace_does_not_mix_events_from_different_runs(db_path):
    record_event(_make_event("run-a", "a1", node="plan"), db_path)
    record_event(_make_event("run-a", "a2", node="research", offset_seconds=5), db_path)
    record_event(_make_event("run-b", "b1", node="plan"), db_path)

    trace_a = get_trace("run-a", db_path=db_path)
    trace_b = get_trace("run-b", db_path=db_path)

    assert {e.step_id for e in trace_a} == {"a1", "a2"}
    assert {e.step_id for e in trace_b} == {"b1"}


def test_error_event_round_trips_with_message_and_fields_intact(db_path):
    original = _make_event(
        "run-1",
        "s1",
        node="research",
        status="error",
        error="LLMValidationError: Invalid JSON after 2 retries",
    )
    record_event(original, db_path)

    (fetched,) = get_trace("run-1", db_path=db_path)

    assert fetched.status == "error"
    assert fetched.error == "LLMValidationError: Invalid JSON after 2 retries"
    assert fetched.node == "research"
    assert fetched.started_at == original.started_at
    assert fetched.finished_at == original.finished_at
    assert fetched.latency_ms == original.latency_ms


def test_ok_event_stores_no_error(db_path):
    record_event(_make_event("run-1", "s1", status="ok"), db_path)

    (fetched,) = get_trace("run-1", db_path=db_path)

    assert fetched.status == "ok"
    assert fetched.error is None


def test_recording_duplicate_step_id_raises(db_path):
    # step_id is the primary key, so a duplicate is an error, not a silent second row.
    record_event(_make_event("run-1", "s1"), db_path)

    with pytest.raises(sqlite3.IntegrityError):
        record_event(_make_event("run-1", "s1"), db_path)
