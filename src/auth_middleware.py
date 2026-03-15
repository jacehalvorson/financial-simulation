from context import current_user_id


class AuthMiddleware:
    """Reads user_id from the session (populated by SessionMiddleware) and
    stores it in a ContextVar so any .wire file can read it via import."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            session = scope.get("session", {})
            token = current_user_id.set(session.get("user_id", "dev-user-hardcoded"))  # TEMP
            try:
                await self.app(scope, receive, send)
            finally:
                current_user_id.reset(token)
        else:
            await self.app(scope, receive, send)
