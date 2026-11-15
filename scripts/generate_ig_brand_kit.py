#!/usr/bin/env python3
"""Generate @cyberjasoos HD Brand Identity, Story Highlights & Grid-Safe Reel Covers."""

import argparse, json, os, re, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
REPO_ROOT = SCRIPT_DIR.parent
VENV_PYTHON = REPO_ROOT / ".venv_audio" / "bin" / "python"
try:
    import numpy as np
except ImportError:
    if VENV_PYTHON.is_file() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])
    raise

import render_instagram_ui_mockup as ui
from render_instagram_ui_mockup import circ, decode_rgb, encode_png, resolve_episode_manifest, rrect, seg, vgrad

FFMPEG = "/opt/homebrew/bin/ffmpeg" if Path("/opt/homebrew/bin/ffmpeg").is_file() else "ffmpeg"
GOLD, CRIMSON, EMERALD, CYAN, WHITE = (250, 204, 21), (225, 29, 72), (16, 185, 129), (56, 189, 248), (248, 250, 252)
NOIR_BG, NOIR_CARD = (6, 9, 18), (11, 16, 30)

SWIFT_TYPO = r"""
import AppKit
import Foundation
struct Item: Decodable {
  let text: String; let x: Double; let y: Double; let size: Double
  let font: String; let rgb: [Double]; let maxW: Double; let center: Bool; let kern: Double
}
struct Payload: Decodable { let w: Int; let h: Int; let items: [Item] }
let p = try! JSONDecoder().decode(Payload.self, from: Data(ProcessInfo.processInfo.environment["TYPO_JSON"]!.utf8))
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: p.w, pixelsHigh: p.h, bitsPerSample: 8,
  samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: p.w * 4, bitsPerPixel: 32)!
rep.size = NSSize(width: p.w, height: p.h)
if let ptr = rep.bitmapData { memset(ptr, 0, p.w * p.h * 4) }
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
for it in p.items {
  var pt = CGFloat(it.size)
  let col = NSColor(deviceRed: it.rgb[0]/255.0, green: it.rgb[1]/255.0, blue: it.rgb[2]/255.0, alpha: 1.0)
  let shCol = NSColor(deviceRed: 0, green: 0, blue: 0, alpha: 0.86)
  var f = NSFont(name: it.font, size: pt) ?? NSFont.boldSystemFont(ofSize: pt)
  var attrs: [NSAttributedString.Key: Any] = [.font: f, .foregroundColor: col, .kern: it.kern]
  while pt > 20 && NSAttributedString(string: it.text, attributes: attrs).size().width > CGFloat(it.maxW) {
    pt -= 2; f = NSFont(name: it.font, size: pt) ?? NSFont.boldSystemFont(ofSize: pt); attrs[.font] = f
  }
  let fg = NSAttributedString(string: it.text, attributes: attrs)
  let sh = NSAttributedString(string: it.text, attributes: [.font: f, .foregroundColor: shCol, .kern: it.kern])
  let sz = fg.size()
  let dx = it.center ? CGFloat(it.x) - sz.width * 0.5 : CGFloat(it.x)
  let dy = CGFloat(p.h) - CGFloat(it.y) - sz.height
  sh.draw(at: NSPoint(x: dx + 3.0, y: dy - 4.0)); sh.draw(at: NSPoint(x: dx - 1.5, y: dy - 1.5))
  fg.draw(at: NSPoint(x: dx, y: dy))
}
NSGraphicsContext.restoreGraphicsState()
FileHandle.standardOutput.write(rep.representation(using: .png, properties: [:])!)
"""


def _txt(text: str, y: float, size: float, rgb: tuple[int, int, int] = WHITE, x: float = 540, max_w: float = 620, font: str = "HelveticaNeue-CondensedBlack", kern: float = 2.0) -> dict:
    return {"text": text, "x": x, "y": y, "size": size, "font": font, "rgb": list(rgb), "maxW": max_w, "center": True, "kern": kern}


def overlay_typography(img: np.ndarray, items: list[dict]) -> None:
    ih, iw = img.shape[:2]
    png_bytes = subprocess.check_output(["swift", "-e", SWIFT_TYPO], env={**os.environ, "TYPO_JSON": json.dumps({"w": iw, "h": ih, "items": items})})
    raw = subprocess.check_output([FFMPEG, "-v", "error", "-i", "-", "-f", "rawvideo", "-pix_fmt", "rgba", "-"], input=png_bytes)
    rgba = np.frombuffer(raw, dtype=np.uint8).reshape((ih, iw, 4)).astype(np.float32)
    alpha = rgba[..., 3:4] / 255.0
    img[:] = img * (1.0 - alpha) + rgba[..., :3] * alpha


