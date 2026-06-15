---
name: escalation-routing
description: Decidir qué hacer con una respuesta de soporte ya validada — auto-responder al cliente o escalar a un humano — y el nuevo estado del ticket. Usar tras el QA, antes de actualizar el CRM.
---

# Ruteo / escalamiento

## Objetivo
Decidir con criterio si la respuesta se envía sola o la revisa/envía un humano.

## Decisión
- **`auto_reply`**: sólo si QA **aprobó**, la **confianza es alta**, y el caso **no es sensible**.
- **`escalate`**: si hay dudas, baja confianza, QA no aprobó, o el caso es sensible. Indicá `team`.

### Casos que SIEMPRE se escalan
Reclamo legal, fraude/seguridad, cancelación de cuenta/servicio, pedido de datos sensibles,
cambio de email/identidad, cliente muy enojado de prioridad alta/urgente.

## Salida
`{action: auto_reply|escalate, reason, team, new_status: open|pending|solved}`.

## Regla de oro
Ante la duda, **escalá**. Es preferible que un humano lo vea a mandar algo incorrecto.
