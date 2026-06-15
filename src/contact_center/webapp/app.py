"""Dashboard FastAPI + HTMX: cola de respuestas de soporte para revisar y aprobar.

Login por sesión (igual que el sistema editorial). Protege todo salvo /login,
/health y /tasks/run-batch (token propio para el scheduler).
"""

from __future__ import annotations

import hmac
import os
from pathlib import Path

import markdown as _md
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Body, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .. import storage
from ..config import get_settings
from ..gcp_secrets import bootstrap_secrets
from ..services import handle_inbound_message, process_open_tickets, resolve_run, save_draft_edits

load_dotenv()
bootstrap_secrets()
storage.init_db()
Path(get_settings().output_dir).mkdir(parents=True, exist_ok=True)

PUBLIC_PATHS = {"/login", "/health", "/tasks/run-batch", "/webhooks/manychat"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        s = get_settings()
        path = request.url.path
        if not s.auth_enabled or path in PUBLIC_PATHS:
            return await call_next(request)
        if request.session.get("user"):
            return await call_next(request)
        if request.method == "GET":
            return RedirectResponse("/login", status_code=303)
        return JSONResponse({"detail": "login requerido"}, status_code=401)


app = FastAPI(title="Contact Center Agents")
app.add_middleware(AuthMiddleware)
app.add_middleware(SessionMiddleware, secret_key=get_settings().session_secret, same_site="lax", https_only=False)

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
TEMPLATES.env.filters["md"] = lambda t: _md.markdown(t or "", extensions=["extra", "sane_lists"])


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    if not get_settings().auth_enabled or request.session.get("user"):
        return RedirectResponse("/", status_code=303)
    return TEMPLATES.TemplateResponse(request, "login.html", {"error": request.query_params.get("error")})


@app.post("/login")
def login_submit(request: Request, username: str = Form(""), password: str = Form("")):
    s = get_settings()
    if hmac.compare_digest(username, s.auth_username) and hmac.compare_digest(password, s.auth_password):
        request.session["user"] = username
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/login?error=1", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return TEMPLATES.TemplateResponse(
        request, "index.html", {"runs": storage.list_runs(150), "settings": get_settings()}
    )


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: int):
    run = storage.get_run(run_id)
    if not run:
        raise HTTPException(404, "Corrida no encontrada")
    return TEMPLATES.TemplateResponse(request, "run_detail.html", {"run": run, "settings": get_settings()})


@app.post("/runs/{run_id}/edit")
def edit_run(run_id: int, reply: str = Form(""), internal_note: str = Form("")):
    save_draft_edits(run_id, reply=reply, internal_note=internal_note)
    return RedirectResponse(f"/runs/{run_id}", status_code=303)


@app.post("/runs/{run_id}/approve", response_class=HTMLResponse)
def approve(request: Request, run_id: int):
    res = resolve_run(run_id)
    run = storage.get_run(run_id)
    return TEMPLATES.TemplateResponse(
        request, "partials/result.html", {"res": res, "run": run, "settings": get_settings()}
    )


def _kickoff() -> None:
    try:
        process_open_tickets()
    except Exception as exc:  # noqa: BLE001
        print(f"[webapp] error en batch: {exc}")


@app.post("/run")
def trigger_run(background: BackgroundTasks):
    background.add_task(_kickoff)
    return RedirectResponse("/", status_code=303)


@app.post("/tasks/run-batch")
def scheduled_run(background: BackgroundTasks, x_scheduler_token: str = Header(default="")):
    token = get_settings().scheduler_token
    if token and x_scheduler_token != token:
        raise HTTPException(401, "token inválido")
    background.add_task(_kickoff)
    return JSONResponse({"status": "accepted"}, status_code=202)


@app.post("/webhooks/manychat")
def manychat_webhook(
    background: BackgroundTasks,
    payload: dict = Body(default={}),
    x_webhook_token: str = Header(default=""),
):
    """Recibe un mensaje entrante (External Request de un Flow de ManyChat).

    Procesa en segundo plano (la respuesta se envía por la Send API de ManyChat desde el
    executor, respetando DRY_RUN) y responde rápido para no agotar el timeout de ManyChat.
    """
    s = get_settings()
    token = s.manychat_webhook_token or s.scheduler_token
    if token and x_webhook_token != token:
        raise HTTPException(401, "token inválido")
    background.add_task(handle_inbound_message, payload)
    return JSONResponse({"status": "accepted"}, status_code=202)


def run() -> None:
    import uvicorn

    s = get_settings()
    uvicorn.run("contact_center.webapp.app:app", host=s.web_host, port=int(os.environ.get("PORT", s.web_port)))


if __name__ == "__main__":
    run()
