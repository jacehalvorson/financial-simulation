# Integration tests

## What's tested

`test_login.py` covers the login/logout flow end to end:

- The `/login` page renders the plain HTML login form when nobody is logged in.
- `/medicalreceipts` correctly shows its anonymous (`data-logged-in="false"`) state, confirming the auth gate added in `medicalreceipts.wire` actually reads the real session.
- `POST /logout` is a safe no-op (redirects to `/login`) when there's no session to clear.
- `POST /login` reports the graceful `no_db` error when `DATABASE_URL` isn't configured, instead of raising.
- (DB-gated, see below) A correct email/password sets a `Set-Cookie` with `HttpOnly`, a wrong password is rejected without setting a cookie, the logged-in identity shows up in the nav (`__layout__.wire`), and logout clears the session.

## What's real vs. stubbed

Nothing is mocked. `tests/conftest.py`'s `client` fixture imports the actual `main.app` — the same `PyWire` instance, middleware stack (`SessionMiddleware` → `LoginFormMiddleware` → `AuthMiddleware`), `.wire` pages, and route handlers used in dev/prod — and drives it in-process via `starlette.testclient.TestClient`. Login/logout go through the real `login_middleware.py`, `models.User`, and `password_utils.py` (real bcrypt hashing/verification).

The one thing that *is* different from a real deployment: requests go straight into the ASGI app in-process, not over a real TCP socket or through a browser. That's fine here because `/login`/`/logout` are plain, unbound HTML forms with no client-side JS involved (see CLAUDE.md's Auth section for why that's deliberate) — a real browser round-trip wouldn't exercise anything this test doesn't already cover.

## Limitations

- **The DB-backed class (`TestLoginAgainstRealDatabase`) needs Docker.** It uses the `postgres_url` fixture (`tests/conftest.py`): if `DATABASE_URL` is already set it's reused as-is (assumed already migrated); otherwise a disposable Postgres is auto-provisioned via testcontainers and migrated with the project's real `alembic upgrade head` — no manual setup required. If Docker isn't reachable, the fixture calls `pytest.skip(...)` rather than erroring, so that class skips cleanly instead of the run failing. `test_login_post_reports_no_db_when_unconfigured` deliberately does *not* depend on this fixture — it forces `database.engine`/`SessionLocal` to `None` directly via `monkeypatch`, so its outcome doesn't depend on whether a DB test ran earlier in the same session (see the docstring on that test).
- No coverage of PyWire's interactive WebSocket protocol — irrelevant to *this* page since login/logout are plain form POSTs, but a page with `@click`-driven behavior (e.g. `contributions.wire`) would need a different test approach (see "Future improvements").
- No browser-level check (real cookie storage, CSS, JS) — this is a server-side/HTTP-contract test, not a UI test.
- No coverage of signup/password-reset — those don't exist yet.
- Auto-provisioning adds real time to the default `uv run pytest` run — a fresh container + migration is a few seconds on the first DB test in a session (subsequent tests in the same session reuse it, since the container is session-scoped). Pointing `DATABASE_URL` at an already-running, already-migrated Postgres (e.g. your docker compose one) skips that cost entirely.

## Future improvements

- Add a WebSocket-protocol test helper (speaking PyWire's msgpack event protocol over `client.websocket_connect("/_pywire/ws")`) once a test needs to drive an interactive `@click` page — not needed yet since nothing currently under test uses it.
- Extend coverage to signup and password-reset flows once they exist.
- Assert the RLS-relevant behavior once tests touch `medical_receipts` (the `users` table itself has no row-level security — see `tests/db/README.md`).
- `tests/db/`'s real test harness (once built) should reuse `postgres_url`/`db_session_factory` from `tests/conftest.py` rather than duplicating the provisioning logic.
