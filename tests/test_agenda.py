"""Agenda propia: disponibilidad, reserva y dispatch de tools (SQLite temporal)."""

from __future__ import annotations

from datetime import date, datetime


def _stub_settings(tmp_path):
    class S:
        database_path = str(tmp_path / "agenda.db")
        agenda_sede_list = ["CABA", "Morón"]
        agenda_open_hour = 10
        agenda_close_hour = 18
        agenda_slot_minutes = 60

    return S()


def _patch(monkeypatch, tmp_path):
    from contact_center.integrations import agenda

    monkeypatch.setattr(agenda, "get_settings", lambda: _stub_settings(tmp_path))
    return agenda


def test_availability_business_hours(monkeypatch, tmp_path):
    agenda = _patch(monkeypatch, tmp_path)
    far_past = datetime(2000, 1, 1)
    slots = agenda.available_slots("Morón", today=date(2030, 3, 4), days=7, now=far_past)

    assert slots, "debería haber horarios libres"
    assert all(s["sede"] == "Morón" for s in slots)                       # sede canónica
    assert all(10 <= int(s["time"][:2]) < 18 for s in slots)              # horario comercial
    assert all(date.fromisoformat(s["date"]).weekday() != 6 for s in slots)  # domingo cerrado


def test_sede_normalization_and_unknown(monkeypatch, tmp_path):
    agenda = _patch(monkeypatch, tmp_path)
    slots = agenda.available_slots("moron", today=date(2030, 3, 4), days=2, now=datetime(2000, 1, 1))
    assert slots and slots[0]["sede"] == "Morón"          # ignora acento/mayúsculas
    assert agenda.available_slots("Rosario", today=date(2030, 3, 4)) == []  # sede inexistente


def test_book_and_conflict(monkeypatch, tmp_path):
    agenda = _patch(monkeypatch, tmp_path)
    before = agenda.available_slots("CABA", today=date(2030, 3, 4), days=2, now=datetime(2000, 1, 1))
    slot = before[0]["slot_iso"]

    ok = agenda.book(sede="CABA", slot_iso=slot, treatment="Armonización", client_name="Ana")
    assert ok["ok"] and ok["appointment_id"] and ok["sede"] == "CABA"

    after = agenda.available_slots("CABA", today=date(2030, 3, 4), days=2, now=datetime(2000, 1, 1))
    assert slot not in {s["slot_iso"] for s in after}      # ya no se ofrece
    assert len(after) == len(before) - 1

    dup = agenda.book(sede="CABA", slot_iso=slot, client_name="Otro")
    assert dup["ok"] is False                              # no doble reserva


def test_book_rejects_past_and_bad_input(monkeypatch, tmp_path):
    agenda = _patch(monkeypatch, tmp_path)
    assert agenda.book(sede="CABA", slot_iso="2000-01-01T10:00", client_name="X")["ok"] is False
    assert agenda.book(sede="CABA", slot_iso="no-fecha", client_name="X")["ok"] is False
    assert agenda.book(sede="Inexistente", slot_iso="2030-03-04T10:00", client_name="X")["ok"] is False


def test_dispatch(monkeypatch, tmp_path):
    agenda = _patch(monkeypatch, tmp_path)
    out = agenda.dispatch("check_availability", {"sede": "Morón", "date_from": "2030-03-04", "days": 2})
    assert "slots" in out and len(out["slots"]) <= 8
    assert agenda.dispatch("tool_inexistente", {})["error"]
