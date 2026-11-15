# SocialMediaShortVideo — Standardized 5-Layer `/tests` Architecture

This directory centralizes all automated verification and governance documentation for `SocialMediaShortVideo` (`@cyberjasoos`) across 5 layers:

## Directory Structure

- `unit/` — **Layer 1 (Unit Tests)**: Formula-driven validation of `episodes/schema.json`, WPM pacing bounds (`130–195 WPM`), and `--pui-*` token contracts in `docs/assets/guide.css`.
  - `tests/unit/test_unit_episode_schema.py`
- `integration/` — **Layer 2 (Integration Tests)**: Verifies `docs/index.html` mounts `data-brand="creator"` + `assets/00-personal-ui-shared.css` before `assets/guide.css` and validates cross-project CSS parity via `sync-personal-ui.mjs --check`.
  - `tests/integration/test_integration_pipeline_and_ui.py`
- `e2e/` — **Layer 3 (E2E & Smoke Tests)**: Verifies `docs/index.html`, stylesheet link order, token mappings, and Remotion `engine/` registry integrity.
  - `tests/e2e/run_smoke.mjs`
- `load/` — **Layer 4 (Load & Throughput Tests)**: k6 load script benchmarking local preview and manifest throughput.
  - `tests/load/k6-render-throughput.js`
- `docs/` — **Layer 5 (Security, UAT, Regression & Accessibility Docs)**:
  - `tests/docs/owasp-security-audit.md`
  - `tests/docs/uat-stakeholder-matrix.md`
  - `tests/docs/module-regression-map.md`
  - `tests/docs/wcag-a11y-checklist.md`
- Root Regression Suites (Preserved):
  - `tests/test_framework.py`
  - `tests/test_instagram_ops.py`
  - `tests/test_self_healing_pipeline.py`

## Exact Commands to Run All Layers

```bash
# Run all Python Unit, Integration, and Root Regression suites (Layers 1 & 2)
python3 -m unittest

# Run only Layer 1 Unit suite
python3 -m unittest tests/unit/test_unit_episode_schema.py

# Run only Layer 2 Integration suite
python3 -m unittest tests/integration/test_integration_pipeline_and_ui.py

# Run Layer 3 E2E & Smoke verification
node tests/e2e/run_smoke.mjs

# Run Layer 4 k6 Load script (requires local loopback server on 127.0.0.1:4173)
k6 run tests/load/k6-render-throughput.js
```
