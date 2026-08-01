# Database tests (skeleton)

## What's tested

Nothing yet. `test_models.py` is a single placeholder (`pytest.skip(...)`) marking where database-layer coverage belongs, per the `db` pytest marker registered in `pyproject.toml`.

## What's stubbed / fetched from source

N/A — no fixtures exist yet. When built, this suite should exercise the real `src/models.py` (SQLAlchemy `Base`/`User`/`MedicalReceipt`) and `src/database.py` (`get_session()`) directly, the same way `tests/integration/test_login.py` does for the login flow, rather than reimplementing schema/session logic in test code.

## Limitations

- `database.get_session()` issues `SET LOCAL app.user_id = ...` for Postgres row-level security (see `alembic/versions/fb4488ff3ebf_add_user_id_to_medical_receipts_and_rls.py`, which enables RLS on `medical_receipts`). **sqlite can't stand in for Postgres here** — `SET LOCAL` and `CREATE POLICY` are Postgres-specific, so any real test of RLS enforcement needs an actual Postgres instance.
- The provisioning fixtures already exist (`postgres_url` / `db_session_factory` in `tests/conftest.py`, built for `tests/integration/test_login.py`) — this category just hasn't been filled in with actual model/RLS test cases yet.

## What's already available (and just needs test cases written against it)

`tests/conftest.py` provides:

- **`postgres_url`** (session-scoped): reuses `DATABASE_URL` if already set (assumed migrated), otherwise auto-provisions a disposable Postgres via testcontainers and runs the project's real `alembic upgrade head` against it. Skips (not errors) if Docker isn't reachable.
- **`db_session_factory`**: monkeypatches `database.engine`/`database.SessionLocal` to point at `postgres_url` for one test, so `database.get_session()` works exactly as it does in production, no reimplementation.

A real `test_models.py` should just request `db_session_factory` (see `tests/integration/test_login.py`'s `test_user` fixture for the pattern) rather than building its own provisioning logic.

## Future improvements

- Test each model's constraints (e.g. `User.email` uniqueness, the `@validates("email")` lowercasing behavior).
- Test the RLS policy on `medical_receipts` directly: one user's session should never see another user's rows, with and without `SET LOCAL app.user_id` set.
- Test that a fresh database migrates cleanly from scratch (`alembic upgrade head` on an empty Postgres) — `postgres_url` already does this for every run, so this would mostly be asserting on the *result* (expected tables/columns/policies exist).
