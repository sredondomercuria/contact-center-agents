# 08 · Mejores prácticas

## Diseño
- **Una responsabilidad por agente**; modelo por rol (Opus razonar, Sonnet acotado).
- **Conectores aislados** detrás de una interfaz (`get_crm()`): cambiás de CRM sin tocar agentes.
- **Empezá simple**: la cadena local antes que el híbrido; sumá complejidad cuando rinde.

## Calidad y seguridad del soporte (lo crítico)
- **Cero invención**: la respuesta se funda en la KB; si no alcanza, **escalá** (no inventes).
- **QA adversarial** antes de responder (exactitud/política/tono/completitud/seguridad/idioma)
  con bucle acotado (`MAX_REVISIONS`).
- **Escalamiento obligatorio** en casos sensibles (legal, fraude, datos sensibles, cancelación,
  cliente muy enojado de alta prioridad).
- **Human-in-the-loop**: `DRY_RUN=true` + aprobación en el dashboard antes de tocar al cliente.
- Nunca pedir/guardar datos sensibles (tarjeta completa, etc.).

## API de Claude
- Structured outputs para datos confiables; sin `temperature`/`budget_tokens` en Opus 4.8.
- Razonamiento adaptativo + `effort` en redacción y QA. Prompt caching si reusás prefijos.

## Operación
- Determinismo en el flujo (LangGraph), no en la improvisación.
- Persistí cada corrida (auditoría) y límites explícitos (`recursion_limit`, `MAX_REVISIONS`).
- Secretos en `.env`/Secret Manager; tests sin red ni API key; lockfile + clean-room.

## Costos
- Sonnet para clasificar/recuperar/rutear; Opus sólo redacción/QA.
- Bajá `NUM_TICKETS` y la profundidad de búsqueda si hace falta.
- RAG por keywords es gratis; embeddings agregan costo (mejor calidad).

## Reutilizar el patrón
Este repo nació del **skill-pack constructor** (`~/.claude/skills/`:
`agentic-system-architect`, `langgraph-scaffold`, `connectors`, `quality-loop`,
`managed-agents-hybrid`, `review-dashboard`, `gcp-cloudrun-deploy`). Para otro dominio,
arrancá por `agentic-system-architect`.

## Fin
Volvé al [README](../README.md).
