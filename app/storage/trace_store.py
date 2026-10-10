import sqlite3
from contextlib import closing

from app.models.trace import TraceEvent
from app.storage.run_store import DEFAULT_DB_PATH


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trace_events (
            step_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            node TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            latency_ms REAL NOT NULL,
            summary TEXT NOT NULL,
            error TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_trace_events_run_id ON trace_events (run_id, started_at)"
    )
    return conn


def record_event(event: TraceEvent, db_path: str = DEFAULT_DB_PATH) -> None:
    with closing(_connect(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO trace_events
                (step_id, run_id, node, status, started_at,
                 finished_at, latency_ms, summary, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.step_id,
                event.run_id,
                event.node,
                event.status,
                event.started_at.isoformat(),
                event.finished_at.isoformat(),
                event.latency_ms,
                event.summary,
                event.error,
            ),
        )
        conn.commit()


def get_trace(run_id: str, db_path: str = DEFAULT_DB_PATH) -> list[TraceEvent]:
    with closing(_connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT step_id, run_id, node, status, started_at,
                   finished_at, latency_ms, summary, error
            FROM trace_events
            WHERE run_id = ?
            ORDER BY started_at, rowid
            """,
            (run_id,),
        ).fetchall()
    return [TraceEvent(**dict(row)) for row in rows]
