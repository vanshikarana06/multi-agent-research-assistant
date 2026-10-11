from types import SimpleNamespace

import pytest

from app.observability.tracing import traced


def _state(run_id: str = "run-1"):
    return SimpleNamespace(run_id=run_id)


def test_successful_node_returns_result_and_records_ok_event(mocker):
    record = mocker.patch("app.observability.tracing.record_event")

    @traced("plan", lambda r: f"{len(r['items'])} items")
    def node(state):
        return {"items": [1, 2, 3]}

    result = node(_state())

    assert result == {"items": [1, 2, 3]}
    record.assert_called_once()
    event = record.call_args.args[0]
    assert event.run_id == "run-1"
    assert event.node == "plan"
    assert event.status == "ok"
    assert event.summary == "3 items"
    assert event.error is None


def test_failing_node_reraises_original_error_and_records_error_event(mocker):
    record = mocker.patch("app.observability.tracing.record_event")

    @traced("research")
    def node(state):
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        node(_state())

    record.assert_called_once()
    event = record.call_args.args[0]
    assert event.status == "error"
    assert event.error == "ValueError: boom"


def test_recording_failure_does_not_change_node_result(mocker):
    mocker.patch("app.observability.tracing.record_event", side_effect=OSError("disk full"))

    @traced("write")
    def node(state):
        return {"ok": True}

    assert node(_state()) == {"ok": True}


def test_recording_failure_does_not_mask_node_error(mocker):
    mocker.patch("app.observability.tracing.record_event", side_effect=OSError("disk full"))

    @traced("write")
    def node(state):
        raise ValueError("real failure")

    with pytest.raises(ValueError, match="real failure"):
        node(_state())
