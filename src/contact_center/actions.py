"""Ejecución de la resolución (la "salida" del sistema): CRM + notificación.

Reutilizable por el nodo `executor` del grafo y por la UI al aprobar. Respeta
`dry_run`: si está activo, NO toca el CRM ni envía nada (devuelve la previsualización).
"""

from __future__ import annotations

from .integrations.crm import get_crm
from .integrations.notify import notify_slack


def do_resolve(*, ticket: dict, draft: dict, routing: dict, dry_run: bool) -> dict:
    ticket_id = str(ticket.get("id", ""))
    action = routing.get("action", "escalate")
    new_status = routing.get("new_status", "open")
    reply = draft.get("reply", "")
    note = draft.get("internal_note", "")

    result: dict = {"dry_run": dry_run, "action": action, "crm": None, "notified": False, "errors": []}

    if dry_run:
        result["preview"] = {"reply": reply, "new_status": new_status,
                             "would": "responder al cliente" if action == "auto_reply" else "escalar a humano"}
        return result

    try:
        crm = get_crm()
        if action == "auto_reply":
            crm.add_reply(ticket_id, reply, public=True)
            if note:
                crm.add_internal_note(ticket_id, note)
            crm.set_status(ticket_id, new_status or "pending")
            result["crm"] = "replied"
        else:  # escalate
            crm.add_internal_note(ticket_id, f"[Borrador para revisión]\n{reply}\n\n[Contexto]\n{note}")
            crm.set_status(ticket_id, new_status or "open")
            result["crm"] = "escalated"
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(f"crm: {exc}")

    if action == "escalate":
        team = routing.get("team", "soporte")
        ok = notify_slack(
            f"🆘 Ticket {ticket_id} escalado a *{team}*: {ticket.get('subject','')}\n"
            f"Motivo: {routing.get('reason','')}"
        )
        result["notified"] = ok

    return result
