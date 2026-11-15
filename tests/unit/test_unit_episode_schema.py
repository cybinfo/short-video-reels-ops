#!/usr/bin/env python3
"""Layer 1 Unit Tests: Episode brief schema, WPM pacing, and design token contracts."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import compile_story_brief  # noqa: E402
import validate_episode  # noqa: E402


class EpisodeSchemaAndTokenContractUnitTests(unittest.TestCase):
    """Formula-driven unit tests for episode schema, WPM pacing, and CSS token contracts."""

    def test_episode_json_schema_and_live_manifests_valid(self) -> None:
        schema_path = REPO_ROOT / "episodes" / "schema.json"
        self.assertTrue(schema_path.is_file(), f"Missing schema file: {schema_path}")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertIn("$schema", schema)

        ep_files = sorted(
            f for f in (REPO_ROOT / "episodes").rglob("*.json")
            if f.name != "schema.json" and "brief" not in f.name and "briefs" not in f.parts
        )
        self.assertGreaterEqual(len(ep_files), 5)
        for ep_file in ep_files:
            manifest = json.loads(ep_file.read_text(encoding="utf-8"))
            errors = validate_episode.validate_manifest(manifest)
            self.assertEqual(errors, [], f"Schema validation failed for {ep_file.name}: {errors}")

    def test_wpm_pacing_formula_bounds_across_case01_and_case02(self) -> None:
        for rel_path in (
            "episodes/s01-asset-classification/s01e01-forgotten-bucket.json",
            "episodes/s01-asset-classification/s01e02-crown-jewels.json",
        ):
            manifest = json.loads((REPO_ROOT / rel_path).read_text(encoding="utf-8"))
            duration_sec = float(manifest["durationSeconds"])
            word_count = sum(len(seg["narration"].split()) for seg in manifest["scriptSegments"])
            computed_wpm = word_count / (duration_sec / 60.0)
            self.assertGreaterEqual(computed_wpm, 130.0, f"{manifest['id']} WPM too slow: {computed_wpm:.2f}")
            self.assertLessEqual(computed_wpm, 195.0, f"{manifest['id']} WPM too fast: {computed_wpm:.2f}")

        brief = compile_story_brief.load_brief(REPO_ROOT / "episodes" / "briefs" / "case02-part1-shaadi-qr.yaml")
        compiled = compile_story_brief.compile_brief(brief)
        self.assertEqual(validate_episode.validate_manifest(compiled), [])

    def test_shared_personal_ui_creator_token_contract(self) -> None:
        shared_css = (REPO_ROOT / "docs" / "assets" / "00-personal-ui-shared.css").read_text(encoding="utf-8")
        guide_css = (REPO_ROOT / "docs" / "assets" / "guide.css").read_text(encoding="utf-8")

        self.assertIn('html[data-brand="creator"]', shared_css)
        for token in (
            "--pui-surface-dark",
            "--pui-surface-light",
            "--pui-brand-accent",
            "--pui-emerald",
            "--pui-amber",
            "--pui-font-sans",
        ):
            self.assertIn(token, shared_css, f"Missing {token} in 00-personal-ui-shared.css")
            self.assertIn(token, guide_css, f"guide.css does not consume {token}")

        for mapped_var in ("--bg-primary:", "--accent-crimson:", "--emerald:", "--amber:", "font-family: var(--pui-font-sans"):
            self.assertIn(mapped_var, guide_css, f"Missing mapped variable {mapped_var} in guide.css")


if __name__ == "__main__":
    unittest.main()
