"""Persistencia SQLite (archivo temporal)."""

from __future__ import annotations


def test_storage_roundtrip(tmp_path, monkeypatch):
    from contact_center import storage

    class S:
        database_path = str(tmp_path / "t.db")

    monkeypatch.setattr(storage, "get_settings", lambda: S())
    storage.init_db()

    state = {"ticket": {"id": "42", "subject": "Cobro duplicado"},
             "triage": {"priority": "alta"}, "routing": {"action": "escalate"}, "log": []}
    rid = storage.create_run(status="drafted", state=state)
    assert rid == 1

    rows = storage.list_runs()
    assert rows[0]["ticket_id"] == "42"
    assert rows[0]["subject"] == "Cobro duplicado"
    assert rows[0]["status"] == "drafted"

    full = storage.get_run(rid)
    assert full["state"]["triage"]["priority"] == "alta"

    storage.set_status(rid, "resolved")
    assert storage.get_run(rid)["status"] == "resolved"
