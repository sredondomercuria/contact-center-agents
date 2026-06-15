"""Cliente de ManyChat — capa omnicanal (WhatsApp, Instagram, Facebook Messenger,
TikTok, Telegram). El subscriber es agnóstico del canal; ManyChat enruta al canal
por el que llegó el contacto.

Auth: `Authorization: Bearer <MANYCHAT_API_KEY>`.
Docs/API: https://api.manychat.com/swagger

Envío de respuesta dentro de la ventana de servicio (el cliente acaba de escribir):
  POST /fb/sending/sendContent  {subscriber_id, data:{version:"v2", content:{messages:[...]}}}

Nota WhatsApp: para mensajes *iniciados por el negocio* fuera de la ventana de 24 h hay
que usar `sendFlow` con una plantilla aprobada (ver `send_flow`). Como acá respondemos a
un mensaje entrante, `sendContent` (texto) funciona.
"""

from __future__ import annotations

import requests

from ..config import get_settings

API = "https://api.manychat.com"


class ManyChatClient:
    def __init__(self, timeout: int = 30):
        s = get_settings()
        if not s.manychat_api_key:
            raise RuntimeError("Falta MANYCHAT_API_KEY.")
        self.h = {"Authorization": f"Bearer {s.manychat_api_key}", "Content-Type": "application/json"}
        self.timeout = timeout

    def send_text(self, subscriber_id: str, text: str, *, message_tag: str | None = None) -> dict:
        body: dict = {
            "subscriber_id": subscriber_id,
            "data": {"version": "v2", "content": {"messages": [{"type": "text", "text": text}]}},
        }
        if message_tag:
            body["message_tag"] = message_tag
        r = requests.post(f"{API}/fb/sending/sendContent", headers=self.h, json=body, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def send_flow(self, subscriber_id: str, flow_ns: str) -> dict:
        """Dispara un Flow (p.ej. plantilla de WhatsApp para mensajes fuera de la ventana de 24h)."""
        r = requests.post(
            f"{API}/fb/sending/sendFlow", headers=self.h,
            json={"subscriber_id": subscriber_id, "flow_ns": flow_ns}, timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def add_tag(self, subscriber_id: str, tag_name: str) -> dict:
        r = requests.post(
            f"{API}/fb/subscriber/addTagByName", headers=self.h,
            json={"subscriber_id": subscriber_id, "tag_name": tag_name}, timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def get_subscriber(self, subscriber_id: str) -> dict:
        r = requests.get(
            f"{API}/fb/subscriber/getInfo", headers=self.h,
            params={"subscriber_id": subscriber_id}, timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()
