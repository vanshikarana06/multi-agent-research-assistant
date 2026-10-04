import os
import tempfile

from app.models.report import ResearchReport
from app.storage.run_store import create_run, get_run, mark_run_completed, mark_run_failed


def test_create_and_retrieve_run():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        create_run("run-1", "test question?", db_path=db_path)
        result = get_run("run-1", db_path=db_path)
        assert result is not None
        assert result["status"] == "planning"
        assert result["research_question"] == "test question?"
    finally:
        os.remove(db_path)


def test_mark_run_completed_stores_report():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        create_run("run-2", "test question?", db_path=db_path)
        report = ResearchReport(title="T", executive_summary="S", sections=[])
        mark_run_completed("run-2", report, db_path=db_path)

        result = get_run("run-2", db_path=db_path)
        assert result["status"] == "done"
        assert result["final_report"]["title"] == "T"
    finally:
        os.remove(db_path)


def test_mark_run_failed_stores_error():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        create_run("run-3", "test question?", db_path=db_path)
        mark_run_failed("run-3", "Something broke", db_path=db_path)

        result = get_run("run-3", db_path=db_path)
        assert result["status"] == "failed"
        assert result["error"] == "Something broke"
    finally:
        os.remove(db_path)
