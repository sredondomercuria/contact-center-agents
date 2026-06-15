#!/usr/bin/env bash
# Cloud Scheduler: procesa tickets abiertos cada N minutos (pega a /tasks/run-batch).
set -euo pipefail

PROJECT="${GCP_PROJECT:-supple-framing-498515-a0}"
REGION="${REGION:-southamerica-east1}"
SERVICE="${SERVICE:-contact-center-agents}"
JOB="${JOB:-contact-center-batch}"
SCHED="${SCHED:-*/15 * * * *}"   # cada 15 minutos

gcloud config set project "$PROJECT"
URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')/tasks/run-batch"
TOKEN="${SCHEDULER_TOKEN:?Definí SCHEDULER_TOKEN en el entorno}"

ARGS=(--schedule "$SCHED" --time-zone "America/Argentina/Buenos_Aires"
      --uri "$URL" --http-method POST --headers "X-Scheduler-Token=${TOKEN}" --location "$REGION")

if gcloud scheduler jobs describe "$JOB" --location "$REGION" >/dev/null 2>&1; then
  gcloud scheduler jobs update http "$JOB" "${ARGS[@]}"
else
  gcloud scheduler jobs create http "$JOB" "${ARGS[@]}"
fi
echo "✅ Cloud Scheduler '$JOB' → $URL ($SCHED, hora AR)"
