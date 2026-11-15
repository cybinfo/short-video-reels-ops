#!/usr/bin/env python3
"""Deterministic 1080x1920 NOIR_GRID visual plate generator for Guide Episode (guide01)."""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = REPO_ROOT / "assets" / "characters" / "guide01" / "raw"
SCRATCH_DIR = REPO_ROOT / "renders" / "uat"
CHROME_BIN = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FFMPEG = "/opt/homebrew/bin/ffmpeg" if Path("/opt/homebrew/bin/ffmpeg").is_file() else "ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe" if Path("/opt/homebrew/bin/ffprobe").is_file() else "ffprobe"

NOISE_SVG_URI = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
    "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='3' stitchTiles='stitch'/></filter>"
    "<rect width='180' height='180' filter='url(%23n)' opacity='0.55'/></svg>"
)

BASE_CSS = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  width: 1080px; height: 1920px; overflow: hidden;
  background: #060912; color: #F8FAFC;
  font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
  -webkit-font-smoothing: antialiased;
}}
.canvas {{
  position: relative; width: 1080px; height: 1920px; overflow: hidden;
  background: linear-gradient(180deg, #060912 0px, #070B16 195px, #0B101E 590px, #070B16 995px, #060912 1920px);
}}
.grid-bg {{
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(0, 240, 255, 0.038) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 240, 255, 0.038) 1px, transparent 1px);
  background-size: 48px 48px;
  -webkit-mask-image: linear-gradient(180deg, rgba(0,0,0,0.12) 0%, rgba(0,0,0,0.88) 18%, rgba(0,0,0,0.88) 48%, rgba(0,0,0,0.14) 56%, rgba(0,0,0,0.06) 100%);
}}
.stage-glow {{
  position: absolute; left: 54px; top: 210px; width: 972px; height: 766px;
  background: radial-gradient(ellipse at 50% 50%, rgba(0, 240, 255, 0.17) 0%, rgba(250, 204, 21, 0.07) 46%, transparent 72%);
}}
.grain {{
  position: absolute; inset: 0; opacity: 0.055; mix-blend-mode: overlay;
  background-image: url("{NOISE_SVG_URI}");
}}
.focal-card {{
  position: absolute; left: 96px; top: 232px; width: 888px; height: 724px;
  background: linear-gradient(168deg, rgba(16, 25, 46, 0.97) 0%, rgba(9, 14, 27, 0.99) 100%);
  border: 2px solid rgba(0, 240, 255, 0.46); border-radius: 26px;
  box-shadow: 0 26px 68px rgba(0, 0, 0, 0.82), 0 0 42px rgba(0, 240, 255, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.14);
  display: flex; flex-direction: column; overflow: hidden;
}}
.card-hdr {{
  height: 76px; padding: 0 26px; display: flex; align-items: center; justify-content: space-between;
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.15) 0%, rgba(250, 204, 21, 0.10) 100%);
  border-bottom: 1.5px solid rgba(0, 240, 255, 0.30); flex-shrink: 0;
}}
.hdr-left {{ display: flex; align-items: center; gap: 14px; }}
.dots {{ display: flex; gap: 8px; }}
.dot {{ width: 13px; height: 13px; border-radius: 50%; }}
.hdr-title {{
  font-size: 22px; font-weight: 800; letter-spacing: 1.2px; color: #00F0FF;
  text-shadow: 0 0 18px rgba(0, 240, 255, 0.38); text-transform: uppercase;
}}
.hdr-pill {{
  font-size: 20px; font-weight: 800; letter-spacing: 0.6px; color: #FACC15;
  background: rgba(250, 204, 21, 0.15); border: 1.5px solid rgba(250, 204, 21, 0.65);
  padding: 7px 16px; border-radius: 999px; white-space: nowrap;
}}
.mono {{ font-family: "Menlo", "SF Mono", monospace; }}
"""


def _first_existing(*rel_paths: str) -> Path:
    for rel in rel_paths:
        cand = REPO_ROOT / rel
        if cand.is_file():
            return cand
    raise FileNotFoundError(f"Missing required asset among: {rel_paths}")


def _file_url(path: Path) -> str:
    return path.resolve().as_uri()


def _wrap_stage_html(hdr_title: str, hdr_badge: str, body_html: str) -> str:
    t_esc = html.escape(hdr_title)
    b_esc = html.escape(hdr_badge)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"/><style>{BASE_CSS}</style></head>
<body><div class="canvas">
  <div class="grid-bg"></div>
  <div class="stage-glow"></div>
  <div class="focal-card">
    <div class="card-hdr">
      <div class="hdr-left">
        <div class="dots">
          <span class="dot" style="background:#FF5F56"></span>
          <span class="dot" style="background:#FFBD2E"></span>
          <span class="dot" style="background:#27C93F"></span>
        </div>
        <div class="hdr-title">{t_esc}</div>
      </div>
      <div class="hdr-pill">{b_esc}</div>
    </div>
    {body_html}
  </div>
  <div class="grain"></div>
</div></body></html>"""


