from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DB_PATH = Path(os.getenv("VERITY_DB_PATH", "data/verity.sqlite"))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize() -> None:
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS verification_reports (
            report_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            source_text TEXT NOT NULL,
            report_json TEXT NOT NULL
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_reports_created ON verification_reports(created_at DESC)")


def create(report: dict[str, Any]) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO verification_reports(report_id, created_at, status, source_text, report_json) VALUES(?,?,?,?,?)",
            (report["report_id"], report["created_at"], report["status"], report["source_text"], json.dumps(report)),
        )


def get(report_id: str) -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute("SELECT report_json FROM verification_reports WHERE report_id = ?", (report_id,)).fetchone()
    return json.loads(row["report_json"]) if row else None


def update(report: dict[str, Any]) -> None:
    with connect() as db:
        db.execute(
            "UPDATE verification_reports SET status=?, report_json=? WHERE report_id=?",
            (report["status"], json.dumps(report), report["report_id"]),
        )


def list_reports(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute("SELECT report_json FROM verification_reports ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [json.loads(row["report_json"]) for row in rows]


def delete(report_id: str) -> bool:
    with connect() as db:
        cursor = db.execute("DELETE FROM verification_reports WHERE report_id = ?", (report_id,))
    return cursor.rowcount > 0
