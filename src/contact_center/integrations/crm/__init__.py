"""Capa CRM pluggable. `get_crm()` devuelve el cliente según CRM_PROVIDER."""

from .base import CRMClient, get_crm

__all__ = ["CRMClient", "get_crm"]
