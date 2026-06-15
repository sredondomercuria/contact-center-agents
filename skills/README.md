# Skills del equipo de soporte

Cada carpeta es una **Claude Agent Skill** (capacidad reutilizable con su `SKILL.md`).
El workflow las usa: en `local` las implementan los nodos LangGraph (`src/contact_center/agents/`);
en `hybrid` las carga el **Managed Agent** como manual operativo.

| Skill | Rol | Nodo |
|-------|-----|------|
| [`ticket-triage`](ticket-triage/SKILL.md) | clasificar el ticket | `classifier` |
| [`knowledge-retrieval`](knowledge-retrieval/SKILL.md) | buscar en la base de conocimiento | `retriever` |
| [`response-writing`](response-writing/SKILL.md) | redactar la respuesta | `responder` |
| [`qa-review`](qa-review/SKILL.md) | control de calidad de la respuesta | `critic` |
| [`escalation-routing`](escalation-routing/SKILL.md) | auto-responder vs escalar | `router` |
| [`crm-update`](crm-update/SKILL.md) | ejecutar la acción en el CRM | `actions.py` |
