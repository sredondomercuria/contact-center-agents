"""Productor (runtime híbrido): resuelve el ticket (clasificar→recuperar→redactar→QA).

hybrid → Managed Agent en la plataforma de Claude (con la KB recuperada localmente).
local  → sub-pipeline de nodos LangGraph (classifier→retriever→responder⇄critic).
Devuelve las mismas claves para que el resto del grafo (router→executor) no cambie.
"""

from __future__ import annotations

from ..config import get_settings
from ..integrations.knowledge import retrieve
from ..integrations.managed_agents import run_support_agent
from ..state import TicketState


def produce(state: TicketState) -> dict:
    s = get_settings()
    ticket = state.get("ticket", {})

    # La KB vive en tu repo: la recuperamos local y se la pasamos al Managed Agent.
    kb = retrieve([f"{ticket.get('subject','')} {ticket.get('body','')}"], k=3)
    result = run_support_agent(ticket=ticket, kb_snippets=kb)
    if result and result.get("draft"):
        return {
            "triage": result.get("triage", {}),
            "knowledge": result.get("knowledge", kb),
            "draft": result.get("draft", {}),
            "review": result.get("review", {}),
            "revision_count": 1,
            "log": ["producer: resuelto por Managed Agent (plataforma Claude)"],
        }
    return _produce_local(state)


def _produce_local(state: TicketState) -> dict:
    from .classifier import classifier
    from .critic import critic
    from .responder import responder
    from .retriever import retriever

    s = get_settings()
    work: dict = dict(state)
    logs: list[str] = []
    for node in (classifier, retriever):
        out = node(work)
        logs += out.pop("log", [])
        work.update(out)

    work["revision_count"] = 0
    while True:
        for node in (responder, critic):
            out = node(work)
            logs += out.pop("log", [])
            work.update(out)
        review = work.get("review", {})
        if review.get("verdict") == "needs_revision" and work.get("revision_count", 0) < s.max_revisions:
            continue
        break

    return {
        "triage": work.get("triage", {}),
        "knowledge": work.get("knowledge", []),
        "draft": work.get("draft", {}),
        "review": work.get("review", {}),
        "revision_count": work.get("revision_count", 1),
        "log": logs + ["producer: fallback local"],
    }
