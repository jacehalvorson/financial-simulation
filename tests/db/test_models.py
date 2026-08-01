"""Skeleton for src/models.py + src/database.py coverage.

database.get_session() sets a Postgres session variable (`SET LOCAL
app.user_id`) for row-level security — sqlite can't stand in for that, so
this needs a disposable real Postgres (e.g. testcontainers-python's
postgres module, or a docker-compose service gated behind the `docker`
marker). Not implemented yet.
"""

import pytest

pytestmark = pytest.mark.db


def test_placeholder():
    pytest.skip("DB test harness not implemented yet — see module docstring")
