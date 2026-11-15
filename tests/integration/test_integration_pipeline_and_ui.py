#!/usr/bin/env python3
"""Layer 2 Integration Tests: Pipeline orchestration, UI skin consumption, and Personal UI sync parity."""

from __future__ import annotations

import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent


class _HeadAndRootParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.html_attrs: dict[str, str | None] = {}
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "html":
            self.html_attrs = attr_map
        elif tag == "link" and attr_map.get("rel") == "stylesheet" and attr_map.get("href"):
            self.stylesheets.append(str(attr_map["href"]))


class PipelineAndPersonalUIIntegrationTests(unittest.TestCase):
    """Verifies docs/index.html consumes 00-personal-ui-shared.css + data-brand='creator' and sync parity passes."""

    def test_docs_index_html_consumes_creator_brand_and_shared_css_order(self) -> None:
        index_html = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        parser = _HeadAndRootParser()
        parser.feed(index_html)

        self.assertEqual(parser.html_attrs.get("lang"), "en")
        self.assertEqual(parser.html_attrs.get("data-brand"), "creator")
        self.assertEqual(
            parser.stylesheets[:2],
            ["assets/00-personal-ui-shared.css", "assets/guide.css"],
            f"Expected 00-personal-ui-shared.css right before guide.css, got {parser.stylesheets}",
        )

    def test_sync_personal_ui_check_passes(self) -> None:
        sync_script = WORKSPACE_ROOT / "shared" / "personal-ui" / "sync-personal-ui.mjs"
        self.assertTrue(sync_script.is_file(), f"Missing canonical sync script: {sync_script}")
        proc = subprocess.run(
            ["node", str(sync_script), "--check"],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, f"sync-personal-ui.mjs --check failed:\n{proc.stdout}\n{proc.stderr}")


if __name__ == "__main__":
    unittest.main()
