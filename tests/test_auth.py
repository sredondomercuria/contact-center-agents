"""Login del dashboard: con AUTH activo, todo exige sesión salvo /login y /health."""

from __future__ import annotations


def test_login_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_USERNAME", "admin")
    monkeypatch.setenv("AUTH_PASSWORD", "secret123")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "a.db"))
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("USE_GCP_SECRETS", "false")

    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: None)

    from contact_center.config import get_settings

    get_settings.cache_clear()
    import importlib

    import contact_center.webapp.app as appmod

    importlib.reload(appmod)
    from fastapi.testclient import TestClient

    c = TestClient(appmod.app)

    r = c.get("/", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert c.get("/health").status_code == 200
    assert c.get("/login").status_code == 200

    r = c.post("/login", data={"username": "admin", "password": "mal"}, follow_redirects=False)
    assert r.status_code == 303 and "/login" in r.headers["location"]

    r = c.post("/login", data={"username": "admin", "password": "secret123"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert c.get("/").status_code == 200

    get_settings.cache_clear()
