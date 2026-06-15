"""Interfaz común de CRM + factory.

Todas las implementaciones normalizan los tickets a este dict:
  {id, subject, body, requester, status, priority, url}

Implementaciones reales: Zendesk, HubSpot y un cliente REST genérico configurable.
Para enchufar otro CRM, escribí una clase con estos métodos y agregala al factory.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...config import get_settings


@runtime_checkable
class CRMClient(Protocol):
    def list_open_tickets(self, limit: int = 10) -> list[dict]: ...
    def get_ticket(self, ticket_id: str) -> dict: ...
    def add_reply(self, ticket_id: str, body: str, *, public: bool = True) -> dict: ...
    def add_internal_note(self, ticket_id: str, body: str) -> dict: ...
    def set_status(self, ticket_id: str, status: str) -> dict: ...


def get_crm() -> CRMClient:
    provider = get_settings().crm_provider.lower()
    if provider == "zendesk":
        from .zendesk import ZendeskCRM

        return ZendeskCRM()
    if provider == "hubspot":
        from .hubspot import HubSpotCRM

        return HubSpotCRM()
    from .generic import GenericCRM

    return GenericCRM()
