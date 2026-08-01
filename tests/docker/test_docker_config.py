"""Skeleton for static validation of docker-compose.yml / Dockerfile.

Candidates: CLAUDE.md's rule that mkcert must never be added to the
Dockerfile, required env vars are documented in .env.example, the compose
service actually mounts src/ for hot-reload. Not implemented yet.
"""

import pytest

pytestmark = pytest.mark.docker


def test_placeholder():
    pytest.skip("Docker config test harness not implemented yet — see module docstring")
