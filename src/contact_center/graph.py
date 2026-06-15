"""Grafo LangGraph del equipo de soporte.

HÍBRIDO (default):  START → producer (Managed Agent) → router → executor → END
LOCAL:              START → classifier → retriever → responder ⇄ critic → router → executor → END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .actions import do_resolve
from .agents import classifier, critic, produce, responder, retriever, router
from .config import get_settings
from .state import TicketState


def route_after_review(state: TicketState) -> str:
    review = state.get("review") or {}
    if review.get("verdict") == "needs_revision" and state.get("revision_count", 0) < get_settings().max_revisions:
        return "revise"
    return "approve"


def executor(state: TicketState) -> dict:
    s = get_settings()
    res = do_resolve(
        ticket=state.get("ticket", {}),
        draft=state.get("draft", {}),
        routing=state.get("routing", {}),
        dry_run=s.dry_run,
    )
    tag = "DRY_RUN" if s.dry_run else (res.get("crm") or "error")
    return {"result": res, "log": [f"executor: {tag}"]}


def build_graph():
    s = get_settings()
    g = StateGraph(TicketState)
    g.add_node("router", router)
    g.add_node("executor", executor)

    if s.agent_runtime == "hybrid":
        g.add_node("producer", produce)
        g.add_edge(START, "producer")
        g.add_edge("producer", "router")
    else:
        g.add_node("classifier", classifier)
        g.add_node("retriever", retriever)
        g.add_node("responder", responder)
        g.add_node("critic", critic)
        g.add_edge(START, "classifier")
        g.add_edge("classifier", "retriever")
        g.add_edge("retriever", "responder")
        g.add_edge("responder", "critic")
        g.add_conditional_edges("critic", route_after_review, {"revise": "responder", "approve": "router"})

    g.add_edge("router", "executor")
    g.add_edge("executor", END)
    return g.compile()
