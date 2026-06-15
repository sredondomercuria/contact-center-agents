"""Recuperación de conocimiento (RAG simple) sobre una carpeta de artículos .md.

Implementación real sin dependencias extra: ranking por coincidencia de términos.
Para producción, reemplazá por embeddings + vector DB (pgvector, AgentDB, etc.) —
la interfaz `retrieve(queries) -> [{title, path, snippet, score}]` no cambia.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import get_settings

_WORD = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text) if len(w) > 2]


def _snippet(text: str, terms: set[str], width: int = 400) -> str:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    best, best_score = "", -1
    for p in paras:
        score = sum(1 for w in _tokens(p) if w in terms)
        if score > best_score:
            best, best_score = p, score
    return (best or text)[:width]


def retrieve(queries: list[str], k: int = 2, *, rel_threshold: float = 0.4) -> list[dict]:
    """Top-k artículos relevantes. Descarta matches débiles con un umbral relativo al mejor."""
    kb_dir = Path(get_settings().knowledge_dir)
    if not kb_dir.exists():
        return []
    terms: set[str] = set()
    for q in queries:
        terms.update(_tokens(q))
    if not terms:
        return []

    scored = []
    for path in kb_dir.glob("**/*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        doc_tokens = _tokens(text)
        if not doc_tokens:
            continue
        score = sum(doc_tokens.count(t) for t in terms)
        if score > 0:
            title = next((ln.lstrip("# ").strip() for ln in text.splitlines() if ln.strip()), path.stem)
            scored.append({"title": title, "path": str(path), "snippet": _snippet(text, terms), "score": score})

    scored.sort(key=lambda d: d["score"], reverse=True)
    if not scored:
        return []
    # Umbral: descarta artículos cuyo score es muy bajo respecto del mejor (ruido).
    cutoff = max(2, scored[0]["score"] * rel_threshold)
    return [d for d in scored if d["score"] >= cutoff][:k]