def _with_canvas(img: np.ndarray, fn) -> None:
    old_w, old_h = ui.W, ui.H
    ui.W, ui.H = img.shape[1], img.shape[0]
    try:
        fn()
    finally:
        ui.W, ui.H = old_w, old_h


def build_profile_avatars() -> tuple[Path, Path]:
    src = decode_rgb(REPO_ROOT / "engine/public/characters/kabir-closeup.png", 1080, 1920)
    # Eyes sit at y=780 in 1080x1920; cropping y=326..1406 places eyes at 454/1080 = 42.0% with full chin & collar
    sq = src[326:1406, :, :].copy()
    yy, xx = np.mgrid[0:1080, 0:1080]
    dist = np.hypot(xx - 540.0, yy - 540.0)
    vig = np.clip((dist - 435.0) / 105.0, 0.0, 1.0) ** 1.35 * 0.78
    outer_mask = np.clip((dist - 525.0) / 8.0, 0.0, 1.0) * 0.88
    dark = np.maximum(vig, outer_mask)[..., None]
    sq[:] = sq * (1.0 - dark) + np.array(NOIR_BG, dtype=np.float32) * dark

    def _draw_rings() -> None:
        circ(sq, 540, 540, 514, CRIMSON, a=0.24, stroke=22.0)
        circ(sq, 540, 540, 520, CRIMSON, a=0.98, stroke=6.0)
        circ(sq, 540, 540, 508, GOLD, a=0.98, stroke=6.0)

    _with_canvas(sq, _draw_rings)
    dp_out = REPO_ROOT / "assets/brand/thecyberjasoos-dp-1080.png"
    encode_png(sq, dp_out)
    avatar_out = REPO_ROOT / "engine/public/brand/kabir-avatar.png"
    avatar_out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-i", str(dp_out), "-vf", "scale=512:512:flags=lanczos,unsharp=3:3:0.35:3:3:0.0", "-pix_fmt", "rgb24", str(avatar_out)],
        check=True,
    )
    return dp_out, avatar_out


def _highlight_base(accent: tuple[int, int, int]) -> np.ndarray:
    yy, xx = np.mgrid[0:1920, 0:1080]
    dist = np.hypot(xx - 540.0, yy - 960.0)
    img = np.broadcast_to(np.array(NOIR_BG, dtype=np.float32), (1920, 1080, 3)).copy()
    glow = np.clip(1.0 - dist / 640.0, 0.0, 1.0) ** 2.0 * 0.28
    img[:] = img * (1.0 - glow[..., None]) + np.array(accent, dtype=np.float32) * glow[..., None]
    circ(img, 540, 960, 426, accent, a=0.22, stroke=26.0)
    circ(img, 540, 960, 430, accent, a=0.98, stroke=8.0)
    circ(img, 540, 960, 412, GOLD, a=0.95, stroke=6.0)
    circ(img, 540, 960, 398, NOIR_CARD, a=0.92)
    circ(img, 540, 960, 376, GOLD, a=0.24, stroke=2.5)
    return img