def _capture_portal_hub(out_png: Path) -> bool:
    portal_html = REPO_ROOT / "docs" / "index.html"
    if not CHROME_BIN.is_file() or not portal_html.is_file():
        return False
    cmd = [
        str(CHROME_BIN),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--window-size=1080,1100",
        f"--screenshot={out_png}",
        f"{portal_html.resolve().as_uri()}#tab-factory",
    ]
    try:
        subprocess.run(cmd, check=True, timeout=15, capture_output=True)
        return out_png.is_file() and out_png.stat().st_size > 10_000
    except Exception:
        return False


def _load_yaml_rows() -> list[tuple[int, str, str, str]]:
    yaml_path = _first_existing("episodes/briefs/case02-part1-shaadi-qr.yaml")
    raw_lines = yaml_path.read_text(encoding="utf-8").splitlines()
    picked_indices = [1, 2, 13, 14, 15, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]
    rows: list[tuple[int, str, str, str]] = []
    for ln in picked_indices:
        if ln > len(raw_lines):
            continue
        line = raw_lines[ln - 1]
        if len(line) > 66:
            line = line[:63].rstrip() + '..."'
        indent = "&nbsp;" * (len(line) - len(line.lstrip(" ")))
        stripped = line.lstrip(" ")
        if ":" in stripped and not stripped.startswith("-"):
            k, v = stripped.split(":", 1)
            rows.append((ln, indent, k + ":", v))
        else:
            rows.append((ln, indent, stripped, ""))
    return rows


def _plate_01_portal(portal_shot: Path | None) -> str:
    tabs = ["1. Reel Factory", "2. Launch Pack", "3. IG Ops", "4. 6-Seasons", "5. Setup"]
    tab_pills = "".join(
        f'<span style="padding:6px 13px;border-radius:10px;font-size:20px;font-weight:800;'
        f'background:{"rgba(0,240,255,0.22)" if i == 0 else "rgba(255,255,255,0.06)"};'
        f'border:1.5px solid {"#00F0FF" if i == 0 else "rgba(148,163,184,0.25)"};'
        f'color:{"#00F0FF" if i == 0 else "#CBD5E1"}">{t}</span>'
        for i, t in enumerate(tabs)
    )
    if portal_shot and portal_shot.is_file():
        shot_view = (
            f'<img src="{_file_url(portal_shot)}" '
            f'style="width:100%;height:100%;object-fit:cover;object-position:50% 0%;display:block;"/>'
        )
    else:
        shot_view = (
            '<div style="padding:28px;font-size:24px;font-weight:800;color:#00F0FF;">'
            'docs/index.html#tab-factory · 6-Stage Zero-AI Reel Pipeline</div>'
        )
    body = f"""
    <div style="padding:14px 24px;background:rgba(6,10,18,0.85);border-bottom:1px solid rgba(148,163,184,0.2);display:flex;align-items:center;justify-content:space-between;">
      <div style="display:flex;gap:8px;">{tab_pills}</div>
    </div>
    <div style="margin:16px 22px 14px;flex:1;border-radius:18px;overflow:hidden;border:2px solid rgba(250,204,21,0.45);position:relative;box-shadow:0 12px 34px rgba(0,0,0,0.65);">
      {shot_view}
      <div style="position:absolute;inset:auto 0 0 0;padding:14px 20px;background:linear-gradient(180deg,transparent,rgba(6,9,18,0.96) 48%);display:flex;justify-content:space-between;align-items:center;">
        <span class="mono" style="font-size:20px;font-weight:800;color:#00F0FF;">docs/index.html#tab-factory</span>
        <span style="font-size:20px;font-weight:800;color:#10B981;">6 STAGES · 1-CLICK CLI COPY</span>
      </div>
    </div>"""
    return _wrap_stage_html("LIVE WEB HUB · 5 WORKSPACE TABS", "DARK HUB", body)


