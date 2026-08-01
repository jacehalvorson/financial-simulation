"""End-to-end coverage of the login/logout flow (see src/login_middleware.py).

Runs against the in-process TestClient — no live dev server needed. The
DB-backed happy path (`TestLoginAgainstRealDatabase`) uses the `postgres_url`
fixture from tests/conftest.py, which auto-provisions a disposable Postgres
via testcontainers if Docker is available (or reuses DATABASE_URL if you've
already set one) — no manual setup required either way. It creates a
throwaway bcrypt-hashed user, exercises real login, then deletes it. See
tests/db/README.md for why a real Postgres can't be swapped for sqlite.
"""

import uuid

import pytest

pytestmark = pytest.mark.integration


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


def test_login_post_reports_no_db_when_unconfigured(client, monkeypatch):
    """Forces the not-configured state explicitly (rather than relying on
    DATABASE_URL being ambiently unset) so this test's outcome doesn't depend
    on whether a DB-backed test happened to run earlier in the same session
    and auto-provisioned one — see postgres_url in tests/conftest.py."""
    import database

    monkeypatch.setattr(database, "engine", None)
    monkeypatch.setattr(database, "SessionLocal", None)

    resp = client.post(
        "/login",
        data={"email": "nobody@example.com", "password": "irrelevant"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login?error=no_db"


@pytest.mark.db
class TestLoginAgainstRealDatabase:
    """Exercises the bcrypt-verified path against a real Postgres.

    Creates and tears down its own disposable user so it never depends on
    (or pollutes) whatever else lives in the database. Auto-provisioned via
    the `db_session_factory` fixture — no manual DATABASE_URL setup needed.
    """

    @pytest.fixture
    def test_user(self, db_session_factory):
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

    def test_session_persists_across_navigation_and_refresh(self, client, test_user):
        """A logged-in session must survive both navigating to other pages
        and refreshing (repeating a GET on) the same page — regressions here
        would mean users get silently logged out mid-session."""
        client.post(
            "/login",
            data={"email": test_user["email"], "password": test_user["password"]},
        )

        # Navigating to other pages shouldn't drop the session.
        for path in ["/", "/pricing", "/medicalreceipts", "/login"]:
            resp = client.get(path)
            assert resp.status_code == 200
            if path == "/login":
                assert "already logged in" in resp.text
            elif path == "/medicalreceipts":
                assert 'data-logged-in="true"' in resp.text
            else:
                assert test_user["email"] in resp.text
                assert "Log out" in resp.text

        # Refreshing (repeating a GET on) the same page shouldn't either.
        for _ in range(3):
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
