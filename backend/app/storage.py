"""SQLite audit persistence for analysis runs."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "audit.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:12]}"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
              run_id TEXT PRIMARY KEY,
              symbol TEXT NOT NULL,
              company TEXT NOT NULL,
              analysis_type TEXT NOT NULL,
              risk_preference TEXT NOT NULL,
              status TEXT NOT NULL,
              planner_json TEXT,
              verifier_json TEXT,
              guardrail_json TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT NOT NULL,
              event_type TEXT NOT NULL,
              agent_name TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tool_calls (
              tool_call_id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              tool_name TEXT NOT NULL,
              input_json TEXT NOT NULL,
              output_json TEXT NOT NULL,
              evidence_json TEXT NOT NULL,
              latency_ms REAL NOT NULL,
              success INTEGER NOT NULL,
              error_type TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS report_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT NOT NULL,
              report_markdown TEXT NOT NULL,
              report_path TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS eval_results (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT,
              eval_type TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS human_reviews (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT NOT NULL,
              action TEXT NOT NULL,
              reviewer TEXT,
              edited_report TEXT,
              comment TEXT,
              created_at TEXT NOT NULL
            );
            """
        )


def _dump(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def _load(text: str | None, fallback: Any = None) -> Any:
    if not text:
        return fallback
    return json.loads(text)


def create_run(
    run_id: str,
    symbol: str,
    company: str,
    analysis_type: str,
    risk_preference: str,
    status: str = "running",
) -> None:
    init_db()
    now = utc_now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO analysis_runs
            (run_id, symbol, company, analysis_type, risk_preference, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, symbol, company, analysis_type, risk_preference, status, now, now),
        )


def update_run(run_id: str, **fields: Any) -> None:
    if not fields:
        return
    init_db()
    fields["updated_at"] = utc_now()
    assignments = ", ".join(f"{key}=?" for key in fields)
    values = [_dump(value) if key.endswith("_json") or isinstance(value, (dict, list)) else value for key, value in fields.items()]
    with _connect() as conn:
        conn.execute(f"UPDATE analysis_runs SET {assignments} WHERE run_id=?", values + [run_id])


def add_event(run_id: str, event_type: str, agent_name: str, payload: dict[str, Any]) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO agent_events (run_id, event_type, agent_name, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, event_type, agent_name, _dump(payload), utc_now()),
        )


def add_tool_call(run_id: str, record: dict[str, Any]) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO tool_calls
            (tool_call_id, run_id, tool_name, input_json, output_json, evidence_json, latency_ms, success, error_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["tool_call_id"],
                run_id,
                record["tool_name"],
                _dump(record.get("input_args", {})),
                _dump(record.get("output", {})),
                _dump(record.get("evidence_ids", [])),
                float(record.get("latency_ms", 0.0)),
                1 if record.get("success") else 0,
                record.get("error_type"),
                utc_now(),
            ),
        )


def add_report_snapshot(run_id: str, report_markdown: str, report_path: str | None = None) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO report_snapshots (run_id, report_markdown, report_path, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, report_markdown, report_path, utc_now()),
        )


def add_eval_result(eval_type: str, payload: dict[str, Any], run_id: str | None = None) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO eval_results (run_id, eval_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (run_id, eval_type, _dump(payload), utc_now()),
        )


def add_human_review(
    run_id: str,
    action: str,
    reviewer: str | None = None,
    edited_report: str | None = None,
    comment: str | None = None,
) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO human_reviews (run_id, action, reviewer, edited_report, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, action, reviewer, edited_report, comment, utc_now()),
        )


def get_run(run_id: str) -> dict[str, Any] | None:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM analysis_runs WHERE run_id=?", (run_id,)).fetchone()
    if row is None:
        return None
    item = dict(row)
    for key in ("planner_json", "verifier_json", "guardrail_json"):
        item[key.replace("_json", "")] = _load(item.pop(key), {})
    return item


def list_events(run_id: str) -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT event_type, agent_name, payload_json, created_at FROM agent_events WHERE run_id=? ORDER BY id",
            (run_id,),
        ).fetchall()
    return [{**dict(row), "payload": _load(row["payload_json"], {})} for row in rows]


def list_tool_calls(run_id: str) -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM tool_calls WHERE run_id=? ORDER BY created_at", (run_id,)).fetchall()
    return [
        {
            "tool_call_id": row["tool_call_id"],
            "tool_name": row["tool_name"],
            "input_args": _load(row["input_json"], {}),
            "output": _load(row["output_json"], {}),
            "evidence_ids": _load(row["evidence_json"], []),
            "latency_ms": row["latency_ms"],
            "success": bool(row["success"]),
            "error_type": row["error_type"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def get_latest_report(run_id: str) -> dict[str, Any] | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT report_markdown, report_path, created_at FROM report_snapshots
            WHERE run_id=? ORDER BY id DESC LIMIT 1
            """,
            (run_id,),
        ).fetchone()
    return dict(row) if row else None