def _plate_02_yaml() -> str:
    rows = _load_yaml_rows()
    rendered_lines: list[str] = []
    for ln, indent, key_part, val_part in rows:
        k_esc = html.escape(key_part)
        v_esc = html.escape(val_part)
        if key_part.startswith("-"):
            code_span = f'<span style="color:#FACC15">{k_esc}</span>'
        else:
            v_col = "#A7F3D0" if '"' in val_part else "#F8FAFC"
            code_span = f'<span style="color:#38BDF8">{k_esc}</span><span style="color:{v_col}">{v_esc}</span>'
        rendered_lines.append(
            f'<div style="display:flex;gap:14px;line-height:1.42;">'
            f'<span style="color:#64748B;width:30px;text-align:right;flex-shrink:0;">{ln:02d}</span>'
            f'<span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{indent}{code_span}</span>'
            f'</div>'
        )
    code_block = "".join(rendered_lines)
    body = f"""
    <div class="mono" style="padding:18px 24px 12px;font-size:20px;font-weight:700;flex:1;display:flex;flex-direction:column;justify-content:space-between;">
      <div style="background:rgba(5,9,18,0.88);border:1.5px solid rgba(56,189,248,0.32);border-radius:16px;padding:16px 18px;">
        {code_block}
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 18px;border-radius:14px;background:rgba(16,185,129,0.14);border:1.5px solid rgba(16,185,129,0.5);white-space:nowrap;">
        <span style="font-size:20px;color:#F8FAFC;">case02-part1-shaadi-qr.yaml</span>
        <span style="font-size:20px;color:#10B981;font-weight:800;">compile_story_brief.py -&gt; JSON</span>
      </div>
    </div>"""
    return _wrap_stage_html("YAML STORY BRIEF", "35 LINES -> 450-LINE MANIFEST", body)


def _plate_03_autocast() -> str:
    raw_kabir = _first_existing("engine/public/characters/kabir-investigating.png")
    fg_kabir = _first_existing("engine/public/characters/fg/kabir-investigating.png")
    bg_kabir = _first_existing("engine/public/characters/bg/kabir-investigating.jpg", "engine/public/characters/kabir-investigating.png")
    body = f"""
    <div style="padding:18px 22px;flex:1;min-height:0;display:grid;grid-template-columns:1fr 1fr;gap:20px;">
      <div style="position:relative;height:100%;border-radius:18px;overflow:hidden;border:2px solid rgba(250,204,21,0.55);background:#070B14;">
        <img src="{_file_url(raw_kabir)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 18%;display:block;"/>
        <div style="position:absolute;left:50%;top:0;bottom:0;border-left:2px dashed rgba(0,240,255,0.78);"></div>
        <div style="position:absolute;left:0;right:0;top:40.1%;border-top:2.5px solid #FACC15;box-shadow:0 0 14px #FACC15;"></div>
        <div style="position:absolute;left:50%;top:40.1%;width:44px;height:44px;margin:-22px 0 0 -22px;border:3px solid #00F0FF;border-radius:50%;box-shadow:0 0 16px #00F0FF;"></div>
        <div class="mono" style="position:absolute;left:14px;top:14px;padding:6px 12px;border-radius:10px;background:rgba(6,9,18,0.92);border:1.5px solid #FACC15;font-size:20px;font-weight:800;color:#FACC15;">EYE_Y 36.5% LOCK</div>
        <div style="position:absolute;inset:auto 0 0 0;padding:18px 14px 12px;background:linear-gradient(180deg,transparent,rgba(6,9,18,0.98) 42%);font-size:20px;font-weight:900;color:#FACC15;text-align:center;">RAW PLATE -&gt; EYE_Y 36.5% LOCK</div>
      </div>
      <div style="position:relative;height:100%;border-radius:18px;overflow:hidden;border:2px solid rgba(0,240,255,0.6);background:#070D1C;">
        <img src="{_file_url(bg_kabir)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 18%;opacity:0.42;transform:scale(1.06);"/>
        <div style="position:absolute;inset:0;background-image:linear-gradient(45deg,rgba(0,240,255,0.10) 25%,transparent 25%,transparent 75%,rgba(0,240,255,0.10) 75%),linear-gradient(45deg,rgba(0,240,255,0.10) 25%,transparent 25%,transparent 75%,rgba(0,240,255,0.10) 75%);background-size:28px 28px;background-position:0 0,14px 14px;"></div>
        <img src="{_file_url(fg_kabir)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 18%;display:block;filter:drop-shadow(0 0 18px rgba(0,240,255,0.85));"/>
        <div class="mono" style="position:absolute;left:14px;top:14px;padding:6px 12px;border-radius:10px;background:rgba(6,9,18,0.92);border:1.5px solid #00F0FF;font-size:20px;font-weight:800;color:#00F0FF;">ONNX FG + BG</div>
        <div style="position:absolute;inset:auto 0 0 0;padding:18px 14px 12px;background:linear-gradient(180deg,transparent,rgba(6,9,18,0.98) 42%);font-size:20px;font-weight:900;color:#00F0FF;text-align:center;">DEPTH-ANYTHING-V2 FG + BG MATTE</div>
      </div>
    </div>"""
    return _wrap_stage_html("AUTO-CAST & 2.5D ONNX DEPTH", "1080x1920 PARALLAX", body)


