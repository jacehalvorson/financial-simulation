import os

from context import current_user_id
from login_middleware import LoginFormMiddleware
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


def auth_middleware_stack():
    """Return the middleware list to pass to PyWire(middleware=...).

    Order: outermost first. SessionMiddleware must wrap LoginFormMiddleware
    so scope['session'] is a real Starlette Session the login/logout POST
    handlers can write to. AuthMiddleware runs innermost, reading whatever
    SessionMiddleware decoded from the cookie on this request.
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
        LoginFormMiddleware,
        AuthMiddleware,
    ]
