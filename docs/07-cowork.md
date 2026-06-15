# 07 · Correr el equipo en Claude Cowork

El mismo equipo se puede correr como **agente autónomo** en Claude Cowork (en vez del
workflow programático LangGraph). Comparten las **skills**.

## Pasos
1. Instalá las carpetas de `skills/` en tu agente de Cowork.
2. Cargá el prompt de [`cowork/PROMPT.md`](../cowork/PROMPT.md) (rol, objetivo, workflow de
   6 pasos: triage → KB → redactar → QA → rutear → CRM).
3. Configurá las credenciales (CRM, Slack) como secretos del agente — **no en el chat**.
4. Programá el prompt para correr cada N minutos sobre los tickets abiertos.

## Cowork vs Managed Agents
- **Cowork**: lo manejás vos en la UI de Claude (interactivo / programado).
- **Managed Agents** (runtime `hybrid`): lo maneja tu **código** (sessions desde el backend).
  En este repo `hybrid` ya usa Managed Agents para el `producer`. Ver [04](04-agentes-langgraph.md).

## Reglas (en ambos)
Cero invención (la respuesta se basa en la KB); casos sensibles → escalar; `DRY_RUN` para
aprobación humana; nunca exponer credenciales.

## Siguiente
→ [08-mejores-practicas.md](08-mejores-practicas.md)
