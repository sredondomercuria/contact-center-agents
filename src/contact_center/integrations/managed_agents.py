"""Managed Agents — runtime híbrido para resolver un ticket en la plataforma de Claude.

El agente (con las skills de soporte como manual) clasifica → recupera → redacta →
revalida un ticket y devuelve el resultado estructurado. Fallback a `None` si no está
disponible (el grafo usa entonces el sub-pipeline local).

Setup (una vez):  python -m contact_center.integrations.managed_agents setup
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from ..config import get_settings
from ..llm import get_client

AGENT_NAME = "equipo-soporte-contact-center"
ENV_NAME = "contact-center-env"
SKILL_FILES = ["ticket-triage", "knowledge-retrieval", "response-writing", "qa-review"]

OUTPUT_CONTRACT = """\
Al terminar, devolvé EXCLUSIVAMENTE un bloque ```json con este shape (sin texto extra):
{
  "triage":   {"intent","sentiment","priority","language","summary","key_questions":[...]},
  "knowledge":[{"title","snippet"}],
  "draft":    {"reply","internal_note","sources":[...],"confidence"},
  "review":   {"verdict","score","issues":[{"severity","type","detail","fix"}],"notes"}
}
sentiment ∈ positivo|neutral|negativo|enojado · priority ∈ baja|media|alta|urgente ·
verdict ∈ approved|needs_revision
"""


def _skills_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "skills"


def _load_skill(name: str) -> str:
    try:
        return (_skills_dir() / name / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return ""


def _system_prompt() -> str:
    s = get_settings()
    manual = "\n\n---\n\n".join(_load_skill(n) for n in SKILL_FILES if _load_skill(n))
    return (
        f"Sos un agente de soporte senior de {s.company_name}. Voz de marca: {s.brand_voice}. "
        f"Idioma: {s.support_language}. Seguís estas SKILLS al pie de la letra.\n\n"
        f"REGLAS: no inventes políticas ni datos; basá la respuesta en la base de conocimiento; "
        f"si no hay info suficiente o el caso es sensible, marcá para escalar; tono empático y resolutivo.\n\n"
        f"===== SKILLS =====\n{manual}\n"
    )


def ensure_environment(client) -> str:
    s = get_settings()
    if s.managed_env_id:
        return s.managed_env_id
    for env in client.beta.environments.list():
        if getattr(env, "name", None) == ENV_NAME:
            return env.id
    return client.beta.environments.create(
        name=ENV_NAME, config={"type": "cloud", "networking": {"type": "unrestricted"}}
    ).id


def ensure_agent(client) -> str:
    s = get_settings()
    if s.managed_agent_id:
        return s.managed_agent_id
    for agent in client.beta.agents.list():
        if getattr(agent, "name", None) == AGENT_NAME:
            return agent.id
    return client.beta.agents.create(
        name=AGENT_NAME, model=s.model_responder, system=_system_prompt(),
        tools=[{"type": "agent_toolset_20260401"}],
    ).id


def _extract_json(text: str) -> dict | None:
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    blob = m.group(1) if m else None
    if blob is None:
        i, j = text.find("{"), text.rfind("}")
        blob = text[i : j + 1] if i != -1 and j != -1 else None
    try:
        return json.loads(blob) if blob else None
    except json.JSONDecodeError:
        return None


def run_support_agent(*, ticket: dict, kb_snippets: list[dict]) -> dict | None:
    """Resuelve un ticket como Managed Agent. Devuelve dict o None (fallback local)."""
    try:
        client = get_client()
        env_id = ensure_environment(client)
        agent_id = ensure_agent(client)
        session = client.beta.sessions.create(
            agent=agent_id, environment_id=env_id, title=f"Ticket {ticket.get('id')}"
        )
        task = (
            "Resolvé este ticket de soporte siguiendo tus skills (clasificá, usá la base de "
            "conocimiento provista, redactá la respuesta y hacé QA).\n\n"
            f"TICKET:\n{json.dumps(ticket, ensure_ascii=False, indent=2)}\n\n"
            f"BASE DE CONOCIMIENTO (usá sólo esto):\n{json.dumps(kb_snippets, ensure_ascii=False, indent=2)}\n\n"
            f"{OUTPUT_CONTRACT}"
        )
        final = ""
        with client.beta.sessions.events.stream(session_id=session.id) as stream:
            client.beta.sessions.events.send(
                session_id=session.id,
                events=[{"type": "user.message", "content": [{"type": "text", "text": task}]}],
            )
            for ev in stream:
                et = getattr(ev, "type", "")
                if et == "agent.message":
                    final += "".join(b.text for b in ev.content if getattr(b, "type", None) == "text")
                elif et == "session.status_idle":
                    if getattr(getattr(ev, "stop_reason", None), "type", None) == "requires_action":
                        continue
                    break
                elif et == "session.status_terminated":
                    break
        data = _extract_json(final)
        if not data or "draft" not in data:
            print("[managed_agents] salida no parseable; fallback local.")
            return None
        return data
    except Exception as exc:  # noqa: BLE001
        print(f"[managed_agents] no disponible ({exc}); fallback local.")
        return None


def setup() -> int:
    client = get_client()
    print("Creando/obteniendo environment y agent en la plataforma de Claude...")
    env_id, agent_id = ensure_environment(client), ensure_agent(client)
    print("\n✅ Agregá esto a tu .env:\n")
    print(f"MANAGED_ENV_ID={env_id}")
    print(f"MANAGED_AGENT_ID={agent_id}")
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        return setup()
    print("Uso: python -m contact_center.integrations.managed_agents setup")
    return 0


if __name__ == "__main__":
    sys.exit(main())
