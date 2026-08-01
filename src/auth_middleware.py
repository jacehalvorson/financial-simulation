import json
import os
from base64 import b64encode

import itsdangerous
from context import current_user_id
from starlette.middleware.sessions import SessionMiddleware

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days, must match auth_middleware_stack()


class AuthMiddleware:
    """Reads user_id from the session (populated by SessionMiddleware) and
    stores it in a ContextVar so any .wire file can read it via import."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        session = scope.get("session", {})
        token = current_user_id.set(session.get("user_id"))
        try:
            await self.app(scope, receive, send)
        finally:
            current_user_id.reset(token)


def sign_session(data: dict) -> str:
    """Sign a session payload in the exact format Starlette's SessionMiddleware
    expects to read back from the "session" cookie.

    Login happens inside a PyWire interactive event handler, which runs over
    the page's persistent WebSocket connection rather than a fresh HTTP
    request/response cycle. SessionMiddleware only ever attaches its
    Set-Cookie header to an ``http.response.start`` message, which never
    occurs on that connection — so it cannot save our login itself. We sign
    the cookie value by hand (same secret, same itsdangerous scheme) and push
    it to the browser via ``page.set_cookie()``, PyWire's transport-agnostic
    cookie primitive. On the next page load/reconnect, SessionMiddleware reads
    this cookie normally and AuthMiddleware picks up the user id from it.
    """
    signer = itsdangerous.TimestampSigner(SECRET_KEY)
    payload = b64encode(json.dumps(data).encode("utf-8"))
    return signer.sign(payload).decode("utf-8")


def auth_middleware_stack():
    """Return the middleware list to pass to PyWire(middleware=...).

    Order: outermost first. SessionMiddleware must wrap AuthMiddleware so
    scope['session'] is populated before AuthMiddleware reads it.
    """
    return [
        (
            SessionMiddleware,
            {
                "secret_key": SECRET_KEY,
                "https_only": False,
                "max_age": SESSION_MAX_AGE,
            },
        ),
        AuthMiddleware,
    ]
