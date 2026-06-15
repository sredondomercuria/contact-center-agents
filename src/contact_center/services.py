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


def payload_to_ticket(payload: dict) -> dict | None:
    """Convierte el payload de un External Request de ManyChat en un ticket.

    Configurá el cuerpo del External Request en tu Flow de ManyChat, por ejemplo:
      {"subscriber_id":"{{contact_id}}", "channel":"whatsapp",
       "message":"{{last_input_text}}", "name":"{{first_name}} {{last_name}}"}
    El parser tolera nombres alternativos de campo.
    """
    sub = payload.get("subscriber_id") or payload.get("contact_id") or payload.get("id")
    msg = payload.get("message") or payload.get("text") or payload.get("last_input_text") or ""
    if not sub or not str(msg).strip():
        return None
    subchannel = payload.get("channel") or "manychat"
    name = payload.get("name") or payload.get("first_name") or ""
    return {
        "id": str(sub),
        "subject": f"Chat ({subchannel})",
        "body": str(msg),
        "requester": name,
        "status": "open",
        "channel": "manychat",
        "subchannel": subchannel,
    }


def handle_inbound_message(payload: dict) -> dict | None:
    """Procesa un mensaje entrante de ManyChat (omnicanal), con memoria de conversación.

    Carga el historial previo del contacto, lo adjunta al ticket (los agentes lo ven),
    y guarda este mensaje + la respuesta para sostener el multi-turno.
    """
    ticket = payload_to_ticket(payload)
    if not ticket:
        print("[inbound] payload sin subscriber_id o mensaje; ignorado.")
        return None

    contact_id = ticket["id"]
    ticket["history"] = storage.conversation_history(contact_id)   # turnos previos (contexto)
    storage.append_message(contact_id, "client", ticket["body"])   # registra el mensaje entrante

    result = run_for_ticket(ticket)

    reply = (result["state"].get("draft") or {}).get("reply", "")
    storage.append_message(contact_id, "assistant", reply)         # registra nuestra respuesta
    return result


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