def _plate_04_build_cli() -> str:
    steps = [
        ("[1/5] Compiled 35-line YAML -> schema PASS", "#10B981", "PASS", False),
        ("[2/5] Auto-Cast & 2.5D Depth Mattes -> READY", "#38BDF8", "READY", False),
        ("[3/5] Voice Self-Heal: 206.6 WPM -> 168 WPM (51.13s)", "#FACC15", "HEALED", True),
        ("[4/5] Chrome DOM Audit: 0 defects (x < 956px)", "#10B981", "0 DEFECTS", False),
        ("[5/5] Cover + Copy Pack + H.264 MP4 -> DONE", "#FACC15", "DONE", False),
    ]
    step_html = "".join(
        f'<div style="display:flex;align-items:center;justify-content:space-between;padding:13px 18px;border-radius:14px;'
        f'background:{"rgba(250,204,21,0.14)" if hi else "rgba(15,23,42,0.78)"};'
        f'border:1.5px solid {col if hi else "rgba(148,163,184,0.24)"};">'
        f'<span style="font-size:20.5px;font-weight:800;color:{"#FEF08A" if hi else "#F8FAFC"}">{html.escape(txt)}</span>'
        f'<span style="font-size:20px;font-weight:800;padding:4px 12px;border-radius:999px;color:{col};border:1.5px solid {col};">{tag}</span>'
        f'</div>'
        for txt, col, tag, hi in steps
    )
    body = f"""
    <div class="mono" style="padding:20px 24px;flex:1;display:flex;flex-direction:column;justify-content:space-between;">
      <div style="padding:15px 16px;border-radius:14px;background:#050811;border:2px solid rgba(0,240,255,0.45);font-size:19.2px;font-weight:800;color:#F8FAFC;white-space:nowrap;">
        <span style="color:#10B981">$</span> python3 scripts/build_episode.py --brief case02.yaml --render-mp4
      </div>
      <div style="display:flex;flex-direction:column;gap:11px;">{step_html}</div>
      <div style="display:flex;justify-content:space-between;padding:11px 18px;border-radius:12px;background:rgba(16,185,129,0.13);border:1.5px solid rgba(16,185,129,0.45);font-size:20px;font-weight:800;color:#A7F3D0;">
        <span>CLOCK: 51.13s (42-58s GATE)</span><span>168 WPM TARGET</span><span>EXIT 0</span>
      </div>
    </div>"""
    return _wrap_stage_html("SELF-HEALING EPISODE BUILDER", "BUILD_EPISODE.PY", body)


