# 03 · Skills

Cada función del equipo es una **Claude Agent Skill** (carpeta con `SKILL.md`). En
`local` las implementan los nodos LangGraph (`src/contact_center/agents/`); en `hybrid`
el **Managed Agent** las carga como manual operativo. Misma especificación, distinto runtime.

| Skill | Hace | Nodo |
|-------|------|------|
| `ticket-triage` | clasifica (intención, sentimiento, prioridad, idioma) | `classifier` |
| `knowledge-retrieval` | recupera artículos de la KB (RAG) | `retriever` |
| `response-writing` | redacta la respuesta basada en la KB | `responder` |
| `qa-review` | control de calidad adversarial | `critic` |
| `escalation-routing` | auto-responder vs escalar | `router` |
| `crm-update` | ejecuta la acción en el CRM (+ Slack) | `actions.py` |

## Anatomía
```markdown
---
name: qa-review
description: Cuándo usar la skill (una línea — es lo que el modelo lee para decidir).
---
# Instrucciones: Objetivo / Entradas / Procedimiento / Salida / Reglas
```

## Crear/editar
1. Editá el `SKILL.md`. 2. Si cambia el contrato de datos, actualizá el schema en
`schemas.py`. 3. Ajustá el nodo en `agents/`. Para crear/optimizar skills, está la
skill `skill-creator` de Claude.

> Estas son skills de **runtime** (del dominio soporte). Para construir un sistema NUEVO
> como este en otro dominio, está el **skill-pack constructor** (`agentic-system-architect`,
> `langgraph-scaffold`, `connectors`, etc.) en `~/.claude/skills/`.

## Siguiente
→ [04-agentes-langgraph.md](04-agentes-langgraph.md)
