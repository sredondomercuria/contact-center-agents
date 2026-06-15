"""Redactor de respuesta. Skill: skills/response-writing."""

from __future__ import annotations

import json

from ..config import get_settings
from ..llm import complete_json
from ..schemas import RESPONSE_SCHEMA
from ..state import TicketState

SYSTEM = """\
Sos agente de soporte de {company}. Redactás la respuesta al cliente en {lang}, con voz
de marca: {voice}. Reglas:
- Basá la respuesta SÓLO en la base de conocimiento provista. No inventes políticas ni datos.
- Si la KB no alcanza para resolver, decilo y proponé escalar (no inventes una solución).
- Empática, clara y accionable: pasos concretos. Saludo y cierre acordes al sentimiento.
- `internal_note`: contexto para el agente humano (qué falta, riesgos, qué confirmar).
- `sources`: títulos de los artículos KB usados. `confidence`: 0-100.
Si hay NOTAS DE QA, corregí cada punto.
"""


def responder(state: TicketState) -> dict:
    s = get_settings()
    ticket = state.get("ticket", {})
    triage = state.get("triage", {})
    knowledge = state.get("knowledge", [])
    review = state.get("review")
    revision_count = state.get("revision_count", 0)

    ctx = {"ticket": ticket, "triage": triage, "knowledge": knowledge}
    user = "Material:\n" + json.dumps(ctx, ensure_ascii=False, indent=2)
    if review and review.get("verdict") == "needs_revision":
        user += "\n\nNOTAS DE QA (corregí cada punto):\n" + json.dumps(
            review.get("issues", []), ensure_ascii=False, indent=2
        )

    draft = complete_json(
        system=SYSTEM.format(company=s.company_name, lang=s.support_language, voice=s.brand_voice),
        user=user,
        schema=RESPONSE_SCHEMA,
        model=s.model_responder,
        thinking=True,
    )
    return {
        "draft": draft,
        "revision_count": revision_count + 1,
        "log": [f"responder: respuesta propuesta (confianza {draft.get('confidence')})"],
    }
