# 05 · Integraciones de CRM (real y pluggable)

El sistema lee tickets abiertos del CRM y, tras generar la respuesta, la **ejecuta**
(responder / dejar borrador + escalar / cambiar estado). Todo detrás de una **interfaz
común**, con implementaciones **reales** para Zendesk, HubSpot y un cliente REST genérico.

## Interfaz común (`integrations/crm/base.py`)

```python
class CRMClient(Protocol):
    def list_open_tickets(self, limit=10) -> list[dict]
    def get_ticket(self, ticket_id) -> dict
    def add_reply(self, ticket_id, body, *, public=True) -> dict
    def add_internal_note(self, ticket_id, body) -> dict
    def set_status(self, ticket_id, status) -> dict

def get_crm() -> CRMClient   # elige según CRM_PROVIDER
```
Todas normalizan a `{id, subject, body, requester, status, priority, url}`.
**Para enchufar otro CRM**: escribí una clase con esos métodos y agregala al factory.

## `CRM_PROVIDER=zendesk`
- `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN`.
- Auth: HTTP Basic `{email}/token : {api_token}`.
- `list_open_tickets`: `/search.json?query=type:ticket status<solved`.
- `add_reply`/`add_internal_note`: `PUT /tickets/{id}.json` con `comment.public` true/false.
- `set_status`: open | pending | solved.

## `CRM_PROVIDER=hubspot`
- `HUBSPOT_TOKEN` (Private App).
- Tickets = objetos CRM v3 (`subject`, `content`, `hs_pipeline_stage`, `hs_ticket_priority`).
- Enviar un mensaje al cliente requiere la **Conversations API**; por eso `add_reply`/
  `add_internal_note` dejan el texto como **Nota** asociada al ticket (el humano la envía).
- `set_status` cambia `hs_pipeline_stage` → `new_status` debe ser un **stage id** de tu pipeline.

## `CRM_PROVIDER=generic` (cualquier REST)
- `CRM_GENERIC_BASE_URL` (+ `CRM_GENERIC_TOKEN` Bearer).
- Contrato asumido (ajustable en `integrations/crm/generic.py`):
  ```
  GET    {base}/tickets?status=open&limit=N
  GET    {base}/tickets/{id}
  POST   {base}/tickets/{id}/replies   {body, public}
  POST   {base}/tickets/{id}/notes     {body}
  PATCH  {base}/tickets/{id}           {status}
  ```
- `_norm` mapea campos flexibles (`title`/`subject`, `description`/`content`, etc.).

## La acción final (`actions.do_resolve`)
- `auto_reply` → `add_reply` público + nota interna + `set_status`.
- `escalate` → `add_internal_note` (borrador) + `set_status(open)` + **Slack** al equipo.
- **`DRY_RUN=true`** → no toca el CRM; devuelve la previsualización (la aprobás en el dashboard).
- Errores por paso se reportan sin frenar.

## Escalamiento (Slack)
`SLACK_WEBHOOK_URL` (Incoming Webhook). Se notifica en `escalate` con ticket, equipo y motivo.

## Siguiente
→ [06-scheduling-gcp.md](06-scheduling-gcp.md)
