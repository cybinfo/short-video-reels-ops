# OWASP Top-10 & Creator Pipeline Security Audit (`SocialMediaShortVideo`)

| Control ID | OWASP Category | Pipeline / UI Enforcement | Verification Layer |
|---|---|---|---|
| `SEC-01` | A01 Broken Access Control | Loopback-only (`127.0.0.1`) preview servers; zero LAN/0.0.0.0 exposure | `tests/integration/test_integration_pipeline_and_ui.py` |
| `SEC-02` | A02 Cryptographic & Secret Hygiene | Instagram Graph API access tokens redacted in error logs; zero tokens in git | `tests/test_instagram_ops.py` |
| `SEC-03` | A03 Injection Prevention | Strict JSON Schema validation (`episodes/schema.json`) and parameterized SQLite queries in `instagram_ops.py` | `tests/unit/test_unit_episode_schema.py` |
| `SEC-04` | A05 Security Misconfiguration | Publish-Ready Commercial Voice License Guard blocks non-commercial TTS in production uploads | `tests/test_framework.py` |
| `SEC-05` | A08 Software & Data Integrity | `sync-personal-ui.mjs --check` enforces byte-identical `00-personal-ui-shared.css` parity | `tests/integration/test_integration_pipeline_and_ui.py` |
