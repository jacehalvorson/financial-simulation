import os
import subprocess
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    """In-process ASGI client for the PyWire app — no server process, no open ports.

    `main` imports bare (`from auth_middleware import ...`), which only
    resolves because pyproject.toml's `pythonpath` puts src/ on sys.path
    the same way pywire's own CLI does for `pywire dev src.main:app`.
    """
    from main import app

    with TestClient(app) as c:
        yield c


def _run_migrations(database_url: str) -> None:
    """Apply the project's real alembic migrations against `database_url`.

    Runs as a subprocess (not the alembic Python API in-process) so it's
    exactly the command a human/CI would run, and its output is easy to
    read if it fails.
    """
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic upgrade head failed against the test Postgres:\n"
        f"{result.stdout}\n{result.stderr}"
    )


@pytest.fixture(scope="session")
def postgres_url():
    """A real Postgres URL for DB-backed tests — auto-provisioned, no setup required.

    Prefers an already-configured `DATABASE_URL` (e.g. your local docker
    compose Postgres) so nothing extra spins up if you already have one —
    just make sure migrations are applied. Otherwise starts a disposable
    container via testcontainers, migrated with the project's real alembic
    migrations, and tears it down at the end of the session.

    Session-scoped: one container for the whole run. Skips (not errors) any
    test that needs it if Docker isn't reachable — tests/web, tests/docker,
    and the anonymous/no-db integration tests are unaffected either way,
    since none of them depend on this fixture.
    """
    existing = os.environ.get("DATABASE_URL")
    if existing:
        yield existing
        return

    try:
        from testcontainers.community.postgres import PostgresContainer
    except ImportError as e:
        pytest.skip(f"testcontainers not installed: {e}")

    try:
        # The docker client connects as soon as PostgresContainer() is
        # constructed, not just on .start() — both must be inside this try.
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except Exception as e:
        pytest.skip(f"Docker not available to auto-provision a test Postgres: {e}")

    try:
        url = container.get_connection_url()
        _run_migrations(url)
        yield url
    finally:
        container.stop()


@pytest.fixture
def db_session_factory(postgres_url, monkeypatch):
    """Point database.get_session() at `postgres_url` for this test only.

    database.py builds its engine/SessionLocal from DATABASE_URL at import
    time, so by the time a test runs, some earlier test may already have
    triggered that import with DATABASE_URL unset (engine=None baked in).
    Patching the two module attributes directly sidesteps that import-order
    dependency — get_session() reads them dynamically on every call.
    """
    import database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(postgres_url)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine))
    yield
    engine.dispose()
