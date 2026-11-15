#!/usr/bin/env python3
"""Export a sanitized, static GitHub Pages bundle from docs/ to --out-dir."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC_DIR = REPO_ROOT / "docs"

# Hex-encoded tokens so forbidden personal/account strings never sit in plaintext in tracked scripts.
_FORBIDDEN_HEX_TOKENS: tuple[str, ...] = (
    "7265616c63796265726a61736f6f7340676d61696c2e636f6d",
    "7365746872616a6174",
    "72616a61742e73657468",
    "736572766963656e6f77",
)
FORBIDDEN_TOKENS: tuple[str, ...] = tuple(bytes.fromhex(h).decode("utf-8") for h in _FORBIDDEN_HEX_TOKENS)

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE)
_REPO_USER_PATH_RE = re.compile(
    r"/Users/[A-Za-z0-9._-]+(?:/Desktop/[A-Za-z0-9._ -]+/SocialMediaShortVideo)?"
)
_SPOILER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"asli\s+gaddar\s+pados\s+ka\s+golu(?:\s+nikla)?!?", re.IGNORECASE),
    re.compile(r"neighbor\s+golu\s*\(option\s*a\)[^.<\n]*", re.IGNORECASE),
    re.compile(r"culprit\s*(?:is|[:=])\s*(?:option\s*a\s*[-—:]?\s*)?(?:pados\s+ka\s+)?golu", re.IGNORECASE),
)


def sanitize_html(raw_html: str) -> str:
    """Deterministically redact creator emails, local macOS paths, and explicit Part 2 spoilers."""
    out = _EMAIL_RE.sub("&lt;DEDICATED_CREATOR_GMAIL&gt;", raw_html)
    out = _REPO_USER_PATH_RE.sub("&lt;REPO_ROOT&gt;", out)
    for pat in _SPOILER_PATTERNS:
        out = pat.sub("&lt;PART2_REVEAL&gt;", out)
    for tok in FORBIDDEN_TOKENS:
        if "@" in tok:
            out = re.sub(re.escape(tok), "&lt;DEDICATED_CREATOR_GMAIL&gt;", out, flags=re.IGNORECASE)
        else:
            out = re.sub(re.escape(tok), "&lt;REDACTED&gt;", out, flags=re.IGNORECASE)
    return out


def find_forbidden_leaks(text: str) -> list[str]:
    """Return any forbidden tokens still present (case-insensitive) in exported text."""
    lower = text.lower()
    return [tok for tok in FORBIDDEN_TOKENS if tok.lower() in lower]


def export_sanitized_site(src_dir: Path, out_dir: Path) -> dict[str, object]:
    """Copy docs/index.html + docs/assets/* to out_dir, write .nojekyll, sanitize, and verify."""
    src = Path(src_dir).resolve()
    dst = Path(out_dir).resolve()
    index_src = src / "index.html"
    assets_src = src / "assets"
    if not index_src.is_file():
        raise FileNotFoundError(f"Missing source portal HTML: {index_src}")
    if not assets_src.is_dir():
        raise FileNotFoundError(f"Missing source assets directory: {assets_src}")

    dst.mkdir(parents=True, exist_ok=True)
    dst_assets = dst / "assets"
    if dst_assets.exists():
        shutil.rmtree(dst_assets)
    shutil.copytree(assets_src, dst_assets)

    sanitized_html = sanitize_html(index_src.read_text(encoding="utf-8"))
    index_dst = dst / "index.html"
    index_dst.write_text(sanitized_html, encoding="utf-8")
    (dst / ".nojekyll").write_text("", encoding="utf-8")

    leaks = find_forbidden_leaks(index_dst.read_text(encoding="utf-8"))
    for text_asset in sorted(dst_assets.glob("*")):
        if text_asset.suffix.lower() in {".css", ".js", ".html", ".json", ".svg"}:
            leaks.extend(find_forbidden_leaks(text_asset.read_text(encoding="utf-8")))
    if leaks:
        raise RuntimeError(f"Sanitization assertion failed; forbidden tokens remain: {sorted(set(leaks))}")

    copied_assets = sorted(p.name for p in dst_assets.iterdir() if p.is_file())
    return {
        "outDir": str(dst),
        "indexHtml": str(index_dst),
        "nojekyll": str(dst / ".nojekyll"),
        "assetCount": len(copied_assets),
        "assets": copied_assets,
        "forbiddenLeakCount": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export sanitized Cyber Jasoos Web Hub for GitHub Pages.")
    parser.add_argument("--src-dir", type=Path, default=DEFAULT_SRC_DIR, help="Source docs directory (default: docs/).")
    parser.add_argument("--out-dir", type=Path, required=True, help="Target output directory for sanitized Pages site.")
    args = parser.parse_args(argv)
    summary = export_sanitized_site(args.src_dir, args.out_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
