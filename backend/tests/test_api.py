from __future__ import annotations

from fastapi.testclient import TestClient

from app.database import repository
from app.main import app
import app.routes.verification as routes


def test_health_reports_configuration_without_values(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "groq_configured": True, "tavily_configured": False}
    assert "test-key" not in response.text


def test_verify_creates_report_and_validates_input(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setattr(routes, "run_verification", lambda report_id: None)
    with TestClient(app) as client:
        response = client.post("/api/verify", json={"text": "A sufficiently long sample answer with one factual claim."})
        assert response.status_code == 202
        report_id = response.json()["report_id"]
        report = client.get(f"/api/report/{report_id}")
        assert report.status_code == 200
        assert report.json()["status"] == "processing"
        assert len(report.json()["stages"]) == 5
        invalid = client.post("/api/verify", json={"text": "short"})
        assert invalid.status_code == 422
        deleted = client.delete(f"/api/report/{report_id}")
        assert deleted.status_code == 204
        assert client.get(f"/api/report/{report_id}").status_code == 404