def build_highlight_covers() -> list[Path]:
    out_dir, foot = REPO_ROOT / "assets/brand", _txt("@CYBERJASOOS", 1560, 28, (148, 163, 184), font="HelveticaNeue-Bold", kern=3.0)
    outputs: list[Path] = []

    img = _highlight_base(CRIMSON)
    rrect(img, 418, 706, 200, 248, 20, (22, 31, 54), a=0.98)
    rrect(img, 418, 706, 200, 248, 20, GOLD, a=0.92, stroke=5.5)
    rrect(img, 444, 738, 92, 24, 8, CRIMSON, a=0.95)
    for ry, rw in [(786, 144), (814, 128), (842, 106)]:
        rrect(img, 444, ry, rw, 11, 5, (148, 163, 184), a=0.85)
    circ(img, 594, 868, 66, (12, 19, 36), a=0.96); circ(img, 594, 868, 66, GOLD, a=0.99, stroke=11.0)
    circ(img, 594, 868, 46, CYAN, a=0.55, stroke=4.0, a_deg=(200, 310))
    seg(img, 642, 916, 696, 970, 16.0, CRIMSON, a=0.99); seg(img, 640, 914, 692, 966, 9.0, GOLD, a=0.98)
    overlay_typography(img, [_txt("CASE FILES", 1030, 76, kern=2.2), foot])
    p1 = out_dir / "highlight-cases.png"; encode_png(img, p1); outputs.append(p1)

    img = _highlight_base(CRIMSON)
    for cx, cy, col in [(356, 756, CRIMSON), (480, 720, GOLD), (604, 756, CYAN)]:
        rrect(img, cx, cy, 120, 174, 22, (18, 26, 46), a=0.98)
        rrect(img, cx, cy, 120, 174, 22, col, a=0.98, stroke=6.5)
    overlay_typography(img, [_txt("A", 786, 92, CRIMSON, x=416, max_w=100, kern=0), _txt("B", 750, 96, GOLD, x=540, max_w=100, kern=0), _txt("C", 786, 92, CYAN, x=664, max_w=100, kern=0), _txt("A / B / C POLLS", 1026, 72, kern=1.8), foot])
    p2 = out_dir / "highlight-polls.png"; encode_png(img, p2); outputs.append(p2)

    img = _highlight_base(EMERALD)
    pts = [(540, 692), (668, 742), (650, 886), (540, 976), (430, 886), (412, 742)]
    ipts = [(540, 720), (640, 760), (626, 874), (540, 946), (454, 874), (440, 760)]
    for i in range(6):
        seg(img, pts[i][0], pts[i][1], pts[(i + 1) % 6][0], pts[(i + 1) % 6][1], 11.0, EMERALD, a=0.98)
        seg(img, ipts[i][0], ipts[i][1], ipts[(i + 1) % 6][0], ipts[(i + 1) % 6][1], 4.5, GOLD, a=0.92)
    seg(img, 488, 838, 526, 878, 15.0, GOLD, a=0.99); seg(img, 526, 878, 598, 792, 15.0, GOLD, a=0.99)
    overlay_typography(img, [_txt("5s KAVACH", 1026, 76, kern=2.0), foot])
    p3 = out_dir / "highlight-kavach.png"; encode_png(img, p3); outputs.append(p3)

    img = _highlight_base(CRIMSON)
    rrect(img, 366, 734, 348, 198, 42, (34, 14, 28), a=0.96); rrect(img, 366, 734, 348, 198, 42, CRIMSON, a=0.98, stroke=8.0)
    circ(img, 540, 704, 54, GOLD, a=0.88, stroke=5.5, a_deg=(205, 335)); circ(img, 540, 704, 82, CRIMSON, a=0.72, stroke=5.0, a_deg=(212, 328))
    overlay_typography(img, [_txt("1930", 764, 122, GOLD, max_w=320, kern=3.0), _txt("1930 HELP", 1026, 76, kern=2.2), foot])
    p4 = out_dir / "highlight-1930.png"; encode_png(img, p4); outputs.append(p4)
    return outputs


