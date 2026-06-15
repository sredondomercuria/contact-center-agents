"""Estado compartido del grafo (un ticket por corrida del pipeline)."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict


def _append(a: list, b: list) -> list:
    return (a or []) + (b or [])


class TicketState(TypedDict, total=False):
    # Entrada
    ticket: dict[str, Any]          # {id, subject, body, requester, status, ...}

    # Producido por los agentes
    triage: dict[str, Any]          # classifier: intención, sentimiento, prioridad, idioma
    knowledge: list[dict[str, Any]] # retriever: snippets de KB usados
    draft: dict[str, Any]           # responder: respuesta propuesta
    agenda_trace: list[dict[str, Any]]  # responder: tools de agenda usadas (disponibilidad/reservas)
    review: dict[str, Any]          # critic: veredicto QA
    revision_count: int
    routing: dict[str, Any]         # router: auto_reply | escalate + motivo
    result: dict[str, Any]          # actions: qué se hizo (CRM/notify) o simulación

    log: Annotated[list[str], _append]
