"""Router de resolución: ¿auto-responder o escalar a humano? Skill: skills/escalation-routing."""

from __future__ import annotations

import json

from ..config import get_settings
from ..llm import complete_json
from ..schemas import ROUTING_SCHEMA
from ..state import TicketState

SYSTEM = """\
Decidís qué hacer con la respuesta propuesta a un ticket:
- `auto_reply`: enviarla al cliente. Sólo si QA aprobó, la confianza es alta y el caso
  NO es sensible (sin reclamo legal, fraude, cancelación de cuenta, datos sensibles,
  cliente muy enojado de alta prioridad).
- `escalate`: derivar a un humano (indicá `team`). Si hay dudas, escalá.
`new_status`: open (escalado), pending (esperando al cliente) o solved (resuelto).
"""


def router(state: TicketState) -> dict:
    s = get_settings()
    triage = state.get("triage", {})
    review = state.get("review", {})
    draft = state.get("draft", {})

    routing = complete_json(
        system=SYSTEM,
        user=(
            "TRIAGE:\n" + json.dumps(triage, ensure_ascii=False, indent=2)
            + "\n\nQA:\n" + json.dumps(review, ensure_ascii=False, indent=2)
            + f"\n\nConfianza de la respuesta: {draft.get('confidence')}"
        ),
        schema=ROUTING_SCHEMA,
        model=s.model_router,
    )
    return {"routing": routing, "log": [f"router: {routing.get('action')} ({routing.get('reason','')[:50]})"]}
