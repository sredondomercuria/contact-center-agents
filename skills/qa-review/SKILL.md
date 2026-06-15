---
name: qa-review
description: Control de calidad adversarial de una respuesta de soporte antes de enviarla — exactitud, política, tono, completitud, seguridad e idioma. Puede devolver la respuesta a redacción. Usar siempre antes de resolver.
---

# QA de la respuesta

## Objetivo
Última línea de defensa antes de responderle al cliente. Buscás el error.

## Dimensiones
- **accuracy**: ¿todo está respaldado por la KB? ¿algo inventado o mal?
- **policy**: ¿cumple políticas? ¿promete algo que no se puede? ¿pide datos sensibles?
- **tone**: ¿empática y acorde al sentimiento? ¿voz de marca?
- **completeness**: ¿responde TODAS las preguntas del cliente?
- **safety**: ¿riesgo legal/seguridad? ¿debería escalar?
- **language**: ¿idioma correcto y bien escrita?

## Salida
`{verdict, score, issues:[{severity,type,detail,fix}], notes}`.

## Reglas
- `needs_revision` ante cualquier issue `high` o varios `medium`.
- Cada issue con un `fix` accionable.
- Bucle acotado (`MAX_REVISIONS`); si se agota, escalá a humano en vez de auto-responder.
