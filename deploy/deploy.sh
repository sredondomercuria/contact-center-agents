#!/usr/bin/env bash
# Deploy del dashboard a Cloud Run desde el código fuente (usa el Dockerfile).
set -euo pipefail

PROJECT="${GCP_PROJECT:-supple-framing-498515-a0}"
REGION="${REGION:-southamerica-east1}"
SERVICE="${SERVICE:-contact-center-agents}"
CRM="${CRM_PROVIDER:-generic}"

echo "▶ Proyecto: $PROJECT · Región: $REGION · Servicio: $SERVICE · CRM: $CRM"
gcloud config set project "$PROJECT"

echo "▶ Habilitando APIs..."
gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com cloudscheduler.googleapis.com

echo "▶ Deploy a Cloud Run..."
gcloud run deploy "$SERVICE" \
  --source . --region "$REGION" --allow-unauthenticated \
  --memory 1Gi --cpu 1 --timeout 900 \
  --set-env-vars "USE_GCP_SECRETS=true,GCP_PROJECT=${PROJECT},AGENT_RUNTIME=hybrid,DRY_RUN=true,RESEARCH_BACKEND=claude,CRM_PROVIDER=${CRM}"

echo "✅ URL:"
gcloud run services describe "$SERVICE" --region "$REGION" --format="value(status.url)"
echo "Recordá: dashboard público (--allow-unauthenticated) pero con login propio (AUTH_PASSWORD)."
