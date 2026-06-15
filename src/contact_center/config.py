"""Configuración central (pydantic-settings, lee .env)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Claude ---
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # --- Runtime de agentes ---
    agent_runtime: str = Field(default="hybrid", alias="AGENT_RUNTIME")  # hybrid | local
    managed_agent_id: str = Field(default="", alias="MANAGED_AGENT_ID")
    managed_env_id: str = Field(default="", alias="MANAGED_ENV_ID")

    # --- Modelos por agente ---
    model_classifier: str = Field(default="claude-sonnet-4-6", alias="MODEL_CLASSIFIER")
    model_retriever: str = Field(default="claude-sonnet-4-6", alias="MODEL_RETRIEVER")
    model_responder: str = Field(default="claude-opus-4-8", alias="MODEL_RESPONDER")
    model_critic: str = Field(default="claude-opus-4-8", alias="MODEL_CRITIC")
    model_router: str = Field(default="claude-sonnet-4-6", alias="MODEL_ROUTER")

    # --- Política de soporte ---
    company_name: str = Field(default="Mi Empresa", alias="COMPANY_NAME")
    support_language: str = Field(default="es", alias="SUPPORT_LANGUAGE")
    brand_voice: str = Field(default="cordial, claro y resolutivo", alias="BRAND_VOICE")
    max_revisions: int = Field(default=2, alias="MAX_REVISIONS")
    num_tickets: int = Field(default=10, alias="NUM_TICKETS")

    # --- Conocimiento (RAG) ---
    knowledge_dir: str = Field(default="knowledge_base", alias="KNOWLEDGE_DIR")

    # --- Investigación opcional ---
    research_backend: str = Field(default="claude", alias="RESEARCH_BACKEND")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    # --- CRM ---
    crm_provider: str = Field(default="generic", alias="CRM_PROVIDER")  # generic|zendesk|hubspot
    crm_generic_base_url: str = Field(default="", alias="CRM_GENERIC_BASE_URL")
    crm_generic_token: str = Field(default="", alias="CRM_GENERIC_TOKEN")
    zendesk_subdomain: str = Field(default="", alias="ZENDESK_SUBDOMAIN")
    zendesk_email: str = Field(default="", alias="ZENDESK_EMAIL")
    zendesk_api_token: str = Field(default="", alias="ZENDESK_API_TOKEN")
    hubspot_token: str = Field(default="", alias="HUBSPOT_TOKEN")

    # --- Notificaciones ---
    slack_webhook_url: str = Field(default="", alias="SLACK_WEBHOOK_URL")

    # --- Persistencia ---
    database_path: str = Field(default="output/contact_center.db", alias="DATABASE_PATH")

    # --- Webapp ---
    web_host: str = Field(default="0.0.0.0", alias="WEB_HOST")
    web_port: int = Field(default=8080, alias="PORT")
    scheduler_token: str = Field(default="", alias="SCHEDULER_TOKEN")

    # --- Login ---
    auth_username: str = Field(default="admin", alias="AUTH_USERNAME")
    auth_password: str = Field(default="", alias="AUTH_PASSWORD")
    session_secret: str = Field(default="dev-insecure-change-me", alias="SESSION_SECRET")

    # --- GCP ---
    use_gcp_secrets: bool = Field(default=False, alias="USE_GCP_SECRETS")
    gcp_project: str = Field(default="", alias="GCP_PROJECT")

    # --- Ejecución ---
    dry_run: bool = Field(default=True, alias="DRY_RUN")
    output_dir: str = Field(default="output", alias="OUTPUT_DIR")

    @property
    def auth_enabled(self) -> bool:
        return bool(self.auth_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()
