"""Cliente CRM genérico sobre cualquier REST API de tickets (real, configurable).

Pensado para enchufar tu propio backend / un CRM sin cliente dedicado. Hace HTTP
real contra `CRM_GENERIC_BASE_URL` con Bearer `CRM_GENERIC_TOKEN`. Si tu API usa
otras rutas o nombres de campo, ajustá las constantes / `_norm` de abajo.

Contrato asumido (ajustable):
  GET    {base}/tickets?status=open&limit=N   -> {"tickets":[...]} o [...]
  GET    {base}/tickets/{id}                  -> ticket
  POST   {base}/tickets/{id}/replies          -> {body, public}
  POST   {base}/tickets/{id}/notes            -> {body}
  PATCH  {base}/tickets/{id}                  -> {status}
"""

from __future__ import annotations

import requests

from ...config import get_settings


class GenericCRM:
    def __init__(self, timeout: int = 30):
        s = get_settings()
        if not s.crm_generic_base_url:
            raise RuntimeError("Falta CRM_GENERIC_BASE_URL.")
        self.base = s.crm_generic_base_url.rstrip("/")
        self.h = {"Content-Type": "application/json"}
        if s.crm_generic_token:
            self.h["Authorization"] = f"Bearer {s.crm_generic_token}"
        self.timeout = timeout

    def _norm(self, t: dict) -> dict:
        return {
            "id": str(t.get("id") or t.get("ticket_id") or ""),
            "subject": t.get("subject") or t.get("title") or "",
            "body": t.get("body") or t.get("description") or t.get("content") or "",
            "requester": str(t.get("requester") or t.get("customer") or t.get("email") or ""),
            "status": t.get("status") or "",
            "priority": t.get("priority") or "",
            "url": f"{self.base}/tickets/{t.get('id') or t.get('ticket_id')}",
        }

    def list_open_tickets(self, limit: int = 10) -> list[dict]:
        r = requests.get(f"{self.base}/tickets", headers=self.h,
                         params={"status": "open", "limit": limit}, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        items = data.get("tickets", data) if isinstance(data, dict) else data
        return [self._norm(t) for t in items[:limit]]

    def get_ticket(self, ticket_id: str) -> dict:
        r = requests.get(f"{self.base}/tickets/{ticket_id}", headers=self.h, timeout=self.timeout)
        r.raise_for_status()
        return self._norm(r.json())

    def add_reply(self, ticket_id: str, body: str, *, public: bool = True) -> dict:
        r = requests.post(f"{self.base}/tickets/{ticket_id}/replies", headers=self.h,
                          json={"body": body, "public": public}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def add_internal_note(self, ticket_id: str, body: str) -> dict:
        r = requests.post(f"{self.base}/tickets/{ticket_id}/notes", headers=self.h,
                          json={"body": body}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def set_status(self, ticket_id: str, status: str) -> dict:
        r = requests.patch(f"{self.base}/tickets/{ticket_id}", headers=self.h,
                           json={"status": status}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
