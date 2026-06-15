"""Router de resolución: ¿auto-responder o escalar a humano? Skill: skills/escalation-routing."""

from __future__ import annotations

import json

from ..config import get_settings
from ..llm import complete_json
from ..schemas import ROUTING_SCHEMA
from ..state import TicketState

SYSTEM = """\
Decidís qué hacer con la respuesta propuesta a un mensaje del cliente. En una conversación,
`auto_reply` es la opción POR DEFECTO: avanzar el chat con el cliente NO requiere un humano.
- `auto_reply`: enviar la respuesta al cliente. Es lo correcto cuando QA aprobó y el caso NO
  es sensible: responder consultas, dar info de tratamientos/precios, ofrecer turnos de la
  agenda, o pedir UN dato para avanzar. Que el tema siga abierto NO es motivo para escalar; el
  sentimiento negativo tampoco, si la respuesta resuelve o avanza.
- `escalate`: derivar a un humano (indicá `team`). Escalá SOLO si el caso es sensible
  (reclamo/queja formal, legal, fraude/seguridad, cancelación, datos sensibles, urgencia
  médica/de salud, cliente muy enojado de alta prioridad) o si la respuesta NO puede avanzar
  (QA no aprobó por un problema real, o el bot admite que no tiene la información).

Coherencia: si la respuesta ya ofrece o resuelve algo concreto (info, turnos, un próximo paso),
es `auto_reply` — nunca escales y a la vez mandes una respuesta resolutiva.
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
