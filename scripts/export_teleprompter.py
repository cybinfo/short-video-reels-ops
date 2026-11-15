#!/usr/bin/env python3
"""Export Season 01 & 02 teleprompter pack for own-voice recording in Voice Memos."""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEASON_DIRS = ("s01-asset-classification", "s02-risk-assessment")
DEFAULT_OUTPUT = REPO_ROOT / "renders" / "teleprompter-export.md"


def format_teleprompter_narration(narration: str, highlight_keywords: list[str] | None = None) -> str:
    """Wrap highlightKeywords in **BOLD CAPS** and insert ' // ' micro-breath cues at sentence breaks."""
    text = re.sub(r"\s+", " ", str(narration).strip())
    cleaned_kws = sorted({str(k).strip() for k in (highlight_keywords or []) if str(k).strip()}, key=len, reverse=True)
    if cleaned_kws:
        pattern = re.compile(
            r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(k) for k in cleaned_kws) + r")(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
        text = pattern.sub(lambda m: f"**{m.group(0).upper()}**", text)
    return re.sub(r"(?<!\bvs)([.!?])(\*\*)?\s+", lambda m: f"{m.group(1)}{m.group(2) or ''} // ", text)


def format_segment_line(segment: dict) -> str:
    start_sec = float(segment["startSec"])
    end_sec = float(segment["endSec"])
    phase = str(segment.get("phase", "")).upper()
    clauses = segment.get("ttsClauses") if isinstance(segment.get("ttsClauses"), list) else []
    ordered_spks: list[str] = []
    for cl in clauses:
        if isinstance(cl, dict) and str(cl.get("speaker", "")).strip():
            sp = str(cl["speaker"]).strip().upper()
            if not ordered_spks or ordered_spks[-1] != sp:
                ordered_spks.append(sp)
    speaker = " -> ".join(ordered_spks) if ordered_spks else str(segment.get("speaker", "")).strip().upper()
    tag = f"{phase} | {speaker}" if speaker else phase
    body = format_teleprompter_narration(segment.get("narration", ""), segment.get("highlightKeywords") or [])
    return f"**[{start_sec:04.1f}s – {end_sec:04.1f}s | {tag}]** {body}"


def load_season_episodes(episodes_root: Path | None = None) -> list[tuple[Path, dict]]:
    ep_root = episodes_root or (REPO_ROOT / "episodes")
    loaded: list[tuple[Path, dict]] = []
    for folder in SEASON_DIRS:
        folder_path = ep_root / folder
        if not folder_path.is_dir():
            continue
        for json_path in sorted(folder_path.glob("*.json")):
            if json_path.name == "schema.json":
                continue
            loaded.append((json_path, json.loads(json_path.read_text(encoding="utf-8"))))
    loaded.sort(key=lambda item: (int(item[1].get("season", 0)), int(item[1].get("episode", 0)), str(item[1].get("id", ""))))
    return loaded


def render_teleprompter_markdown(episodes: list[tuple[Path, dict]], repo_root: Path | None = None) -> str:
    root = repo_root or REPO_ROOT
    lines = [
        "# Cyber Jasoos (@cyberjasoos) — Season 01 & 02 Teleprompter Pack",
        "",
        "## Voice Memos Recording Checklist",
        "- [ ] **Environment**: Quiet room (HVAC/fans off, soft furnishings nearby to eliminate echo).",
        "- [ ] **Mic Placement**: Hold phone **6 inches off-axis from mouth** (45° angle blocks plosives).",
        "- [ ] **Delivery**: **160 WPM brisk thriller cadence** — punch **`**BOLD CAPS**`** words (synced to Crimson/Cyan screen highlights).",
        "- [ ] **Micro-Breaths**: Take a **`<250ms` pause at `//` markers**; drop exported `.m4a` files into `episodes/audio/<id>.m4a`.",
    ]
    for ep_path, manifest in episodes:
        ep_id = str(manifest["id"])
        season, episode = int(manifest["season"]), int(manifest["episode"])
        short_code = f"s{season:02d}e{episode:02d}"
        upper_code = short_code.upper()
        title = str(manifest.get("episodeTitle", ep_id))
        duration = float(manifest.get("durationSeconds", 50))
        target_wpm = int(manifest.get("voiceConfig", {}).get("targetWpm", 165))
        segments = manifest.get("scriptSegments", [])
        word_count = sum(len(str(s.get("narration", "")).split()) for s in segments)
        actual_wpm = round((word_count / duration) * 60.0) if duration > 0 else target_wpm
        try:
            rel_ep = ep_path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel_ep = ep_path.as_posix()
        ingest_cmd = (
            f"python3 scripts/prepare_voice.py --episode {rel_ep} --mode recorded "
            f"--input episodes/audio/{ep_id}.m4a && (cd engine && npm run render:{short_code})"
        )
        dur_str = f"{int(duration)}s" if duration.is_integer() else f"{duration:.1f}s"
        lines.extend([
            "",
            f"## {upper_code} — {title} (`{ep_id}`)",
            f"- **Duration:** {dur_str} | **Word Count:** {word_count} words | **Target WPM:** {target_wpm} WPM *(script pace: ~{actual_wpm} WPM)*",
            f"- **Ingest & Render:** `{ingest_cmd}`",
            "",
        ])
        for idx, seg in enumerate(segments):
            lines.append(format_segment_line(seg))
            if idx < len(segments) - 1:
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def export_teleprompter(output_path: Path | None = None, episodes_root: Path | None = None) -> Path:
    target = output_path or DEFAULT_OUTPUT
    episodes = load_season_episodes(episodes_root)
    if not episodes:
        raise FileNotFoundError(f"No episode manifests found under {episodes_root or (REPO_ROOT / 'episodes')}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_teleprompter_markdown(episodes), encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Markdown teleprompter pack for Seasons 01 and 02.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output Markdown path.")
    parser.add_argument("--episodes-dir", help="Optional custom episodes root directory.")
    args = parser.parse_args(argv)
    try:
        out = export_teleprompter(
            output_path=Path(args.output),
            episodes_root=Path(args.episodes_dir) if args.episodes_dir else None,
        )
    except Exception as exc:
        print(f"Teleprompter export failed: {exc}", file=sys.stderr)
        return 1
    print(f"Exported teleprompter pack: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
