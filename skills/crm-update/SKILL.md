---
name: crm-update
description: Ejecutar la resolución en el CRM/ticketing — responder al cliente o dejar un borrador interno + escalar, y actualizar el estado del ticket. Soporta Zendesk, HubSpot y un cliente REST genérico. Usar como paso final, respetando DRY_RUN.
---

# Actualización del CRM (acción final)

## Objetivo
Llevar la decisión al sistema de tickets real, de forma segura.

## Entradas
Ticket, respuesta (`reply` + `internal_note`) y ruteo (`action`, `new_status`).

## Procedimiento
- **`auto_reply`**: publicar la respuesta al cliente (`add_reply` público), agregar la nota
  interna, y poner el ticket en `pending`/`solved`.
- **`escalate`**: NO responder al cliente; dejar la respuesta como **nota interna/borrador**
  para el humano, poner `open` y **notificar** (Slack) al equipo correspondiente.

## CRM soportados (interfaz común `get_crm()`)
- **Zendesk**: API token; comentarios públicos/privados; status open/pending/solved.
- **HubSpot**: private app token; respuesta como Nota asociada al ticket; `hs_pipeline_stage`.
- **Genérico**: REST configurable (`CRM_GENERIC_BASE_URL`); para cualquier backend propio.

## Reglas
- **`DRY_RUN`** activo → NO tocar el CRM; devolver la previsualización para aprobación humana.
- Manejar errores sin frenar (reportar). Nunca exponer credenciales.
- Verificá el mapeo de estados de tu CRM (en HubSpot, `new_status` es un stage id del pipeline).
