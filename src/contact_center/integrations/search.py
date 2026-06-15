"""Backend de búsqueda Tavily (opcional, p.ej. para consultar docs públicas)."""

from __future__ import annotations

from ..config import get_settings


def tavily_search(query: str, *, max_results: int = 8) -> list[dict]:
    s = get_settings()
    if not s.tavily_api_key:
        return []
    try:
        from tavily import TavilyClient
    except ImportError:
        print("[search] falta tavily-python.")
        return []
    try:
        resp = TavilyClient(api_key=s.tavily_api_key).search(
            query=query, max_results=max_results, search_depth="advanced"
        )
        return [{"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
                for r in resp.get("results", [])]
    except Exception as exc:  # noqa: BLE001
        print(f"[search] fallo Tavily: {exc}")
        return []
