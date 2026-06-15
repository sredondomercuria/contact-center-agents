"""Clasificador / Triage. Skill: skills/ticket-triage."""

from __future__ import annotations

import json

from ..config import get_settings
from ..llm import complete_json
from ..schemas import TRIAGE_SCHEMA
from ..state import TicketState

SYSTEM = """\
Sos analista de soporte de {company}. Clasificás un ticket entrante: intención (tema),
sentimiento, prioridad, idioma, un resumen breve y las preguntas concretas a responder.
Sé preciso; la prioridad refleja urgencia e impacto para el cliente.
Si el ticket trae `history`, es el historial de la conversación: interpretá el último
mensaje (`body`) en ese contexto (puede ser una respuesta corta a algo ya preguntado).
"""


def classifier(state: TicketState) -> dict:
    s = get_settings()
    ticket = state.get("ticket", {})
    triage = complete_json(
        system=SYSTEM.format(company=s.company_name),
        user="Ticket:\n" + json.dumps(ticket, ensure_ascii=False, indent=2),
        schema=TRIAGE_SCHEMA,
        model=s.model_classifier,
    )
    return {"triage": triage, "log": [f"classifier: {triage.get('intent')} / {triage.get('priority')}"]}
