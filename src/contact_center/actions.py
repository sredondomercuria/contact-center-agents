"""Ejecución de la resolución (la "salida"): según el canal del ticket.

- channel == "manychat"  → responde por ManyChat (WhatsApp/IG/FB/TikTok) o marca handoff.
- channel == "crm" (def) → responde/escala en el CRM (Zendesk/HubSpot/genérico).

Reutilizable por el nodo `executor` del grafo y por la UI al aprobar. Respeta `dry_run`:
si está activo, NO toca ningún sistema externo (devuelve la previsualización).
"""

from __future__ import annotations

from .config import get_settings
from .integrations.crm import get_crm
from .integrations.notify import notify_slack


def do_resolve(*, ticket: dict, draft: dict, routing: dict, dry_run: bool) -> dict:
    channel = ticket.get("channel", "crm")
    if channel == "manychat":
        return _resolve_manychat(ticket=ticket, draft=draft, routing=routing, dry_run=dry_run)
    return _resolve_crm(ticket=ticket, draft=draft, routing=routing, dry_run=dry_run)


def _base_result(action: str, dry_run: bool, reply: str, new_status: str) -> dict:
    res = {"dry_run": dry_run, "action": action, "delivery": None, "notified": False, "errors": []}
    if dry_run:
        res["preview"] = {"reply": reply, "new_status": new_status,
                          "would": "responder al cliente" if action == "auto_reply" else "escalar a humano"}
    return res


def _resolve_manychat(*, ticket: dict, draft: dict, routing: dict, dry_run: bool) -> dict:
    s = get_settings()
    action = routing.get("action", "escalate")
    reply = draft.get("reply", "")
    sub = str(ticket.get("id", ""))
    res = _base_result(action, dry_run, reply, routing.get("new_status", ""))
    res["channel"] = ticket.get("subchannel", "manychat")
    if dry_run:
        return res

    try:
        from .integrations.manychat import ManyChatClient

        mc = ManyChatClient()
        if action == "auto_reply":
            mc.send_text(sub, reply)
            res["delivery"] = "sent"
        else:  # escalate: avisar al cliente, marcar handoff y notificar al equipo
            mc.send_text(sub, "Gracias por escribirnos. Te derivo con un agente humano que "
                              "continuará tu caso a la brevedad. 🙌")
            try:
                mc.add_tag(sub, s.manychat_handoff_tag)
            except Exception:  # noqa: BLE001 — el tag puede no existir; no es crítico
                pass
            res["delivery"] = "handoff"
    except Exception as exc:  # noqa: BLE001
        res["errors"].append(f"manychat: {exc}")

    if action == "escalate":
        res["notified"] = notify_slack(
            f"🆘 Conversación {sub} ({res['channel']}) escalada: {ticket.get('subject','')}\n"
            f"Motivo: {routing.get('reason','')}"
        )
    return res


def _resolve_crm(*, ticket: dict, draft: dict, routing: dict, dry_run: bool) -> dict:
    action = routing.get("action", "escalate")
    new_status = routing.get("new_status", "open")
    reply = draft.get("reply", "")
    note = draft.get("internal_note", "")
    ticket_id = str(ticket.get("id", ""))
    res = _base_result(action, dry_run, reply, new_status)
    if dry_run:
        return res

    try:
        crm = get_crm()
        if action == "auto_reply":
            crm.add_reply(ticket_id, reply, public=True)
            if note:
                crm.add_internal_note(ticket_id, note)
            crm.set_status(ticket_id, new_status or "pending")
            res["delivery"] = "replied"
        else:
            crm.add_internal_note(ticket_id, f"[Borrador para revisión]\n{reply}\n\n[Contexto]\n{note}")
            crm.set_status(ticket_id, new_status or "open")
            res["delivery"] = "escalated"
    except Exception as exc:  # noqa: BLE001
        res["errors"].append(f"crm: {exc}")

    if action == "escalate":
        res["notified"] = notify_slack(
            f"🆘 Ticket {ticket_id} escalado: {ticket.get('subject','')}\nMotivo: {routing.get('reason','')}"
        )
    return res
