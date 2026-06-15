# 02 · Instalación y primer run

## Requisitos
- **Python 3.10+** (probado en 3.12). Con 3.9 no anda; si no tenés 3.10+, usá `uv`:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh && uv python install 3.12
  ```
- **`ANTHROPIC_API_KEY`** (obligatoria).
- (Para correr de verdad) credenciales del CRM. Para probar **sin CRM**, podés usar la
  base de conocimiento incluida y cargar tickets a mano / mockear `get_crm`.

**Costos** (orden de magnitud): por ticket, varias llamadas a Claude (clasificar, recuperar,
redactar, QA, rutear). Con Sonnet para los pasos livianos y Opus para redacción/QA, ronda
**centavos a ~US$0,30 por ticket** según longitud y revisiones. Sin imágenes (a diferencia
del sistema editorial). `DRY_RUN=true` no toca el CRM.

## Instalar

**Opción A (Python 3.10+):**
```bash
git clone https://github.com/sredondomercuria/contact-center-agents.git
cd contact-center-agents
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,integrations]"
```

**Opción B (uv):** `uv venv --python 3.12 .venv && uv pip install -e ".[dev,integrations]"`
(los venv de uv no traen `pip`: instalá con `uv pip`).

## Configurar
```bash
cp .env.example .env   # ANTHROPIC_API_KEY + CRM (ver 05) + AUTH para el login
```
`DRY_RUN=true` y `AGENT_RUNTIME=hybrid` vienen por defecto.

## Verlo funcionar
```bash
make web        # http://localhost:8080 → "Procesar tickets abiertos"
# o por CLI:
make dry-run    # trae tickets del CRM, genera respuestas y las guarda (no envía nada)
```
Revisás cada respuesta en el dashboard y, cuando estás conforme, **Aprobar y ejecutar**.

## Base de conocimiento
Poné tus artículos `.md` en `knowledge_base/` (hay 3 de ejemplo). El recuperador hace RAG
sobre esa carpeta. Para producción, podés cambiar a embeddings + vector DB (misma interfaz
en `integrations/knowledge.py`).

## Tests
```bash
make test
```

## Híbrido (opcional)
`make agent-setup` crea el Managed Agent en la plataforma de Claude e imprime los IDs para
el `.env`. Si tu cuenta no tiene la beta, cae a `local` automáticamente.

## Troubleshooting
| Síntoma | Solución |
|---|---|
| `make web` no levanta / ModuleNotFound | activá el venv o `pip install -e ".[dev,integrations]"` |
| `gcloud failed... Python 3.9` | usá Python 3.10+ (`uv python install 3.12`) y `CLOUDSDK_PYTHON` |
| Error al traer tickets | revisá `CRM_PROVIDER` y sus credenciales (ver 05) |
| Log `producer: fallback local` | tu cuenta no tiene la beta de Managed Agents (normal) |

## Siguiente
→ [03-skills.md](03-skills.md)
