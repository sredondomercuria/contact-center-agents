"""CRM: el factory elige la implementación correcta y normaliza tickets (sin red)."""

from __future__ import annotations

import pytest


def test_generic_factory_and_norm(monkeypatch):
    from contact_center.config import get_settings

    monkeypatch.setenv("CRM_PROVIDER", "generic")
    monkeypatch.setenv("CRM_GENERIC_BASE_URL", "https://api.example.com")
    get_settings.cache_clear()

    from contact_center.integrations.crm import get_crm
    from contact_center.integrations.crm.generic import GenericCRM

    crm = get_crm()
    assert isinstance(crm, GenericCRM)
    norm = crm._norm({"id": 7, "title": "No puedo entrar", "description": "detalle", "status": "open"})
    assert norm["id"] == "7"
    assert norm["subject"] == "No puedo entrar"
    assert norm["body"] == "detalle"
    get_settings.cache_clear()


def test_generic_requires_base_url(monkeypatch):
    from contact_center.config import get_settings

    monkeypatch.setenv("CRM_PROVIDER", "generic")
    monkeypatch.delenv("CRM_GENERIC_BASE_URL", raising=False)
    get_settings.cache_clear()

    from contact_center.integrations.crm import get_crm

    with pytest.raises(RuntimeError):
        get_crm()
    get_settings.cache_clear()
