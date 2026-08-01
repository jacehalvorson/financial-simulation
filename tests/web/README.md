# Web styling tests (skeleton)

## What's tested

Nothing yet. `test_styling.py` is a single placeholder (`pytest.skip(...)`) marking where styling/design-consistency coverage belongs, per the `web` pytest marker registered in `pyproject.toml`.

## What's stubbed / fetched from source

N/A — no checks exist yet. When built, these should read the real `.wire` files under `src/pages/` and `src/components/` directly (source of truth), not a copy of their markup/CSS.

## Limitations

No visual/rendered-pixel testing is in scope here — this category is for *static, source-level* consistency checks (e.g. "does this page's gradient match the documented palette"), not a visual regression suite. Actual rendered-page checks belong in `tests/integration/` (see `test_login.py` for the pattern of asserting on rendered HTML via `TestClient`).

## Future improvements

- Check the feature-card gradient palette CLAUDE.md documents for `index.wire` (Global Market `#4e62c8→#8030b8`, Contributions `#c038a8→#b82040`, Withdrawals `#2868cc→#0898a8`, Medical `#28a860→#108898`) actually appears verbatim in the pages that are supposed to use it, so the doc and code can't silently drift apart.
- Verify every `<style scoped>` block in `src/pages/*.wire` and `src/components/*.wire` compiles cleanly (`pywire build`), catching CSS syntax errors before they ship.
- Spot-check Pico CSS class usage conventions (classless base + the project's own utility classes) for consistency across pages.
