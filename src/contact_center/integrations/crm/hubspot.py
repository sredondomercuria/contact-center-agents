"""Cliente real de HubSpot (objetos Ticket de la CRM API v3).

Auth: Private App token (Bearer).
Docs: https://developers.hubspot.com/docs/api/crm/tickets

Nota: enviar un mensaje al cliente requiere la Conversations API. Acá `add_reply` y
`add_internal_note` registran el texto como una **Nota** (engagement) asociada al
ticket — el agente humano la ve y la envía desde HubSpot. `set_status` cambia
`hs_pipeline_stage` (el valor debe ser un stage id válido de tu pipeline).
"""

from __future__ import annotations

import requests

from ...config import get_settings

API = "https://api.hubapi.com"
_PROPS = "subject,content,hs_pipeline_stage,hs_ticket_priority"


class HubSpotCRM:
    def __init__(self, timeout: int = 30):
        s = get_settings()
        if not s.hubspot_token:
            raise RuntimeError("Falta HUBSPOT_TOKEN.")
        self.h = {"Authorization": f"Bearer {s.hubspot_token}", "Content-Type": "application/json"}
        self.timeout = timeout

    def _norm(self, obj: dict) -> dict:
        p = obj.get("properties", {})
        return {
            "id": str(obj.get("id")),
            "subject": p.get("subject", ""),
            "body": p.get("content", ""),
            "requester": "",
            "status": p.get("hs_pipeline_stage", ""),
            "priority": p.get("hs_ticket_priority") or "",
            "url": f"{API}/crm/v3/objects/tickets/{obj.get('id')}",
        }

    def list_open_tickets(self, limit: int = 10) -> list[dict]:
        r = requests.get(
            f"{API}/crm/v3/objects/tickets",
            headers=self.h, params={"limit": limit, "properties": _PROPS, "archived": "false"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return [self._norm(o) for o in r.json().get("results", [])]

    def get_ticket(self, ticket_id: str) -> dict:
        r = requests.get(
            f"{API}/crm/v3/objects/tickets/{ticket_id}",
            headers=self.h, params={"properties": _PROPS}, timeout=self.timeout,
        )
        r.raise_for_status()
        return self._norm(r.json())

    def _note(self, ticket_id: str, body: str) -> dict:
        # Crea una Nota y la asocia al ticket (assoc type 228 = note→ticket).
        r = requests.post(
            f"{API}/crm/v3/objects/notes",
            headers=self.h,
            json={
                "properties": {"hs_note_body": body, "hs_timestamp": _now_ms()},
                "associations": [{
                    "to": {"id": ticket_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 228}],
                }],
            },
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def add_reply(self, ticket_id: str, body: str, *, public: bool = True) -> dict:
        prefix = "[Respuesta propuesta al cliente]\n" if public else "[Nota interna]\n"
        return self._note(ticket_id, prefix + body)

    def add_internal_note(self, ticket_id: str, body: str) -> dict:
        return self._note(ticket_id, "[Nota interna]\n" + body)

    def set_status(self, ticket_id: str, status: str) -> dict:
        # status debe ser un hs_pipeline_stage id válido de tu pipeline de tickets.
        r = requests.patch(
            f"{API}/crm/v3/objects/tickets/{ticket_id}",
            headers=self.h, json={"properties": {"hs_pipeline_stage": status}}, timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()


def _now_ms() -> int:
    import time

    return int(time.time() * 1000)
