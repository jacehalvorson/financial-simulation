import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

# Shared between auth_middleware.py (SessionMiddleware config) and
# login_middleware.py (the companion cookie below) — kept in its own module
# so neither has to import the other's constants and risk a circular import.
