---
name: knowledge-retrieval
description: Recuperar de la base de conocimiento los artículos relevantes para resolver un ticket (RAG). Usar después del triage y antes de redactar, para fundamentar la respuesta en información real.
---

# Recuperación de conocimiento (RAG)

## Objetivo
Traer los artículos de la KB que permiten responder con datos reales (no inventados).

## Procedimiento
1. Generá 2-4 **consultas** cortas y específicas a partir del ticket y el triage.
2. Buscá en la base de conocimiento (`knowledge_base/`) y traé los **top-k** artículos
   con su título y un snippet relevante.
3. Si no hay artículos pertinentes, devolvé vacío (la respuesta deberá escalar, no inventar).

## Salida
`[{title, snippet, source}]` — lo que el redactor usará como única fuente.

## Notas
- Implementación base: ranking por coincidencia de términos sobre `.md`. Para producción,
  embeddings + vector DB (pgvector/AgentDB) — misma interfaz.
- La respuesta SIEMPRE se basa en lo recuperado; si la KB no alcanza, se escala.
