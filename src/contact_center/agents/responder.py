"""Redactor de respuesta. Skill: skills/response-writing."""

from __future__ import annotations

import json
from datetime import date

from ..config import get_settings
from ..integrations import agenda
from ..llm import complete_json, complete_with_tools
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

AGENDA_SYSTEM = """\
Sos {company}, asistente de atención al cliente. Respondés en {lang}, con voz de marca: {voice}.
Hoy es {today}. Sedes con agenda: {sedes}.

Tenés una AGENDA REAL con dos herramientas:
- `check_availability`: horarios de turno LIBRES de una sede. Usala SIEMPRE antes de ofrecer
  horarios; NUNCA inventes disponibilidad ni digas "déjame chequear con el equipo".
- `book_appointment`: reserva el turno. Usala SOLO cuando el cliente eligió un horario ofrecido
  y ya tenés su nombre.

Cómo trabajar:
- Si el cliente quiere un turno o pregunta disponibilidad: pedí la sede si falta, consultá la
  agenda y ofrecé 2-3 opciones reales y concretas.
- Cuando el cliente confirme un horario y tengas su nombre, reservá y confirmá con fecha, hora y sede.
- Si reservaste con éxito, `confidence` alta. Si falta info para reservar (sede o nombre), pedila.
- Para preguntas que no son de turnos, respondé con la base de conocimiento como siempre.

Reglas generales:
- Basate en la base de conocimiento; no inventes precios ni políticas.
- `internal_note`: qué pasó (turno reservado / qué falta). `sources`: artículos KB usados. `confidence`: 0-100.
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

    if s.agenda_enabled:
        draft, trace = complete_with_tools(
            system=AGENDA_SYSTEM.format(
                company=s.company_name, lang=s.support_language, voice=s.brand_voice,
                today=date.today().isoformat(), sedes=", ".join(s.agenda_sede_list),
            ),
            user=user,
            tools=agenda.TOOLS,
            handlers={t["name"]: (lambda inp, _n=t["name"]: agenda.dispatch(_n, inp)) for t in agenda.TOOLS},
            schema=RESPONSE_SCHEMA,
            model=s.model_responder,
        )
        booked = any(t["tool"] == "book_appointment" and t["output"].get("ok") for t in trace)
        tools_used = ", ".join(t["tool"] for t in trace) or "ninguna"
        return {
            "draft": draft,
            "agenda_trace": trace,
            "revision_count": revision_count + 1,
            "log": [f"responder(agenda): tools=[{tools_used}] reservó={booked} (confianza {draft.get('confidence')})"],
        }

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
