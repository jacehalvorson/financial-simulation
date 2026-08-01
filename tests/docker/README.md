# Docker configuration tests (skeleton)

## What's tested

Nothing yet. `test_docker_config.py` is a single placeholder (`pytest.skip(...)`) marking where Docker/Compose configuration coverage belongs, per the `docker` pytest marker registered in `pyproject.toml`.

## What's stubbed / fetched from source

N/A — no checks exist yet. When built, these should statically parse the real `Dockerfile`, `docker-compose.yml`, and `.env.example` at the repo root directly, rather than duplicating their expected contents in test code.

## Limitations

This category is for **static configuration validation** — it does not build images or boot containers (that would belong in a slower, separately-gated CI job, not the default `uv run pytest` run). It cannot catch runtime failures (e.g. a service that builds fine but crashes on start).

## Future improvements

- Assert the Dockerfile never adds `mkcert` — CLAUDE.md is explicit that the container-generated cert won't be trusted by the host browser, so this regressing would be a real (if subtle) bug.
- Assert the compose service mounts `src/` for hot-reload, matching the documented dev workflow.
- Assert every env var read by the app at import time (`SECRET_KEY`, `DATABASE_URL`, `POSTGRES_PASSWORD`, `STRIPE_PUBLIC_KEY`, etc.) is documented in `.env.example`.
- Consider a separate, explicitly-invoked (not default-run) smoke test that actually runs `docker compose up` and hits `/` — real container-boot coverage, kept out of the fast default suite.
