"""Capa de acceso a Claude: structured outputs + investigación web opcional."""

from __future__ import annotations

import json
from typing import Any

import anthropic

from .config import get_settings

WEB_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search"},
    {"type": "web_fetch_20260209", "name": "web_fetch"},
]


def get_client() -> anthropic.Anthropic:
    s = get_settings()
    return anthropic.Anthropic(api_key=s.anthropic_api_key) if s.anthropic_api_key else anthropic.Anthropic()


def _first_text(content: list[Any]) -> str:
    return "".join(b.text for b in content if getattr(b, "type", None) == "text")


def complete_json(
    *, system: str, user: str, schema: dict, model: str,
    max_tokens: int = 6000, effort: str = "high", thinking: bool = False,
) -> dict:
    """Respuesta de Claude que cumple `schema` (structured outputs)."""
    client = get_client()
    kwargs: dict[str, Any] = {
        "model": model, "max_tokens": max_tokens, "system": system,
        "messages": [{"role": "user", "content": user}],
        "output_config": {"format": {"type": "json_schema", "schema": schema}, "effort": effort},
    }
    if thinking:
        kwargs["thinking"] = {"type": "adaptive"}
    resp = client.messages.create(**kwargs)
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"Claude rechazó: {resp.stop_details}")
    return json.loads(_first_text(resp.content))


def research(*, system: str, user: str, model: str, max_tokens: int = 6000, max_uses: int = 6) -> str:
    """Investiga en la web (Claude web tools o Tavily). Devuelve texto con citas."""
    s = get_settings()
    if s.research_backend == "tavily":
        from .integrations.search import tavily_search

        results = tavily_search(user, max_results=8)
        if not results:
            return "(sin resultados)"
        client = get_client()
        ctx = json.dumps(results, ensure_ascii=False, indent=2)
        resp = client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": f"{user}\n\nResultados:\n{ctx}"}],
        )
        return _first_text(resp.content)

    client = get_client()
    tools = [{**t, "max_uses": max_uses} for t in WEB_TOOLS]
    messages: list[dict[str, Any]] = [{"role": "user", "content": user}]
    resp = None
    for _ in range(6):
        resp = client.messages.create(model=model, max_tokens=max_tokens, system=system,
                                      messages=messages, tools=tools)
        if resp.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue
        break
    assert resp is not None
    return _first_text(resp.content)
