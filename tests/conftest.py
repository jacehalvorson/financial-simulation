import pytest
from starlette.testclient import TestClient


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
