"""Crítico de calidad (QA) de la respuesta. Skill: skills/qa-review."""

from __future__ import annotations

import json

from ..config import get_settings
from ..llm import complete_json
from ..schemas import REVIEW_SCHEMA
from ..state import TicketState

SYSTEM = """\
Sos QA de soporte de {company}, con mirada adversarial. Revisás la respuesta propuesta
antes de enviarla, en estas dimensiones:
- accuracy: ¿lo que dice está respaldado por la base de conocimiento? ¿algo inventado?
- policy: ¿cumple políticas (no promete lo que no se puede, no da datos sensibles)?
- tone: ¿empática y acorde al sentimiento del cliente? ¿voz de marca?
- completeness: ¿responde TODAS las preguntas del cliente?
- safety: ¿riesgos legales/seguridad? ¿debería escalar a humano?
- language: ¿está en el idioma correcto y bien escrita?

`verdict = needs_revision` si hay cualquier issue `high` o varios `medium`. Cada issue
con un `fix` accionable. Es preferible una revisión más que mandar algo flojo.
"""


def critic(state: TicketState) -> dict:
    s = get_settings()
    draft = state.get("draft", {})
    triage = state.get("triage", {})
    knowledge = state.get("knowledge", [])

    user = (
        "RESPUESTA PROPUESTA:\n" + json.dumps(draft, ensure_ascii=False, indent=2)
        + "\n\nTRIAGE:\n" + json.dumps(triage, ensure_ascii=False, indent=2)
        + "\n\nBASE DE CONOCIMIENTO DISPONIBLE:\n" + json.dumps(knowledge, ensure_ascii=False, indent=2)
    )
    review = complete_json(
        system=SYSTEM.format(company=s.company_name),
        user=user,
        schema=REVIEW_SCHEMA,
        model=s.model_critic,
        thinking=True,
    )
    return {
        "review": review,
        "log": [f"critic: {review.get('verdict')} score={review.get('score')} issues={len(review.get('issues', []))}"],
    }
