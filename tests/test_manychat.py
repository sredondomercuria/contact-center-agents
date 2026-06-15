"""ManyChat: parseo del webhook y construcción del envío (sin red)."""

from __future__ import annotations


def test_payload_to_ticket(monkeypatch):
    from contact_center import services

    t = services.payload_to_ticket(
        {"subscriber_id": "123", "channel": "whatsapp", "message": "Hola, no me llega mi pedido",
         "first_name": "Ana"}
    )
    assert t["id"] == "123"
    assert t["channel"] == "manychat"
    assert t["subchannel"] == "whatsapp"
    assert "pedido" in t["body"]

    # tolera nombres alternativos y rechaza vacíos
    assert services.payload_to_ticket({"contact_id": "9", "last_input_text": "ayuda"})["id"] == "9"
    assert services.payload_to_ticket({"subscriber_id": "9", "message": "  "}) is None
    assert services.payload_to_ticket({}) is None


def test_send_text_payload(monkeypatch):
    from contact_center.config import get_settings

    monkeypatch.setenv("MANYCHAT_API_KEY", "mc-test-key")
    get_settings.cache_clear()

    captured = {}

    class FakeResp:
        def raise_for_status(self):  # noqa: D401
            return None

        def json(self):
            return {"status": "success"}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResp()

    import contact_center.integrations.manychat as mc

    monkeypatch.setattr(mc.requests, "post", fake_post)

    client = mc.ManyChatClient()
    client.send_text("sub-1", "Hola!")

    assert captured["url"].endswith("/fb/sending/sendContent")
    assert captured["headers"]["Authorization"] == "Bearer mc-test-key"
    body = captured["json"]
    assert body["subscriber_id"] == "sub-1"
    assert body["data"]["content"]["messages"][0]["text"] == "Hola!"
    get_settings.cache_clear()