def _plate_05_safezone() -> str:
    preview = _first_existing(
        "renders/s01e01-preview-frame.png",
        "renders/launch-pack-case01-part1/brand-and-cover/02-case01-part1-reel-cover-1080x1920.png",
        "engine/public/characters/sharma-shock.png",
    )
    body = f"""
    <div style="padding:18px 24px;flex:1;display:grid;grid-template-columns:338px 1fr;gap:24px;align-items:stretch;">
      <div style="position:relative;border-radius:20px;overflow:hidden;border:2px solid rgba(148,163,184,0.4);background:#050811;">
        <img src="{_file_url(preview)}" style="width:100%;height:100%;object-fit:cover;display:block;"/>
        <div style="position:absolute;left:12.2%;width:75.6%;top:10%;bottom:23%;border:2.5px dashed #00F0FF;background:rgba(0,240,255,0.06);border-radius:12px;"></div>
        <div style="position:absolute;right:0;width:11.5%;top:48%;bottom:18%;background:repeating-linear-gradient(135deg,rgba(255,46,84,0.45),rgba(255,46,84,0.45) 8px,rgba(6,9,18,0.85) 8px,rgba(6,9,18,0.85) 16px);border-left:2.5px solid #FF2E54;"></div>
        <div class="mono" style="position:absolute;left:16%;bottom:26%;padding:6px 12px;border-radius:8px;background:rgba(6,9,18,0.92);border:1.5px solid #00F0FF;font-size:20px;font-weight:800;color:#00F0FF;">SAFE 816px</div>
      </div>
      <div style="display:flex;flex-direction:column;justify-content:space-between;gap:14px;">
        <div style="padding:18px 20px;border-radius:16px;background:rgba(0,240,255,0.10);border:2px solid rgba(0,240,255,0.5);">
          <div class="mono" style="font-size:23px;font-weight:900;color:#00F0FF;margin-bottom:6px;">x: 132..948 SAFE BAND</div>
          <div style="font-size:20px;line-height:1.35;color:#E2E8F0;font-weight:600;">Symmetric 816px lower stage keeps forensic cards &amp; bilingual captions unclipped.</div>
        </div>
        <div style="padding:18px 20px;border-radius:16px;background:rgba(255,46,84,0.12);border:2px solid rgba(255,46,84,0.55);">
          <div class="mono" style="font-size:23px;font-weight:900;color:#FF2E54;margin-bottom:6px;">124px IG RIGHT RAIL CLEAR</div>
          <div style="font-size:20px;line-height:1.35;color:#E2E8F0;font-weight:600;">x &gt;= 956 stays 100% clear of Like, Comment, Share &amp; Audio icons on Reels.</div>
        </div>
        <div style="padding:18px 20px;border-radius:16px;background:rgba(250,204,21,0.12);border:2px solid rgba(250,204,21,0.55);">
          <div class="mono" style="font-size:23px;font-weight:900;color:#FACC15;margin-bottom:6px;">FONT &gt;= 20px LOCK</div>
          <div style="font-size:20px;line-height:1.35;color:#E2E8F0;font-weight:600;">uat-dom-audit.mjs enforces mobile readability &amp; zero overflow before MP4 render.</div>
        </div>
      </div>
    </div>"""
    return _wrap_stage_html("NOIR_GRID SAFE-ZONE AUDITOR", "UAT:DOM 0 DEFECTS", body)


