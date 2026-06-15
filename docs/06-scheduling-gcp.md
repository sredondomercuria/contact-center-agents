# 06 · Scheduling y despliegue en GCP

## Correrlo periódicamente
El soporte se procesa por lotes: cada N minutos se traen los tickets abiertos y se generan
respuestas. Opciones:
- **Cloud Scheduler** (en GCP) → `POST /tasks/run-batch` con token. `deploy/scheduler.sh`.
- **cron** local: `*/15 * * * * cd /ruta && set -a && . ./.env && set +a && .venv/bin/python -m contact_center.run_batch`.
- **Claude Cowork**: programá el prompt de `cowork/PROMPT.md`.

## Deploy a Cloud Run

Infra fija ≈ $0 (escala a cero). El servicio corre el dashboard + el batch.

```bash
gcloud auth login                      # interactivo (browser)
export GCP_PROJECT=supple-framing-498515-a0 REGION=southamerica-east1
export CRM_PROVIDER=zendesk            # o hubspot / generic
bash deploy/push-secrets.sh .env       # secretos -> Secret Manager
bash deploy/deploy.sh                   # build remoto + deploy
export SCHEDULER_TOKEN=$(openssl rand -hex 16); bash deploy/scheduler.sh
```

`deploy.sh` habilita APIs (run, cloudbuild, artifactregistry, secretmanager, scheduler),
deja `USE_GCP_SECRETS=true`, `DRY_RUN=true`, `AGENT_RUNTIME=hybrid` y el `CRM_PROVIDER`.
Los secretos se cargan en runtime (`gcp_secrets.py`); **ninguno viaja en el deploy**.

## Seguridad
- Dashboard `--allow-unauthenticated` pero con **login propio** (`AUTH_PASSWORD`,
  `SESSION_SECRET` por Secret Manager). Candado extra: IAM/IAP.
- `/tasks/run-batch` exige `SCHEDULER_TOKEN`; `/health` abierto.
- Empezá con `DRY_RUN=true`: las respuestas se aprueban a mano antes de tocar el CRM.

## Persistencia en Cloud Run
El FS es efímero: SQLite no persiste entre instancias. Para producción usá **Cloud SQL**
o **Firestore** (la capa `storage.py` está aislada para cambiar el backend).

## Gotchas (de GCP/gcloud)
- `gcloud` necesita Python 3.10+ → `export CLOUDSDK_PYTHON="$(uv python find 3.12)"`.
- Dos credenciales: `gcloud auth login` (deploy/secrets) vs `application-default login` (SDKs).
  Ambas piden reauth interactivo.
- No uses `/healthz` (lo reserva el Google Front End) — el endpoint es `/health`.

## Siguiente
→ [07-cowork.md](07-cowork.md)
