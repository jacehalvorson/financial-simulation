import os
from pywire import PyWire
from starlette.middleware.sessions import SessionMiddleware
from auth_middleware import AuthMiddleware


class _AppWithMiddleware:
    """Proxies PyWire attributes (e.g. pages_dir) while routing ASGI calls
    through the middleware stack."""
    def __init__(self, pywire_app, middleware):
        self._pywire = pywire_app
        self._middleware = middleware

    def __getattr__(self, name):
        return getattr(self._pywire, name)

    async def __call__(self, scope, receive, send):
        await self._middleware(scope, receive, send)


_pywire = PyWire(
    enable_pjax=True,
    debug=True,
)

app = _AppWithMiddleware(
    _pywire,
    AuthMiddleware(
        SessionMiddleware(
            _pywire,
            secret_key=os.environ.get("SECRET_KEY", "dev-secret-change-in-production"),
            https_only=False,
            max_age=60 * 60 * 24 * 30,  # 30 days
        ),
    ),
)
