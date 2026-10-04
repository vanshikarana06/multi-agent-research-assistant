import json
import sqlite3
from datetime import UTC, datetime

from app.models.report import ResearchReport

DEFAULT_DB_PATH = "research_runs.db"


def _get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            research_question TEXT NOT NULL,
            status TEXT NOT NULL,
            final_report TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
        """
    )
    return conn


def create_run(run_id: str, research_question: str, db_path: str = DEFAULT_DB_PATH) -> None:
    conn = _get_connection(db_path)
    conn.execute(
        "INSERT INTO runs (run_id, research_question, status, created_at) VALUES (?, ?, ?, ?)",
        (run_id, research_question, "planning", datetime.now(UTC).isoformat()),
    )
    conn.commit()
    conn.close()


def mark_run_completed(run_id: str, report: ResearchReport, db_path: str = DEFAULT_DB_PATH) -> None:
    conn = _get_connection(db_path)
    conn.execute(
        "UPDATE runs SET status = ?, final_report = ?, completed_at = ? WHERE run_id = ?",
        ("done", report.model_dump_json(), datetime.now(UTC).isoformat(), run_id),
    )
    conn.commit()
    conn.close()


def mark_run_failed(run_id: str, error: str, db_path: str = DEFAULT_DB_PATH) -> None:
    conn = _get_connection(db_path)
    conn.execute(
        "UPDATE runs SET status = ?, error = ?, completed_at = ? WHERE run_id = ?",
        ("failed", error, datetime.now(UTC).isoformat(), run_id),
    )
    conn.commit()
    conn.close()


def get_run(run_id: str, db_path: str = DEFAULT_DB_PATH) -> dict | None:
    conn = _get_connection(db_path)
    cursor = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    columns = [desc[0] for desc in cursor.description]
    result = dict(zip(columns, row, strict=True))
    if result["final_report"]:
        result["final_report"] = json.loads(result["final_report"])
    return result
