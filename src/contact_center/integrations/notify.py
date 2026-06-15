"""Notificación a un agente humano vía Slack (Incoming Webhook)."""

from __future__ import annotations

import requests

from ..config import get_settings


def notify_slack(text: str, *, timeout: int = 15) -> bool:
    url = get_settings().slack_webhook_url
    if not url:
        return False
    try:
        r = requests.post(url, json={"text": text}, timeout=timeout)
        r.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] fallo Slack: {exc}")
        return False
