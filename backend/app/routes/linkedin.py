from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from ..models import LinkedInPublishRequest
from ..config import settings
from ..services.linkedin import (
    build_connect_url,
    complete_oauth_callback,
    disconnect_linkedin,
    get_linkedin_status,
    publish_draft,
)
from ..store import store

router = APIRouter(prefix="/linkedin", tags=["linkedin"])
INVALID_STATE_MESSAGE = "LinkedIn sign-in state is invalid or expired"


@router.get("/connect")
async def linkedin_connect():
    try:
        return RedirectResponse(build_connect_url(store), status_code=302)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/callback")
async def linkedin_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
):
    if error:
        return _settings_redirect(linkedin="error", message=error_description or error)
    if not code or not state:
        return _settings_redirect(linkedin="error", message="LinkedIn callback was missing code or state")
    try:
        complete_oauth_callback(store, code=code, state=state)
    except Exception as exc:
        if str(exc) == INVALID_STATE_MESSAGE and get_linkedin_status(store).connected:
            return _settings_redirect(linkedin="connected")
        return _settings_redirect(linkedin="error", message=str(exc))
    return _settings_redirect(linkedin="connected")


@router.get("/status")
async def linkedin_status() -> dict:
    return get_linkedin_status(store).model_dump(mode="json")


@router.post("/disconnect")
async def linkedin_disconnect() -> dict:
    return disconnect_linkedin(store).model_dump(mode="json")


@router.post("/publish")
async def linkedin_publish(payload: LinkedInPublishRequest) -> dict:
    result = publish_draft(store, payload.draft_id)
    if not result.ok:
        raise HTTPException(status_code=400, detail=result.message)
    return result.model_dump(mode="json")


def _settings_redirect(**params: str) -> HTMLResponse:
    query = urlencode(params)
    separator = "&" if "?" in settings.frontend_url else "?"
    target = f"{settings.frontend_url.rstrip('/')}/settings{separator}{query}"
    is_error = params.get("linkedin") == "error"
    status_text = params.get("message") if is_error else "LinkedIn connected."
    escaped_target = escape(target, quote=True)
    escaped_status = escape(status_text or "Returning to Draftly.", quote=False)
    return HTMLResponse(
        f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="refresh" content="0; url={escaped_target}" />
    <title>Returning to Draftly</title>
    <script>window.location.replace({target!r});</script>
  </head>
  <body>
    <p>{escaped_status} Returning to Draftly...</p>
    <p><a href="{escaped_target}">Continue to Draftly</a></p>
  </body>
</html>"""
    )
