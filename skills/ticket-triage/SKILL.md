---
name: ticket-triage
description: Clasificar un ticket de soporte entrante — intención/tema, sentimiento, prioridad, idioma, resumen y preguntas a responder. Usar al inicio del procesamiento de cada ticket.
---

# Triage de ticket

## Objetivo
Entender el ticket y priorizarlo antes de responder.

## Entradas
Ticket: `{id, subject, body, requester, status}`.

## Procedimiento
1. **Intención/tema**: facturación, devolución, acceso/contraseña, bug, consulta, etc.
2. **Sentimiento**: positivo | neutral | negativo | enojado.
3. **Prioridad**: baja | media | alta | urgente (según urgencia + impacto para el cliente).
4. **Idioma** del cliente.
5. **Resumen** breve y **preguntas concretas** a responder.

## Salida
`{intent, sentiment, priority, language, summary, key_questions[]}`.

## Criterios
- Prioridad `urgente`/`alta` si hay riesgo de pérdida, cliente muy enojado, o impacto grave.
- No resolvés acá; sólo clasificás para el resto del pipeline.
