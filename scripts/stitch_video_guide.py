#!/usr/bin/env python3
"""Stitch ordered chapter MP4s into a 1080x1920 @ 30fps master guide with FFMETADATA1 chapters."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parent.parent
FFMPEG = "/opt/homebrew/bin/ffmpeg" if Path("/opt/homebrew/bin/ffmpeg").is_file() else "ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe" if Path("/opt/homebrew/bin/ffprobe").is_file() else "ffprobe"

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30
TARGET_SAMPLE_RATE = 44100

DEFAULT_CHAPTERS: tuple[tuple[str, str], ...] = (
    ("renders/guide/ch01-story-brief-autocast.mp4", "1. Web Hub, Auto-Cast & 35-Line Story Brief"),
    ("renders/guide/ch02-self-healing-build.mp4", "2. One-Command Build & Safe-Zone Self-Heal"),
    ("renders/guide/ch03-upload-and-poll-branch.mp4", "3. 7:40 PM Upload, Poll Tally & Part 2 Branch"),
    ("renders/guide/ch04-growth-ledger-learning.mp4", "4. SQLite Growth Ledger & Auto-Learning"),
)
DEFAULT_OUTPUT = "renders/guide/cyber-jasoos-automation-master-guide.mp4"


def _resolve_input_path(raw: str | Path) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    if p.is_file():
        return p.resolve()
    return (REPO_ROOT / p).resolve()


def _resolve_output_path(raw: str | Path | None) -> Path:
    if raw is None:
        return (REPO_ROOT / DEFAULT_OUTPUT).resolve()
    p = Path(raw)
    return p if p.is_absolute() else p.resolve()


def _escape_ffmeta(value: str) -> str:
    return re.sub(r"([\\=;#\n\r])", r"\\\1", str(value))


def probe_duration_sec(mp4_path: Path) -> float:
    cmd = [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(mp4_path)]
    dur = float(subprocess.check_output(cmd, text=True).strip())
    if dur <= 0:
        raise ValueError(f"Non-positive duration ({dur}) probed for {mp4_path}")
    return dur


def _has_audio_stream(mp4_path: Path) -> bool:
    cmd = [FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(mp4_path)]
    return bool(subprocess.check_output(cmd, text=True).strip())


def build_ffmetadata(chapters: list[dict[str, object]]) -> str:
    lines = [";FFMETADATA1"]
    for ch in chapters:
        lines.extend(["[CHAPTER]", "TIMEBASE=1/1000", f"START={ch['startMs']}", f"END={ch['endMs']}", f"title={_escape_ffmeta(str(ch['title']))}"])
    return "\n".join(lines) + "\n"


def stitch_video_guide(input_paths: Sequence[Path], titles: Sequence[str], output_path: Path) -> dict[str, object]:
    if not input_paths:
        raise ValueError("At least one chapter MP4 is required.")
    if len(input_paths) != len(titles):
        raise ValueError(f"Input count ({len(input_paths)}) must match title count ({len(titles)}).")

    chapters: list[dict[str, object]] = []
    audio_flags: list[bool] = []
    cursor_sec = 0.0
    for idx, (src, title) in enumerate(zip(input_paths, titles), 1):
        if not src.is_file():
            raise FileNotFoundError(f"Chapter input #{idx} not found: {src}")
        dur = probe_duration_sec(src)
        audio_flags.append(_has_audio_stream(src))
        start_ms = int(round(cursor_sec * 1000.0))
        cursor_sec += dur
        end_ms = max(start_ms + 1, int(round(cursor_sec * 1000.0)))
        chapters.append({"index": idx, "title": str(title), "inputPath": str(src), "durationSec": round(dur, 3), "startMs": start_ms, "endMs": end_ms})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    n_ch = len(chapters)
    meta_input_idx = n_ch

    filter_parts: list[str] = []
    concat_pairs: list[str] = []
    for i, ch in enumerate(chapters):
        filter_parts.append(
            f"[{i}:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"fps={TARGET_FPS},format=yuv420p,setpts=PTS-STARTPTS[v{i}]"
        )
        if audio_flags[i]:
            filter_parts.append(
                f"[{i}:a]aresample={TARGET_SAMPLE_RATE},"
                f"aformat=sample_fmts=fltp:channel_layouts=stereo,asetpts=PTS-STARTPTS[a{i}]"
            )
        else:
            filter_parts.append(
                f"anullsrc=r={TARGET_SAMPLE_RATE}:cl=stereo:d={ch['durationSec']},asetpts=PTS-STARTPTS[a{i}]"
            )
        concat_pairs.append(f"[v{i}][a{i}]")
    filter_parts.append(f"{''.join(concat_pairs)}concat=n={n_ch}:v=1:a=1[vout][aout]")

    with tempfile.TemporaryDirectory() as td:
        ffmeta_path = Path(td) / "chapters.ffmeta"
        ffmeta_path.write_text(build_ffmetadata(chapters), encoding="utf-8")
        cmd: list[str] = [FFMPEG, "-y", "-v", "error"]
        for src in input_paths:
            cmd.extend(["-i", str(src)])
        cmd.extend(
            [
                "-f", "ffmetadata", "-i", str(ffmeta_path),
                "-filter_complex", ";".join(filter_parts),
                "-map", "[vout]", "-map", "[aout]",
                "-map_metadata", str(meta_input_idx),
                "-map_chapters", str(meta_input_idx),
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                str(output_path),
            ]
        )
        subprocess.run(cmd, check=True)

    probe_raw = subprocess.check_output(
        [FFPROBE, "-v", "error", "-show_streams", "-show_chapters", "-show_format", "-of", "json", str(output_path)],
        text=True,
    )
    probe = json.loads(probe_raw)
    streams = probe.get("streams") or []
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    out_chapters = probe.get("chapters") or []
    out_dur = float((probe.get("format") or {}).get("duration") or 0.0)

    if not v_stream or int(v_stream.get("width") or 0) != TARGET_WIDTH or int(v_stream.get("height") or 0) != TARGET_HEIGHT:
        raise RuntimeError(f"Output video stream failed {TARGET_WIDTH}x{TARGET_HEIGHT} check: {v_stream}")
    if not a_stream or a_stream.get("codec_name") != "aac":
        raise RuntimeError(f"Output audio stream failed AAC check: {a_stream}")
    if len(out_chapters) != n_ch:
        raise RuntimeError(f"Output chapter count ({len(out_chapters)}) != expected ({n_ch})")
    if out_dur <= 0:
        raise RuntimeError(f"Invalid output duration: {out_dur}")

    return {
        "status": "ok",
        "outputPath": str(output_path),
        "chapterCount": len(out_chapters),
        "totalDurationSec": round(out_dur, 3),
        "sizeBytes": output_path.stat().st_size,
        "chapters": chapters,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", help="Ordered chapter MP4 paths to stitch.")
    parser.add_argument("--titles", nargs="+", help="Chapter titles matching --inputs.")
    parser.add_argument("--output", help=f"Destination master MP4 (default: {DEFAULT_OUTPUT}).")
    args = parser.parse_args(argv)

    if args.inputs:
        in_paths = [_resolve_input_path(p) for p in args.inputs]
        titles = list(args.titles) if args.titles else [f"Chapter {i}: {p.stem}" for i, p in enumerate(in_paths, 1)]
    else:
        in_paths = [_resolve_input_path(rel) for rel, _ in DEFAULT_CHAPTERS]
        titles = list(args.titles) if args.titles else [title for _, title in DEFAULT_CHAPTERS]

    summary = stitch_video_guide(in_paths, titles, _resolve_output_path(args.output))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
