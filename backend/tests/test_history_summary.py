from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.database import repository
from app.main import app


def test_history_current_count_excludes_stable_and_summarizes_all_verdicts(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "DB_PATH", tmp_path / "history.sqlite")
    with TestClient(app) as client:
        repository.create({
            "report_id": "HISTORYTEST01",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "complete",
            "source_text": "Sample submitted source text.",
            "stages": [],
            "claims": [
                {"verdict": "CURRENT"},
                {"verdict": "STABLE"},
                {"verdict": "STALE"},
            ],
            "corrected_answer": "",
            "error": None,
        })
        response = client.get("/api/history")
    assert response.status_code == 200
    item = next(row for row in response.json() if row["report_id"] == "HISTORYTEST01")
    assert item["current_count"] == 1
    assert item["stale_count"] == 1
    assert item["result_summary"] == "1 current · 1 stale · 1 stable"