def _plate_06_launch_pack() -> str:
    dp_img = _first_existing("assets/brand/thecyberjasoos-dp-1080.png")
    cover_img = _first_existing(
        "renders/launch-pack-case01-part1/01-case01-part1-reel-cover.png",
        "renders/launch-pack-case01-part1/brand-and-cover/02-case01-part1-reel-cover-1080x1920.png",
        "renders/s01e01-reel-cover.png",
    )
    items = [
        ("MP4 Master (1080x1920 · 30fps)", "H.264 publish-ready reel", "#00F0FF"),
        ("1080x1920 Cover (3:4 Grid Safe)", "Zero profile crop loss", "#FACC15"),
        ("Pinned Poll Copy (A / B / C)", "Whodunit comment magnet", "#10B981"),
        ("AI Label ON (Meta Disclosure)", "100% monetization compliant", "#38BDF8"),
    ]
    checklist = "".join(
        f'<div style="padding:13px 16px;border-radius:14px;background:rgba(15,23,42,0.85);border:1.5px solid {c};display:flex;justify-content:space-between;align-items:center;">'
        f'<div><div style="font-size:21px;font-weight:800;color:#F8FAFC;">{t}</div>'
        f'<div style="font-size:20px;color:#94A3B8;font-weight:600;">{s}</div></div>'
        f'<span class="mono" style="font-size:20px;font-weight:900;color:{c};">READY</span></div>'
        for t, s, c in items
    )
    body = f"""
    <div style="padding:18px 24px;flex:1;min-height:0;display:grid;grid-template-columns:330px 1fr;gap:24px;align-items:stretch;">
      <div style="position:relative;height:100%;border-radius:20px;overflow:hidden;border:2px solid #FACC15;box-shadow:0 14px 36px rgba(0,0,0,0.7);">
        <img src="{_file_url(cover_img)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;"/>
        <div style="position:absolute;left:16px;bottom:16px;display:flex;align-items:center;gap:12px;padding:8px 14px 8px 8px;border-radius:999px;background:rgba(6,9,18,0.92);border:2px solid #00F0FF;">
          <img src="{_file_url(dp_img)}" style="width:58px;height:58px;border-radius:50%;border:2px solid #FACC15;object-fit:cover;"/>
          <div>
            <div style="font-size:20px;font-weight:900;color:#F8FAFC;">@cyberjasoos</div>
            <div style="font-size:20px;font-weight:800;color:#FACC15;">7:40 PM IST</div>
          </div>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;justify-content:center;gap:16px;">
        <div style="padding:14px 18px;border-radius:14px;background:linear-gradient(90deg,rgba(250,204,21,0.2),rgba(0,240,255,0.14));border:1.5px solid #FACC15;font-size:20.5px;font-weight:900;color:#FACC15;">
          AIRDROP / MAC WEB LAUNCH PACK · 7:40 PM IST
        </div>
        <div style="display:flex;flex-direction:column;gap:12px;">{checklist}</div>
      </div>
    </div>"""
    return _wrap_stage_html("LAUNCH PACK & BRAND KIT", "@CYBERJASOOS · 7:40 PM IST", body)


def _plate_07_poll_branch() -> str:
    bars = [
        ("A · Reception Wi-Fi", 15, "#64748B"),
        ("B · Smart Printer", 11, "#64748B"),
        ("C · Shagun QR Standee", 74, "#10B981"),
    ]
    bar_rows = "".join(
        f'<div style="display:grid;grid-template-columns:255px 1fr 84px;align-items:center;gap:14px;">'
        f'<span style="font-size:20px;font-weight:800;color:{"#FACC15" if p == 74 else "#CBD5E1"};">{lbl}</span>'
        f'<div style="height:22px;border-radius:999px;background:rgba(255,255,255,0.08);overflow:hidden;">'
        f'<div style="width:{p}%;height:100%;background:{col};border-radius:999px;"></div></div>'
        f'<span class="mono" style="font-size:20px;font-weight:900;color:{"#10B981" if p == 74 else "#94A3B8"};text-align:right;">{p}%</span></div>'
        for lbl, p, col in bars
    )
    body = f"""
    <div style="padding:20px 26px;flex:1;display:flex;flex-direction:column;justify-content:space-between;">
      <div style="padding:18px 22px;border-radius:18px;background:rgba(8,13,26,0.94);border:2px solid rgba(0,240,255,0.48);">
        <div class="mono" style="font-size:21px;font-weight:900;color:#00F0FF;margin-bottom:14px;">
          instagram_ops.py tally-comments -&gt; WINNER: C (74%)
        </div>
        <div style="display:flex;flex-direction:column;gap:10px;">{bar_rows}</div>
      </div>
      <div style="display:flex;align-items:center;justify-content:center;gap:16px;">
        <span class="mono" style="padding:8px 22px;border-radius:999px;background:rgba(250,204,21,0.16);border:2px solid #FACC15;font-size:20px;font-weight:900;color:#FACC15;">
          ▼  LIVE POLL BRANCH INJECTION  ▼
        </span>
      </div>
      <div style="padding:18px 22px;border-radius:18px;background:linear-gradient(135deg,rgba(16,185,129,0.16),rgba(250,204,21,0.12));border:2px solid #10B981;">
        <div class="mono" style="font-size:21px;font-weight:900;color:#A7F3D0;margin-bottom:10px;">
          apply_poll_result.py --winner C --pct 74
        </div>
        <div style="font-size:27px;font-weight:900;color:#FACC15;margin-bottom:10px;">
          &ldquo;Chauhattar percent logon ne C chuna!&rdquo;
        </div>
        <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:800;color:#F8FAFC;">
          <span>pollBranches.C AUTO-SYNCED</span>
          <span style="color:#10B981;">95% ZERO-AI PART 2</span>
        </div>
      </div>
    </div>"""
    return _wrap_stage_html("PART 1 POLL -> PART 2 REVEAL", "95% ZERO-AI PART 2", body)


