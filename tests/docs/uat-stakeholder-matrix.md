# UAT Stakeholder Matrix (`SocialMediaShortVideo`)

| Persona / Role | Core Journey | Acceptance Criteria | Automated Gate |
|---|---|---|---|
| **Creator / Producer** | Compile 35-line YAML brief into 1080x1920 Reel | `validate_episode.py` passes with 0 errors; WPM within `130-195` | `tests/unit/test_unit_episode_schema.py` |
| **Launch Operator** | Copy caption, bio, and poll stickers from `docs/index.html` | `data-brand="creator"` skin active, 1-click Copy buttons work, Light/Dark toggle persists | `tests/e2e/run_smoke.mjs` |
| **Community Manager** | Tally A/B/C comments and inject winner into Part 2 | Deduplicates repeat voters, excludes creator handles, injects Hindi/Urdu numeral opening line | `tests/test_instagram_ops.py` |
| **Compliance Reviewer** | Verify commercial voice licensing & PIB/I4C citations | `--publish-ready` blocks preview TTS; primary advisories verified | `tests/test_framework.py` |
