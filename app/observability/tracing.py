import logging
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from app.models.trace import TraceEvent
from app.storage.trace_store import record_event

logger = logging.getLogger(__name__)


def traced(node_name: str, summarize: Callable[[dict], str] | None = None):
    """Wrap a LangGraph node so each execution writes one TraceEvent.

    - If the node raises, record an "error" event and re-raise the original error.
    - If recording the event fails, log it and carry on. Tracing must never
      change the outcome of a run.
    """

    def decorator(node_fn):
        def wrapper(state):
            started_at = datetime.now(UTC)
            t0 = time.perf_counter()
            try:
                result = node_fn(state)
            except Exception as exc:
                _safe_record(
                    state,
                    node_name,
                    "error",
                    started_at,
                    t0,
                    "",
                    f"{type(exc).__name__}: {exc}",
                )
                raise
            summary = ""
            if summarize is not None:
                try:
                    summary = summarize(result)
                except Exception:
                    summary = "(summary failed)"
            _safe_record(state, node_name, "ok", started_at, t0, summary, None)
            return result

        return wrapper

    return decorator


def _safe_record(state, node, status, started_at, t0, summary, error) -> None:
    try:
        record_event(
            TraceEvent(
                step_id=str(uuid.uuid4()),
                run_id=state.run_id,
                node=node,
                status=status,
                started_at=started_at,
                finished_at=datetime.now(UTC),
                latency_ms=(time.perf_counter() - t0) * 1000,
                summary=summary,
                error=error,
            )
        )
    except Exception:
        logger.warning("failed to record trace event for node %s", node, exc_info=True)
