"""JSON Schemas para structured outputs de Claude."""

from __future__ import annotations


def _obj(properties: dict, required: list[str]) -> dict:
    return {"type": "object", "properties": properties, "required": required,
            "additionalProperties": False}


# --- Clasificador: triage del ticket ---
TRIAGE_SCHEMA = _obj(
    {
        "intent": {"type": "string"},          # p.ej. facturacion, devolucion, bug, consulta...
        "sentiment": {"type": "string", "enum": ["positivo", "neutral", "negativo", "enojado"]},
        "priority": {"type": "string", "enum": ["baja", "media", "alta", "urgente"]},
        "language": {"type": "string"},
        "summary": {"type": "string"},
        "key_questions": {"type": "array", "items": {"type": "string"}},
    },
    ["intent", "sentiment", "priority", "language", "summary", "key_questions"],
)

# --- Recuperador: qué buscar en la KB ---
QUERY_SCHEMA = _obj(
    {"queries": {"type": "array", "items": {"type": "string"}}},
    ["queries"],
)

# --- Redactor: respuesta propuesta ---
RESPONSE_SCHEMA = _obj(
    {
        "reply": {"type": "string"},                 # respuesta al cliente
        "internal_note": {"type": "string"},         # nota interna para el agente humano
        "sources": {"type": "array", "items": {"type": "string"}},   # artículos KB usados
        "confidence": {"type": "integer"},           # 0-100
    },
    ["reply", "internal_note", "sources", "confidence"],
)

# --- Crítico QA ---
REVIEW_SCHEMA = _obj(
    {
        "verdict": {"type": "string", "enum": ["approved", "needs_revision"]},
        "score": {"type": "integer"},
        "issues": {
            "type": "array",
            "items": _obj(
                {
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "type": {
                        "type": "string",
                        "enum": ["accuracy", "policy", "tone", "completeness", "safety", "language"],
                    },
                    "detail": {"type": "string"},
                    "fix": {"type": "string"},
                },
                ["severity", "type", "detail", "fix"],
            ),
        },
        "notes": {"type": "string"},
    },
    ["verdict", "score", "issues", "notes"],
)

# --- Router: qué hacer con la respuesta ---
ROUTING_SCHEMA = _obj(
    {
        "action": {"type": "string", "enum": ["auto_reply", "escalate"]},
        "reason": {"type": "string"},
        "team": {"type": "string"},          # a qué equipo escalar (si aplica)
        "new_status": {"type": "string", "enum": ["open", "pending", "solved"]},
    },
    ["action", "reason", "new_status"],
)
