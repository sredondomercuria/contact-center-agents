"""Recuperador de conocimiento (RAG). Skill: skills/knowledge-retrieval.

Genera consultas a partir del ticket y recupera artículos de la base de conocimiento.
"""

from __future__ import annotations

import json

from ..config import get_settings
from ..integrations.knowledge import retrieve
from ..llm import complete_json
from ..schemas import QUERY_SCHEMA
from ..state import TicketState

SYSTEM = """\
Generás 2-4 consultas de búsqueda para encontrar en la base de conocimiento los
artículos que ayuden a resolver este ticket. Consultas cortas y específicas.
"""


def retriever(state: TicketState) -> dict:
    s = get_settings()
    ticket = state.get("ticket", {})
    triage = state.get("triage", {})

    data = complete_json(
        system=SYSTEM,
        user=(
            f"Ticket: {ticket.get('subject')}\n{ticket.get('body')}\n\n"
            f"Intención: {triage.get('intent')} · Preguntas: {triage.get('key_questions')}"
        ),
        schema=QUERY_SCHEMA,
        model=s.model_retriever,
    )
    queries = data.get("queries") or [f"{ticket.get('subject','')} {ticket.get('body','')}"]
    snippets = retrieve(queries, k=4)
    return {
        "knowledge": snippets,
        "log": [f"retriever: {len(snippets)} artículos KB ({len(queries)} consultas)"],
    }
