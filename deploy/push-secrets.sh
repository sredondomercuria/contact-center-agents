#!/usr/bin/env bash
# Sube los secretos del .env local a GCP Secret Manager + acceso a la SA de Cloud Run.
set -euo pipefail

PROJECT="${GCP_PROJECT:-supple-framing-498515-a0}"
ENV_FILE="${1:-.env}"
gcloud config set project "$PROJECT"

KEYS=(
  ANTHROPIC_API_KEY TAVILY_API_KEY
  CRM_GENERIC_BASE_URL CRM_GENERIC_TOKEN
  ZENDESK_SUBDOMAIN ZENDESK_EMAIL ZENDESK_API_TOKEN
  HUBSPOT_TOKEN SLACK_WEBHOOK_URL
  SCHEDULER_TOKEN AUTH_PASSWORD SESSION_SECRET
)

# Leer del .env SIN sourcear (robusto ante valores con espacios).
get_env() { grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2-; }

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for KEY in "${KEYS[@]}"; do
  VALUE="$(get_env "$KEY")"
  [ -z "$VALUE" ] && { echo "· $KEY vacío, salteado"; continue; }
  if gcloud secrets describe "$KEY" >/dev/null 2>&1; then
    printf '%s' "$VALUE" | gcloud secrets versions add "$KEY" --data-file=- >/dev/null
    echo "· $KEY actualizado"
  else
    printf '%s' "$VALUE" | gcloud secrets create "$KEY" --data-file=- --replication-policy=automatic >/dev/null
    echo "· $KEY creado"
  fi
  gcloud secrets add-iam-policy-binding "$KEY" \
    --member="serviceAccount:${RUN_SA}" --role="roles/secretmanager.secretAccessor" >/dev/null 2>&1 || true
done
echo "✅ Secretos en Secret Manager. SA: $RUN_SA"
