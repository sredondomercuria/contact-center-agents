"""Smoke: config, armado del grafo (hybrid/local), ruteo. Sin red ni API key."""

from __future__ import annotations

import pytest


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("DRY_RUN", raising=False)
    from contact_center.config import Settings

    s = Settings(_env_file=None)
    assert s.dry_run is True
    assert s.agent_runtime == "hybrid"
    assert s.crm_provider == "generic"
    assert s.model_responder == "claude-opus-4-8"


def test_graph_hybrid():
    pytest.importorskip("langgraph")
    from contact_center.graph import build_graph

    nodes = set(build_graph().get_graph().nodes)
    for n in ("producer", "router", "executor"):
        assert n in nodes


def test_graph_local(monkeypatch):
    pytest.importorskip("langgraph")
    from contact_center import graph

    class S:
        agent_runtime = "local"
        max_revisions = 2

    monkeypatch.setattr(graph, "get_settings", lambda: S())
    nodes = set(graph.build_graph().get_graph().nodes)
    for n in ("classifier", "retriever", "responder", "critic", "router", "executor"):
        assert n in nodes


def test_routing(monkeypatch):
    from contact_center import graph

    monkeypatch.setattr(graph, "get_settings", lambda: type("S", (), {"max_revisions": 2})())
    assert graph.route_after_review({"review": {"verdict": "approved"}, "revision_count": 1}) == "approve"
    assert graph.route_after_review({"review": {"verdict": "needs_revision"}, "revision_count": 0}) == "revise"
    assert graph.route_after_review({"review": {"verdict": "needs_revision"}, "revision_count": 2}) == "approve"
