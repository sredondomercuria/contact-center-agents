# 01 · Arquitectura

Equipo multiagente de **soporte**: por cada ticket abierto, clasifica → recupera
conocimiento → redacta → controla calidad → decide auto-responder o escalar → actualiza
el CRM. Con dashboard para que un humano revise y apruebe.

## El modelo mental en 30 segundos

Dos ejes independientes:
- **¿Dónde corre TU código?** local o **GCP Cloud Run** (backend, UI, scheduler, DB).
- **¿Quién corre el LOOP de agentes?** LangGraph (`AGENT_RUNTIME=local`) o **Managed
  Agents** de Anthropic (`AGENT_RUNTIME=hybrid`, default, con fallback a local).

El **modelo Claude** siempre está en Anthropic. Lo único específico del dominio son los
**conectores** (CRM, KB, Slack) y los **criterios de calidad**.

## Stack

| Pieza | Elección |
|-------|----------|
| Orquestación | LangGraph (+ Managed Agents en híbrido) |
| Modelo | Claude `claude-opus-4-8` / `claude-sonnet-4-6` |
| Conocimiento | RAG sobre `knowledge_base/` (keywords; upgradeable a embeddings) |
| CRM / ticketing | **Zendesk · HubSpot · genérico REST** (interfaz común) |
| Escalamiento | Slack (webhook) |
| UI + Backend | FastAPI + HTMX, con login |
| Persistencia | SQLite (local) / Cloud SQL (GCP) |
| Despliegue | GCP Cloud Run + Secret Manager + Cloud Scheduler |

## Diagrama del sistema

```mermaid
flowchart TB
    user["👤 Agente / Navegador"]
    cron["⏰ Cloud Scheduler"]
    subgraph backend["🖥️ TU BACKEND — local o GCP Cloud Run"]
      direction TB
      ui["Dashboard FastAPI + HTMX (login)"]
      lg["LangGraph — run_for_ticket()"]
      act["actions.do_resolve()"]
      db[("SQLite / Cloud SQL")]
    end
    subgraph anthropic["🟣 ANTHROPIC"]
      direction TB
      managed["Managed Agents"]
      claude["Modelo Claude"]
    end
    subgraph ext["🔌 EXTERNOS"]
      direction TB
      crm["CRM (Zendesk/HubSpot/genérico)"]
      kb["Base de conocimiento"]
      slack["Slack"]
    end
    user --> ui --> lg
    cron -->|"POST + token"| lg
    lg -->|"hybrid"| managed --> claude
    lg -->|"local"| claude
    lg -->|"tickets"| crm
    lg -->|"RAG"| kb
    lg --> act
    act -->|"responder/estado"| crm
    act -->|"escalar"| slack
    lg --> db
    ui -.->|"aprueba"| db
```

## Diagrama de agentes

```mermaid
flowchart TB
    START(["▶ Ticket"]) --> PROD
    subgraph PROD["🤖 producer (hybrid: Managed Agent · local: nodos LangGraph)"]
      direction TB
      cls["🏷️ Clasificador · ticket-triage"]
      ret["📚 Recuperador · knowledge-retrieval (RAG)"]
      wr["✍️ Redactor · response-writing"]
      qa["🧐 QA · qa-review"]
      cls --> ret --> wr --> qa
      qa -->|"needs_revision · hasta MAX_REVISIONS"| wr
    end
    PROD --> rt["🔀 Router · escalation-routing"]
    rt --> ex["🚀 Executor · crm-update (+ Slack) · DRY_RUN"]
    ex --> persist[("💾 SQLite")] --> uin(["🖥️ Dashboard — aprobar"])
```

## El estado compartido
`ticket → triage → knowledge → draft ⇄ review → routing → result`. Ver `state.py`.

## El bucle de calidad
El crítico (QA) revisa exactitud, política, tono, completitud, seguridad e idioma; si hay
problemas, **devuelve al redactor** (hasta `MAX_REVISIONS`). Casos sensibles → escalar.

## Siguiente
→ [02-instalacion.md](02-instalacion.md)
