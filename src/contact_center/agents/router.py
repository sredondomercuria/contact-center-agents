"""Router de resolución: ¿auto-responder o escalar a humano? Skill: skills/escalation-routing."""

from __future__ import annotations

import json

from ..config import get_settings
from ..llm import complete_json
from ..schemas import ROUTING_SCHEMA
from ..state import TicketState

SYSTEM = """\
Decidís qué hacer con la respuesta propuesta a un ticket:
- `auto_reply`: enviarla al cliente. Apropiado si QA aprobó, la **confianza es ≥ 75** y el
  caso NO es sensible. El **sentimiento negativo por sí solo NO obliga a escalar** si la
  respuesta resuelve el problema con datos claros de la base de conocimiento.
- `escalate`: derivar a un humano (indicá `team`). Escalá SIEMPRE en casos sensibles
  (reclamo legal, fraude/seguridad, **cancelación** de cuenta/servicio, pedido de datos
  sensibles, cambio de email/identidad, o cliente muy enojado de prioridad alta/urgente),
  y también si la confianza es baja, QA no aprobó, o faltan datos para resolver.

Regla: en casos sensibles, ante la duda escalá; en casos simples bien resueltos por la KB,
auto_reply (aunque el cliente esté molesto).
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
