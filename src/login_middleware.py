from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import RedirectResponse

from database import get_session
from models import User
from password_utils import verify_password


class LoginFormMiddleware:
    """Handles POST /login and POST /logout as plain HTTP request/response
    cycles, deliberately outside PyWire's interactive WebSocket protocol.

    This must run inside SessionMiddleware (which wraps it — see
    auth_middleware_stack()) so scope["session"] is a real Starlette Session
    and the redirect response below triggers a genuine http.response.start
    message. That's what lets SessionMiddleware attach a true httponly
    Set-Cookie header itself. A PyWire interactive @click handler never gets
    that message (it runs entirely inside one long-lived WebSocket call), so
    it cannot produce an httponly cookie — see AuthMiddleware for the read
    side of this design.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] == "POST":
            if scope["path"] == "/login":
                await self._login(scope, receive, send)
                return
            if scope["path"] == "/logout":
                await self._logout(scope, receive, send)
                return
        await self.app(scope, receive, send)

    async def _login(self, scope, receive, send) -> None:
        request = Request(scope, receive)
        form = await request.form()
        email = str(form.get("email", "")).strip().lower()
        password = str(form.get("password", ""))

        error = "invalid"
        try:
            with get_session() as db_session:
                user = db_session.scalars(
                    select(User).where(User.email == email)
                ).one_or_none()
                if user and verify_password(password, user.password_hash):
                    scope["session"]["user_id"] = user.id
                    error = None
        except RuntimeError:
            error = "no_db"

        destination = "/" if error is None else f"/login?error={error}"
        response = RedirectResponse(destination, status_code=303)
        await response(scope, receive, send)

    async def _logout(self, scope, receive, send) -> None:
        session = scope.get("session")
        if session:
            session.clear()
        response = RedirectResponse("/login", status_code=303)
        await response(scope, receive, send)
