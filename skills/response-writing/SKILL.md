---
name: response-writing
description: Redactar la respuesta al cliente para un ticket de soporte, fundada en la base de conocimiento, con la voz de marca y el tono adecuado al sentimiento. Usar tras recuperar el conocimiento; reescribir si QA pide cambios.
---

# Redacción de respuesta de soporte

## Objetivo
Una respuesta empática, clara y accionable que resuelva (o avance) el caso, basada SÓLO
en la base de conocimiento.

## Entradas
Ticket, triage y artículos de KB recuperados.

## Procedimiento
1. Saludo acorde al sentimiento; reconocé el problema.
2. Respondé **todas** las preguntas con pasos concretos, citando la política de la KB.
3. Si la KB no alcanza para resolver, **decilo y proponé escalar** — no inventes soluciones,
   políticas ni plazos.
4. Cierre cordial con próximos pasos.
5. Completá `internal_note` (contexto para el humano: qué falta, riesgos, qué confirmar),
   `sources` (artículos usados) y `confidence` (0-100).

## Salida
`{reply, internal_note, sources[], confidence}`.

## Reglas
- Cero invención. Nada de datos sensibles (no pedir tarjeta completa, etc.).
- Voz de marca + idioma del cliente.
- Si QA devolvió issues, corregí **cada** punto.
