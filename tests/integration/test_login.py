"""End-to-end coverage of the login/logout flow (see src/login_middleware.py).

Runs against the in-process TestClient — no docker, no dev server needed.
The DB-backed happy path is gated behind DATABASE_URL: it creates a
throwaway bcrypt-hashed user, exercises real login, then deletes it. Without
DATABASE_URL, only the paths that don't require a real user are exercised
(anonymous state, the "no_db" graceful-failure branch, logout safety) — see
tests/db/test_models.py for why a real Postgres can't be swapped for sqlite.
"""

import os
import uuid

import pytest

pytestmark = pytest.mark.integration

HAS_DB = bool(os.environ.get("DATABASE_URL"))


def test_login_page_shows_form_when_anonymous(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert 'action="/login"' in resp.text
    assert "already logged in" not in resp.text


def test_medicalreceipts_gate_is_closed_when_anonymous(client):
    resp = client.get("/medicalreceipts")
    assert resp.status_code == 200
    assert 'data-logged-in="false"' in resp.text


def test_logout_is_a_no_op_when_not_logged_in(client):
    resp = client.post("/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"


@pytest.mark.skipif(HAS_DB, reason="only exercises the no-DATABASE_URL fallback path")
def test_login_post_reports_no_db_when_unconfigured(client):
    resp = client.post(
        "/login",
        data={"email": "nobody@example.com", "password": "irrelevant"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login?error=no_db"


@pytest.mark.db
@pytest.mark.skipif(not HAS_DB, reason="needs a real DATABASE_URL — see tests/db/test_models.py")
class TestLoginAgainstRealDatabase:
    """Exercises the bcrypt-verified path against a real Postgres.

    Creates and tears down its own disposable user so it never depends on
    (or pollutes) whatever else lives in the database.
    """

    @pytest.fixture
    def test_user(self):
        from database import get_session
        from models import User
        from password_utils import hash_password

        # models.User.id is String(36) — a bare uuid4() fits exactly (36 chars);
        # a "test-" prefix would overflow it and fail the INSERT against a real
        # Postgres (verified: psycopg2.errors.StringDataRightTruncation).
        user_id = str(uuid.uuid4())
        email = f"test-{user_id}@example.test"
        password = "correct horse battery staple"

        with get_session() as db_session:
            db_session.add(
                User(id=user_id, email=email, password_hash=hash_password(password))
            )

        yield {"id": user_id, "email": email, "password": password}

        with get_session() as db_session:
            db_session.query(User).filter(User.id == user_id).delete()

    def test_wrong_password_is_rejected(self, client, test_user):
        resp = client.post(
            "/login",
            data={"email": test_user["email"], "password": "wrong"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/login?error=invalid"
        assert "session" not in resp.cookies

    def test_correct_password_sets_httponly_session_cookie(self, client, test_user):
        resp = client.post(
            "/login",
            data={"email": test_user["email"], "password": test_user["password"]},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/"
        set_cookie = resp.headers["set-cookie"]
        assert "session=" in set_cookie
        assert "httponly" in set_cookie.lower()

    def test_session_persists_identity_and_shows_in_nav(self, client, test_user):
        client.post(
            "/login",
            data={"email": test_user["email"], "password": test_user["password"]},
        )
        resp = client.get("/")
        assert test_user["email"] in resp.text
        assert "Log out" in resp.text

    def test_logout_clears_the_session(self, client, test_user):
        client.post(
            "/login",
            data={"email": test_user["email"], "password": test_user["password"]},
        )
        client.post("/logout")
        resp = client.get("/login")
        assert "already logged in" not in resp.text
