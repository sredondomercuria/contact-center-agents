"""Cliente real de Zendesk Support API.

Auth: API token (HTTP Basic `{email}/token : {api_token}`).
Docs: https://developer.zendesk.com/api-reference/ticketing/
"""

from __future__ import annotations

import requests
from requests.auth import HTTPBasicAuth

from ...config import get_settings

_STATUS_MAP = {"open": "open", "pending": "pending", "solved": "solved"}


class ZendeskCRM:
    def __init__(self, timeout: int = 30):
        s = get_settings()
        if not (s.zendesk_subdomain and s.zendesk_email and s.zendesk_api_token):
            raise RuntimeError("Faltan credenciales de Zendesk (subdomain/email/api_token).")
        self.base = f"https://{s.zendesk_subdomain}.zendesk.com/api/v2"
        self.auth = HTTPBasicAuth(f"{s.zendesk_email}/token", s.zendesk_api_token)
        self.timeout = timeout

    def _norm(self, t: dict) -> dict:
        return {
            "id": str(t.get("id")),
            "subject": t.get("subject", ""),
            "body": t.get("description", ""),
            "requester": str(t.get("requester_id", "")),
            "status": t.get("status", ""),
            "priority": t.get("priority") or "",
            "url": f"{self.base}/tickets/{t.get('id')}.json",
        }

    def list_open_tickets(self, limit: int = 10) -> list[dict]:
        r = requests.get(
            f"{self.base}/search.json",
            auth=self.auth,
            params={"query": "type:ticket status<solved", "sort_by": "created_at", "sort_order": "desc"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return [self._norm(t) for t in r.json().get("results", [])[:limit]]

    def get_ticket(self, ticket_id: str) -> dict:
        r = requests.get(f"{self.base}/tickets/{ticket_id}.json", auth=self.auth, timeout=self.timeout)
        r.raise_for_status()
        return self._norm(r.json()["ticket"])

    def _comment(self, ticket_id: str, body: str, public: bool) -> dict:
        r = requests.put(
            f"{self.base}/tickets/{ticket_id}.json",
            auth=self.auth,
            json={"ticket": {"comment": {"body": body, "public": public}}},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def add_reply(self, ticket_id: str, body: str, *, public: bool = True) -> dict:
        return self._comment(ticket_id, body, public)

    def add_internal_note(self, ticket_id: str, body: str) -> dict:
        return self._comment(ticket_id, body, public=False)

    def set_status(self, ticket_id: str, status: str) -> dict:
        r = requests.put(
            f"{self.base}/tickets/{ticket_id}.json",
            auth=self.auth,
            json={"ticket": {"status": _STATUS_MAP.get(status, status)}},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()