def _plate_08_growth_ledger() -> str:
    defaults = [
        ('"targetDurationSec"', "51.0", "48-53s retention sweet spot", "#00F0FF"),
        ('"targetWpm"', "168", "Crisp noir thriller cadence", "#FACC15"),
        ('"preferredHookStyle"', '"mid_crime_amount"', "Rs 8.4L / 12L cold open", "#10B981"),
        ('"preferredIstHour"', '"19:40"', "7:40 PM IST prime window", "#38BDF8"),
    ]
    kv_cards = "".join(
        f'<div style="padding:14px 16px;border-radius:14px;background:rgba(6,10,20,0.9);border:1.5px solid {c};">'
        f'<div class="mono" style="font-size:20px;font-weight:800;color:#CBD5E1;">{k}: <span style="color:{c};">{v}</span></div>'
        f'<div style="font-size:20px;color:#94A3B8;font-weight:600;margin-top:4px;">{note}</div></div>'
        for k, v, note, c in defaults
    )
    body = f"""
    <div style="padding:20px 26px;flex:1;display:flex;flex-direction:column;justify-content:space-between;">
      <div style="padding:18px 22px;border-radius:18px;background:rgba(8,14,28,0.95);border:2px solid rgba(0,240,255,0.5);">
        <div style="display:flex;justify-content:space-between;margin-bottom:10px;font-size:20px;font-weight:800;color:#94A3B8;">
          <span>data/growth_ledger.sqlite3</span><span style="color:#00F0FF;">MOSSERI COMPOSITE RANK</span>
        </div>
        <div class="mono" style="font-size:26px;font-weight:900;color:#FACC15;margin-bottom:14px;">
          0.45 * Share% + 0.35 * Save% + 0.20 * Vote%
        </div>
        <div style="display:grid;grid-template-columns:45fr 35fr 20fr;gap:8px;">
          <div style="padding:8px 12px;border-radius:10px;background:rgba(0,240,255,0.22);border:1.5px solid #00F0FF;font-size:20px;font-weight:800;color:#00F0FF;">45% Share</div>
          <div style="padding:8px 12px;border-radius:10px;background:rgba(250,204,21,0.22);border:1.5px solid #FACC15;font-size:20px;font-weight:800;color:#FACC15;">35% Save</div>
          <div style="padding:8px 12px;border-radius:10px;background:rgba(16,185,129,0.22);border:1.5px solid #10B981;font-size:20px;font-weight:800;color:#10B981;">20% Vote</div>
        </div>
      </div>
      <div class="mono" style="text-align:center;font-size:20px;font-weight:900;color:#10B981;">
        ▼  instagram_ops.py learn -&gt; data/learned_defaults.json  ▼
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">{kv_cards}</div>
    </div>"""
    return _wrap_stage_html("SQLITE MOSSERI GROWTH LEDGER", "AUTO-TUNING DEFAULTS", body)


SWIFT_FALLBACK = r"""
import AppKit
import Foundation
let title = ProcessInfo.processInfo.environment["PLATE_TITLE"] ?? "CYBER JASOOS GUIDE"
let sub = ProcessInfo.processInfo.environment["PLATE_SUB"] ?? "1080x1920 NOIR STAGE"
let w = 1080, h = 1920
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8,
  samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: w * 4, bitsPerPixel: 32)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSColor(deviceRed: 6/255.0, green: 9/255.0, blue: 18/255.0, alpha: 1.0).setFill()
NSBezierPath(rect: NSRect(x: 0, y: 0, width: w, height: h)).fill()
let card = NSRect(x: 96, y: h - 956, width: 888, height: 724)
NSColor(deviceRed: 13/255.0, green: 21/255.0, blue: 38/255.0, alpha: 1.0).setFill()
let bp = NSBezierPath(roundedRect: card, xRadius: 26, yRadius: 26)
bp.fill()
NSColor(deviceRed: 0, green: 240/255.0, blue: 1.0, alpha: 0.65).setStroke()
bp.lineWidth = 3.0; bp.stroke()
let f1 = NSFont.boldSystemFont(ofSize: 34)
let f2 = NSFont.monospacedSystemFont(ofSize: 24, weight: .bold)
NSAttributedString(string: title, attributes: [.font: f1, .foregroundColor: NSColor.cyan]).draw(at: NSPoint(x: 140, y: h - 340))
NSAttributedString(string: sub, attributes: [.font: f2, .foregroundColor: NSColor.systemYellow]).draw(at: NSPoint(x: 140, y: h - 410))
NSGraphicsContext.restoreGraphicsState()
FileHandle.standardOutput.write(rep.representation(using: .png, properties: [:])!)
"""


