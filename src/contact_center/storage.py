"""Persistencia de corridas (1 ticket procesado = 1 fila) en SQLite."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   TEXT,
    subject     TEXT,
    status      TEXT NOT NULL DEFAULT 'drafted',
    priority    TEXT,
    action      TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    state_json  TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    path = Path(get_settings().database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    return conn


def init_db() -> None:
    _connect().close()


def create_run(*, status: str, state: dict) -> int:
    t = state.get("ticket") or {}
    triage = state.get("triage") or {}
    routing = state.get("routing") or {}
    now = _now()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO runs (ticket_id, subject, status, priority, action, created_at, updated_at, state_json)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (str(t.get("id", "")), t.get("subject", ""), status, triage.get("priority", ""),
             routing.get("action", ""), now, now,
             json.dumps(state, ensure_ascii=False, default=str)),
        )
        return cur.lastrowid


def list_runs(limit: int = 100) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, ticket_id, subject, status, priority, action, created_at, updated_at"
            " FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_run(run_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["state"] = json.loads(d.pop("state_json"))
    return d


def update_state(run_id: int, state: dict) -> None:
    routing = state.get("routing") or {}
    with _connect() as conn:
        conn.execute(
            "UPDATE runs SET state_json = ?, action = ?, updated_at = ? WHERE id = ?",
            (json.dumps(state, ensure_ascii=False, default=str), routing.get("action", ""),
             _now(), run_id),
        )


def set_status(run_id: int, status: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE runs SET status = ?, updated_at = ? WHERE id = ?", (status, _now(), run_id))
