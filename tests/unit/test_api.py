from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_start_research_returns_run_id(mocker):
    mocker.patch("app.api.main.run_research")  # prevent real background execution

    response = client.post("/research", json={"research_question": "What is X?"})

    assert response.status_code == 200
    assert "run_id" in response.json()


def test_get_research_status_returns_404_for_unknown_run():
    response = client.get("/research/nonexistent-run-id")
    assert response.status_code == 404