def build_reel_cover(episode_path: Path | str, frame_path: Path | str, out_path: Path | str) -> Path:
    ep_file = Path(episode_path) if Path(episode_path).is_absolute() else REPO_ROOT / episode_path
    fr_file = Path(frame_path) if Path(frame_path).is_absolute() else REPO_ROOT / frame_path
    out_file = Path(out_path) if Path(out_path).is_absolute() else REPO_ROOT / out_path
    manifest = resolve_episode_manifest(ep_file, fr_file) or {}

    img = decode_rgb(fr_file, 1080, 1920)
    vgrad(img, 0, 560, 0.56, 0.0, NOIR_BG); vgrad(img, 980, 1520, 0.0, 0.88, NOIR_BG); vgrad(img, 1520, 1920, 0.88, 0.96, NOIR_BG)

    m_case = re.search(r"(?:CASE|GUIDE)\s*#\d+", f"{manifest.get('securityDomain', '')} {manifest.get('seasonTitle', '')}", re.I)
    hud_badge = str(manifest.get("hudPartBadge") or "PART 1/2").upper()
    is_guide_ep = hud_badge.startswith("GUIDE") or "GUIDE" in str(manifest.get("id", "")).upper()
    case_label = m_case.group(0).upper() if m_case else ("AUTO FACTORY" if is_guide_ep else f"CASE #{int(manifest.get('season') or 1):02d}")
    prev_vote = (manifest.get("hook") or {}).get("previousVoteResult") or {}
    is_finale = "FINALE" in str(manifest.get("securityDomain", "")).upper() or hud_badge.startswith("PART 2") or bool(prev_vote)

    top_pill = f"{case_label} · {hud_badge}" if is_guide_ep else (f"{case_label} · FINALE" if is_finale else f"{case_label} · {hud_badge}")
    pill_fill = (8, 92, 68) if (is_finale or is_guide_ep) else CRIMSON
    rrect(img, 290, 318, 500, 62, 31, pill_fill, a=0.95); rrect(img, 290, 318, 500, 62, 31, GOLD, a=0.95, stroke=3.2)

    parts = [s.strip() for s in str(manifest.get("coldOpenTag") or manifest.get("episodeTitle") or "CYBER CASE").split("·") if s.strip()]
    if manifest.get("id") == "s01e02-crown-jewels" and prev_vote.get("percentage"):
        h1, h2 = f"{int(prev_vote['percentage'])}% KA SHAK GALAT NIKLA!", "CHHAT KA ASLI GADDAR REVEAL"
    elif is_finale and prev_vote.get("percentage"):
        opt = str(prev_vote.get("winningOption") or "C").upper()
        h1 = f"{int(prev_vote['percentage'])}% VOTED OPTION {opt}!"
        h2 = (parts[-1].upper() if len(parts) > 1 else str(manifest.get("episodeTitle") or "ASLI FORENSIC SACH REVEAL").upper())[:36]
    elif "12 lakh" in f"{manifest.get('seasonTitle', '')} {manifest.get('coldOpenTag', '')}".lower():
        h1, h2 = "SHAADI KE 12 LAKH GAYAB!", "ASLI GADDAR: A, B YA C?"
    else:
        default_h2 = "ZERO-AI PIPELINE GUIDE" if is_guide_ep else ("FULL FORENSIC REVEAL" if is_finale else "ASLI GADDAR: A, B YA C?")
        h1, h2 = f"{parts[0].upper()}!", (parts[1].upper() if len(parts) > 1 else default_h2)

    follow_blob = json.dumps(manifest.get("scenes") or [])
    m_handle = re.search(r"@[A-Za-z0-9_.]+", follow_blob)
    handle_label = m_handle.group(0).upper() if m_handle else "@CYBERJASOOS"

    rrect(img, 118, 1188, 844, 258, 28, NOIR_CARD, a=0.84)
    rrect(img, 118, 1188, 844, 258, 28, GOLD if is_finale else CRIMSON, a=0.92, stroke=3.5)
    seg(img, 180, 1372, 900, 1372, 2.0, (71, 85, 105), a=0.65)
    overlay_typography(img, [
        _txt(top_pill, 329, 34, max_w=460, kern=2.2),
        _txt(h1, 1204, 74, max_w=804, kern=1.0),
        _txt(h2, 1296, 50, GOLD, max_w=804, kern=1.4),
        _txt(handle_label, 1386, 31, (226, 232, 240), font="HelveticaNeue-Bold", kern=3.2),
    ])
    encode_png(img, out_file)
    return out_file


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate @cyberjasoos Brand Kit & Grid-Safe Reel Covers")
    ap.add_argument("--all", action="store_true", help="Generate full brand kit, highlights, and default Reel covers")
    ap.add_argument("--episode", help="Episode JSON path for single Reel cover build")
    ap.add_argument("--frame", help="Source 1080x1920 character/frame PNG for single Reel cover build")
    ap.add_argument("--output", help="Output 1080x1920 Reel cover PNG path")
    args = ap.parse_args()
    if args.episode or args.frame or args.output:
        if not (args.episode and args.frame and args.output):
            ap.error("--episode, --frame, and --output must be provided together")
        out = build_reel_cover(args.episode, args.frame, args.output)
        print(f"Generated Reel cover -> {out}")
        return 0
    dp, av = build_profile_avatars()
    hl = build_highlight_covers()
    c1 = build_reel_cover("episodes/s01-asset-classification/s01e01-forgotten-bucket.json", "engine/public/characters/sharma-shock.png", "renders/s01e01-reel-cover.png")
    c2 = build_reel_cover("episodes/s01-asset-classification/s01e02-crown-jewels.json", "engine/public/characters/pappu-chachu.png", "renders/s01e02-reel-cover.png")
    print(f"Brand kit complete: {dp.name}, {av.name}, {len(hl)} highlights, {c1.name}, {c2.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
