# Module Regression Map (`SocialMediaShortVideo`)

| Module / File | Responsibility | Primary Test Coverage |
|---|---|---|
| `scripts/validate_episode.py` | Episode manifest schema, WPM pacing, commercial license, and safe-zone guards | `tests/unit/test_unit_episode_schema.py`, `tests/test_framework.py` |
| `scripts/compile_story_brief.py` | Compiles 35-line YAML story briefs into full Remotion episode manifests | `tests/test_self_healing_pipeline.py` |
| `scripts/prepare_voice.py` | Neural/recorded voice synthesis, RMS silence snapping, and word-boundary timestamps | `tests/test_framework.py` |
| `scripts/instagram_ops.py` | Poll vote classification, deduplication, Socratic replies, and SQLite growth ledger | `tests/test_instagram_ops.py`, `tests/test_self_healing_pipeline.py` |
| `docs/index.html` & `docs/assets/guide.css` | Launch & Automation Hub consuming `00-personal-ui-shared.css` (`data-brand="creator"`) | `tests/integration/test_integration_pipeline_and_ui.py`, `tests/e2e/run_smoke.mjs` |
| `engine/src/` | Remotion 1080x1920 Noir Cinema scene renderers and generated episode registry | `tests/e2e/run_smoke.mjs`, `tests/test_framework.py` |