def _render_plate(slug: str, html_doc: str, out_path: Path, fallback_label: str) -> None:
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_html = SCRATCH_DIR / f"_tmp_guide_{slug}.html"
    tmp_png = SCRATCH_DIR / f"_tmp_guide_{slug}.png"
    tmp_html.write_text(html_doc, encoding="utf-8")

    rendered_ok = False
    if CHROME_BIN.is_file():
        cmd = [
            str(CHROME_BIN),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--window-size=1080,1920",
            f"--screenshot={tmp_png}",
            tmp_html.resolve().as_uri(),
        ]
        try:
            subprocess.run(cmd, check=True, timeout=15, capture_output=True)
            rendered_ok = tmp_png.is_file() and tmp_png.stat().st_size > 20_000
        except Exception:
            rendered_ok = False

    if not rendered_ok:
        png_bytes = subprocess.check_output(
            ["swift", "-e", SWIFT_FALLBACK],
            env={**os.environ, "PLATE_TITLE": slug.upper(), "PLATE_SUB": fallback_label},
        )
        tmp_png.write_bytes(png_bytes)

    if out_path.suffix.lower() in {".jpg", ".jpeg"}:
        subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-i", str(tmp_png), "-q:v", "2", str(out_path)],
            check=True,
        )
    else:
        shutil.move(str(tmp_png), str(out_path))


def _probe_dims(path: Path) -> tuple[int, int]:
    out = subprocess.check_output(
        [
            FFPROBE,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
            str(path),
        ],
        text=True,
    ).strip()
    w_str, h_str = out.split(",")[:2]
    return int(w_str), int(h_str)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output raw plates directory")
    args = parser.parse_args(argv)

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    portal_shot = SCRATCH_DIR / "_tmp_guide_portal_hub_shot.png"

    try:
        has_shot = _capture_portal_hub(portal_shot)
        specs: list[tuple[str, str, str]] = [
            ("guide-01-portal-hub.png", _plate_01_portal(portal_shot if has_shot else None), "LIVE WEB HUB · 5 TABS"),
            ("guide-02-yaml-brief.png", _plate_02_yaml(), "35 LINES -> 450-LINE MANIFEST"),
            ("guide-03-autocast-depth.jpg", _plate_03_autocast(), "EYE_Y 36.5% + ONNX 2.5D MATTE"),
            ("guide-04-build-cli-heal.png", _plate_04_build_cli(), "BUILD_EPISODE.PY SELF-HEAL"),
            ("guide-05-safezone-stage.png", _plate_05_safezone(), "NOIR_GRID x:132..948 SAFE BAND"),
            ("guide-06-launch-pack.png", _plate_06_launch_pack(), "@CYBERJASOOS 7:40 PM IST PACK"),
            ("guide-07-poll-branch-part2.jpg", _plate_07_poll_branch(), "WINNER C 74% -> PART 2"),
            ("guide-08-growth-ledger.png", _plate_08_growth_ledger(), "SQLITE MOSSERI LEDGER"),
        ]
        for filename, html_doc, label in specs:
            dst = out_dir / filename
            _render_plate(Path(filename).stem, html_doc, dst, label)
            w, h = _probe_dims(dst)
            sz = dst.stat().st_size
            if (w, h) != (1080, 1920):
                raise RuntimeError(f"{filename}: expected 1080x1920, got {w}x{h}")
            if sz <= 40_000:
                raise RuntimeError(f"{filename}: expected > 40 KB, got {sz} bytes")
            print(f"[OK] {filename:32s}  {w}x{h}  {sz:9,d} bytes ({sz / 1024.0:6.1f} KB)")
    finally:
        for tmp in SCRATCH_DIR.glob("_tmp_guide_*"):
            tmp.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
