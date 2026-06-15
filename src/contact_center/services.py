"""Servicios de orquestación: procesar tickets, persistir, y resolver desde la UI."""

from __future__ import annotations

from . import storage
from .actions import do_resolve
from .config import get_settings
from .graph import build_graph
from .integrations.crm import get_crm


def run_for_ticket(ticket: dict) -> dict:
    """Corre el pipeline para un ticket y persiste la corrida. Devuelve {run_id, state}."""
    run_id = storage.create_run(status="running", state={"ticket": ticket, "log": []})
    try:
        app = build_graph()
        state = app.invoke({"ticket": ticket, "revision_count": 0, "log": []},
                           config={"recursion_limit": 50})
    except Exception as exc:  # noqa: BLE001
        storage.update_state(run_id, {"ticket": ticket, "log": [f"ERROR: {exc}"], "error": str(exc)})
        storage.set_status(run_id, "failed")
        raise

    res = state.get("result") or {}
    if res.get("dry_run"):
        status = "drafted"          # generado, esperando aprobación humana
    elif res.get("errors"):
        status = "failed"
    else:
        status = "resolved"
    storage.update_state(run_id, state)
    storage.set_status(run_id, status)
    return {"run_id": run_id, "state": state}


def process_open_tickets(limit: int | None = None) -> list[dict]:
    """Trae tickets abiertos del CRM y procesa cada uno. Devuelve resúmenes."""
    s = get_settings()
    crm = get_crm()
    tickets = crm.list_open_tickets(limit or s.num_tickets)
    out = []
    for t in tickets:
        try:
            r = run_for_ticket(t)
            out.append({"ticket_id": t.get("id"), "run_id": r["run_id"], "ok": True})
        except Exception as exc:  # noqa: BLE001
            out.append({"ticket_id": t.get("id"), "ok": False, "error": str(exc)})
    return out


def resolve_run(run_id: int) -> dict:
    """Ejecuta de verdad (dry_run=False) la resolución de una corrida guardada (UI)."""
    run = storage.get_run(run_id)
    if not run:
        raise ValueError(f"run {run_id} no existe")
    state = run["state"]
    res = do_resolve(ticket=state.get("ticket", {}), draft=state.get("draft", {}),
                     routing=state.get("routing", {}), dry_run=False)
    state["result"] = res
    storage.update_state(run_id, state)
    storage.set_status(run_id, "failed" if res.get("errors") else "resolved")
    return res


def save_draft_edits(run_id: int, *, reply: str, internal_note: str) -> None:
    run = storage.get_run(run_id)
    if not run:
        raise ValueError(f"run {run_id} no existe")
    state = run["state"]
    draft = state.setdefault("draft", {})
    draft["reply"] = reply
    draft["internal_note"] = internal_note
    storage.update_state(run_id, state)
