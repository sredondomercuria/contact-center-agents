# 04 · Agentes y grafo LangGraph

## Nodo = función
Recibe el `TicketState` y devuelve un dict parcial. No muta el estado.

## Acceso a Claude (`llm.py`)
- **`complete_json(...)`**: structured outputs (clasificar, redactar, QA, rutear).
- **`research(...)`**: web (Claude tools o Tavily) — opcional, p. ej. para docs públicas.

Reglas de la API (Opus 4.8/Sonnet 4.6): no enviar `temperature`/`top_p`/`budget_tokens`
(400); usar `thinking={"type":"adaptive"}` + `effort`; `output_config.format`; IDs exactos.

## Modelos por rol (`.env`)
| Agente | Modelo | Por qué |
|--------|--------|---------|
| classifier / retriever / router | Sonnet | tareas acotadas, costo/latencia |
| responder / critic | Opus | redacción y QA exigentes |

## El grafo (`graph.py`)
Se arma según `AGENT_RUNTIME`:
- **hybrid**: `START → producer → router → executor → END` (producer = Managed Agent).
- **local**: `START → classifier → retriever → responder ⇄ critic → router → executor → END`.

```python
g.add_conditional_edges("critic", route_after_review, {"revise": "responder", "approve": "router"})
```
`route_after_review` devuelve `revise` (vuelve al redactor) o `approve`, según el QA y
`MAX_REVISIONS`. El `producer` híbrido tiene **fallback**: si Managed Agents no está, corre
el sub-pipeline local y devuelve lo mismo.

## RAG
El recuperador genera consultas (Claude) y `integrations/knowledge.retrieve()` busca en la
KB. En híbrido, el `producer` recupera la KB **local** y se la pasa al Managed Agent (su
sandbox no tiene tus archivos).

## Extender
Nuevo agente → `agents/x.py`, exportar en `agents/__init__.py`, `add_node` + aristas.

## Siguiente
→ [05-integraciones-crm.md](05-integraciones-crm.md)
