"""Carga de secretos desde GCP Secret Manager (si USE_GCP_SECRETS=true)."""

from __future__ import annotations

import os

SECRET_KEYS = [
    "ANTHROPIC_API_KEY", "TAVILY_API_KEY",
    "CRM_GENERIC_BASE_URL", "CRM_GENERIC_TOKEN",
    "ZENDESK_SUBDOMAIN", "ZENDESK_EMAIL", "ZENDESK_API_TOKEN",
    "HUBSPOT_TOKEN", "SLACK_WEBHOOK_URL",
    "MANYCHAT_API_KEY", "MANYCHAT_WEBHOOK_TOKEN",
    "SCHEDULER_TOKEN", "AUTH_PASSWORD", "SESSION_SECRET",
]


def bootstrap_secrets() -> None:
    if os.environ.get("USE_GCP_SECRETS", "").lower() not in ("1", "true", "yes"):
        return
    project = os.environ.get("GCP_PROJECT", "")
    if not project:
        print("[secrets] USE_GCP_SECRETS=true pero falta GCP_PROJECT.")
        return
    try:
        from google.cloud import secretmanager
    except ImportError:
        print("[secrets] falta google-cloud-secret-manager.")
        return
    client = secretmanager.SecretManagerServiceClient()
    loaded = []
    for key in SECRET_KEYS:
        name = f"projects/{project}/secrets/{key}/versions/latest"
        try:
            resp = client.access_secret_version(name=name)
            os.environ[key] = resp.payload.data.decode("utf-8")
            loaded.append(key)
        except Exception:  # noqa: BLE001
            continue
    if loaded:
        print(f"[secrets] cargados: {', '.join(loaded)}")
