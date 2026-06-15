"""Agenda propia: disponibilidad y reservas en NUESTRA base de datos (SQLite).

Es un *tool local* que el agente usa para calendarizar turnos: consulta horarios
libres reales y reserva. Así las conversaciones de turnos se auto-resuelven en vez
de derivar siempre a un humano.

Para producción, reemplazá el almacenamiento por tu sistema de turnos real
(Google Calendar, Calendly, una tabla en tu CRM, etc.) — la interfaz de tools
(`check_availability`, `book_appointment`) no cambia.
"""

from __future__ import annotations

import sqlite3
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

from ..config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS appointments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sede         TEXT NOT NULL,
    treatment    TEXT,
    slot_iso     TEXT NOT NULL,           -- 'YYYY-MM-DDTHH:MM'
    client_name  TEXT,
    client_phone TEXT,
    status       TEXT NOT NULL DEFAULT 'booked',
    created_at   TEXT NOT NULL,
    UNIQUE(sede, slot_iso)                -- no doble reserva del mismo horario/sede
);
"""


def _connect() -> sqlite3.Connection:
    path = Path(get_settings().database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    return conn


def init_db() -> None:
    _connect().close()


def _norm(s: str) -> str:
    """Normaliza para comparar sedes ignorando mayúsculas y acentos."""
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).strip().lower()


def _canonical_sede(sede: str) -> str | None:
    target = _norm(sede)
    for s in get_settings().agenda_sede_list:
        if _norm(s) == target:
            return s
    return None


def _parse_slot(value: str) -> str | None:
    """Acepta 'YYYY-MM-DDTHH:MM' o 'YYYY-MM-DD HH:MM' → 'YYYY-MM-DDTHH:MM'."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.strip().replace(" ", "T"))
        return dt.strftime("%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def _booked_slots(conn: sqlite3.Connection, sede: str) -> set[str]:
    rows = conn.execute(
        "SELECT slot_iso FROM appointments WHERE sede=? AND status='booked'", (sede,)
    ).fetchall()
    return {r["slot_iso"] for r in rows}


def available_slots(
    sede: str, *, date_from: str | None = None, days: int = 7,
    today: date | None = None, now: datetime | None = None, limit: int = 30,
) -> list[dict]:
    """Horarios libres reales: horario comercial (lun-sáb) menos los ya reservados."""
    s = get_settings()
    canonical = _canonical_sede(sede)
    if not canonical:
        return []
    today = today or date.today()
    now = now or datetime.now()
    start = date.fromisoformat(date_from) if date_from else today
    if start < today:
        start = today

    with _connect() as conn:
        booked = _booked_slots(conn, canonical)

    out: list[dict] = []
    for d_off in range(days):
        day = start + timedelta(days=d_off)
        if day.weekday() == 6:  # domingo cerrado
            continue
        hour = s.agenda_open_hour
        minute = 0
        while hour < s.agenda_close_hour:
            slot_dt = datetime(day.year, day.month, day.day, hour, minute)
            slot_iso = slot_dt.strftime("%Y-%m-%dT%H:%M")
            if slot_dt > now and slot_iso not in booked:
                out.append({"date": day.isoformat(), "time": slot_dt.strftime("%H:%M"),
                            "slot_iso": slot_iso, "sede": canonical})
                if len(out) >= limit:
                    return out
            minute += s.agenda_slot_minutes
            hour += minute // 60
            minute %= 60
    return out


def book(*, sede: str, slot_iso: str, treatment: str | None = None,
         client_name: str | None = None, client_phone: str | None = None) -> dict:
    """Reserva un turno en nuestra agenda. Devuelve {ok, ...}."""
    canonical = _canonical_sede(sede)
    if not canonical:
        return {"ok": False, "reason": f"Sede desconocida. Disponibles: {get_settings().agenda_sede_list}"}
    parsed = _parse_slot(slot_iso)
    if not parsed:
        return {"ok": False, "reason": "Formato de fecha/hora inválido (usar YYYY-MM-DDTHH:MM)."}
    if datetime.fromisoformat(parsed) <= datetime.now():
        return {"ok": False, "reason": "Ese horario ya pasó."}
    try:
        with _connect() as conn:
            cur = conn.execute(
                "INSERT INTO appointments (sede, treatment, slot_iso, client_name, client_phone, status, created_at)"
                " VALUES (?,?,?,?,?, 'booked', ?)",
                (canonical, treatment, parsed, client_name, client_phone,
                 datetime.now().astimezone().isoformat()),
            )
            return {"ok": True, "appointment_id": cur.lastrowid, "sede": canonical,
                    "treatment": treatment, "slot_iso": parsed, "client_name": client_name}
    except sqlite3.IntegrityError:
        return {"ok": False, "reason": "Ese horario ya no está disponible, ofrecé otro."}


def list_appointments(sede: str | None = None) -> list[dict]:
    q = "SELECT * FROM appointments WHERE status='booked'"
    args: tuple = ()
    if sede:
        c = _canonical_sede(sede)
        q += " AND sede=?"
        args = (c or sede,)
    with _connect() as conn:
        return [dict(r) for r in conn.execute(q + " ORDER BY slot_iso", args).fetchall()]


# --- Tools que ve el agente (formato de la API de Claude) ---------------------

TOOLS = [
    {
        "name": "check_availability",
        "description": "Consulta horarios de turno LIBRES y reales en la agenda de una sede. "
                       "Usala antes de ofrecer horarios: nunca inventes disponibilidad.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sede": {"type": "string", "description": "Sede donde atenderse."},
                "date_from": {"type": "string", "description": "Fecha inicial YYYY-MM-DD (opcional)."},
                "days": {"type": "integer", "description": "Días a futuro a revisar (default 7)."},
                "treatment": {"type": "string", "description": "Tratamiento de interés (opcional)."},
            },
            "required": ["sede"],
        },
    },
    {
        "name": "book_appointment",
        "description": "Reserva un turno en la agenda. Usala SOLO cuando el cliente eligió un "
                       "horario ofrecido por check_availability y ya tenés su nombre.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sede": {"type": "string"},
                "slot_iso": {"type": "string", "description": "Horario elegido en formato YYYY-MM-DDTHH:MM."},
                "treatment": {"type": "string"},
                "client_name": {"type": "string"},
                "client_phone": {"type": "string"},
            },
            "required": ["sede", "slot_iso", "client_name"],
        },
    },
]


def dispatch(name: str, tool_input: dict) -> dict:
    """Ejecuta una tool de agenda por nombre. Robusto ante input inesperado."""
    inp = tool_input or {}
    if name == "check_availability":
        slots = available_slots(
            inp.get("sede", ""),
            date_from=inp.get("date_from"),
            days=int(inp.get("days") or 7),
        )
        if not slots:
            return {"slots": [], "note": "Sin horarios libres en el rango; ofrecé revisar otra fecha o sede."}
        return {"slots": slots[:8]}
    if name == "book_appointment":
        return book(
            sede=inp.get("sede", ""),
            slot_iso=inp.get("slot_iso", ""),
            treatment=inp.get("treatment"),
            client_name=inp.get("client_name"),
            client_phone=inp.get("client_phone"),
        )
    return {"error": f"tool desconocida: {name}"}
