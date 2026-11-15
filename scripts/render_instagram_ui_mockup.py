#!/usr/bin/env python3
"""Render realistic translucent Instagram Reels Mobile UI overlays onto a 1080x1920 frame."""

import argparse, json, math, os, re, subprocess, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = REPO_ROOT / ".venv_audio" / "bin" / "python"
try:
    import numpy as np
except ImportError:
    if VENV_PYTHON.is_file() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])
    raise

W, H = 1080, 1920
RIGHT_RAIL_X = 956
CAPTION_X = 58
CAPTION_SCALE = 3
MAX_CAPTION_CHARS = 48  # 58 + 48 * 18 = 922px (< 956px iPhone right action rail -> 0% overlap)
DEFAULT_CAPTION_1 = "Har cyber scam ke peeche ek forensic clue hai!"
DEFAULT_CAPTION_2 = "Aapka shaq kis par hai? Comment A, B, C... more"
GLYPHS: dict[str, str] = {
    "A": "EHHVHHH", "B": "UHHUHHU", "C": "EHGGGHE", "D": "UHHHHHU", "E": "VGGUGGV",
    "F": "VGGUGGG", "G": "EHGNHHF", "H": "HHHVHHH", "I": "E44444E", "J": "7222IIC",
    "K": "HIKOKIH", "L": "GGGGGGV", "M": "HRLLHHH", "N": "HPLJHHH", "O": "EHHHHHE",
    "P": "UHHUGGG", "Q": "EHHHLID", "R": "UHHUKIH", "S": "FGGE11U", "T": "V444444",
    "U": "HHHHHHE", "V": "HHHHHA4", "W": "HHHLLRH", "X": "HHA4AHH", "Y": "HHA4444",
    "Z": "V1248GV", "0": "EHJLPHE", "1": "4C4444E", "2": "EH168GV", "3": "U11E11U",
    "4": "26AIV22", "5": "VGU11HE", "6": "EGGUHHE", "7": "V124888", "8": "EHHEHHE",
    "9": "EHHF11E", "a": "00E1FHF", "b": "GGUHHHU", "c": "00EHGHE", "d": "11FHHHF",
    "e": "00EHVGE", "f": "68U8888", "g": "00FHHFE", "h": "GGUHHHH", "i": "40C444E",
    "j": "20622IC", "k": "GGIKOKI", "l": "C44444E", "m": "00QLLLH", "n": "00UHHHH",
    "o": "00EHHHE", "p": "00UHHUG", "q": "00FHHF1", "r": "00MPGGG", "s": "00FGE1U",
    "t": "88U8896", "u": "00HHHHF", "v": "00HHHA4", "w": "00HLLRH", "x": "00HA4AH",
    "y": "00HHHFE", "z": "00V248V", ".": "0000066", ",": "0000624", ":": "0660660",
    "·": "0006600", "-": "000E000", "!": "4444404", "?": "EH16404", "@": "EHJNHGE",
    "#": "AVAVAVA", "%": "PQ248BJ", "/": "122488G", "(": "2488842", ")": "8422248",
    "'": "4400000", "+": "044V440", "*": "0A4V4A0", "=": "00V0V00",
}
_GLYPH_CACHE: dict[tuple[str, int], np.ndarray] = {}


def decode_rgb(path: Path, w: int, h: int) -> np.ndarray:
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    )
    return np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3)).astype(np.float32)


def encode_png(img: np.ndarray, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ih, iw = img.shape[:2]
    buf = np.clip(np.rint(img), 0, 255).astype(np.uint8).tobytes()
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{iw}x{ih}", "-i", "-", str(out_path)],
        input=buf,
        check=True,
    )


def blend(img: np.ndarray, x0: int, y0: int, mask: np.ndarray, rgb: tuple[int, int, int]) -> None:
    mh, mw = mask.shape
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(W, x0 + mw), min(H, y0 + mh)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    sub = mask[cy0 - y0 : cy1 - y0, cx0 - x0 : cx1 - x0][..., None]
    roi = img[cy0:cy1, cx0:cx1]
    roi[:] = roi * (1.0 - sub) + np.array(rgb, dtype=np.float32) * sub


def vgrad(img: np.ndarray, y0: int, y1: int, a0: float, a1: float, rgb: tuple[int, int, int] = (4, 6, 12)) -> None:
    ys = np.linspace(a0, a1, y1 - y0, dtype=np.float32)[:, None, None]
    img[y0:y1] = img[y0:y1] * (1.0 - ys) + np.array(rgb, dtype=np.float32) * ys


def rrect(img: np.ndarray, x: float, y: float, w: float, h: float, r: float, rgb: tuple[int, int, int], a: float = 1.0, stroke: float = 0.0, dash: int = 0) -> None:
    pad = int(math.ceil(stroke + 3))
    x0, y0, x1, y1 = max(0, int(x) - pad), max(0, int(y) - pad), min(W, int(x + w) + pad), min(H, int(y + h) + pad)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    qx = np.abs(xx - (x + w * 0.5)) - (w * 0.5 - r)
    qy = np.abs(yy - (y + h * 0.5)) - (h * 0.5 - r)
    d = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0)) + np.minimum(np.maximum(qx, qy), 0.0) - r
    cov = np.clip(0.5 - (np.abs(d) - stroke * 0.5 if stroke > 0 else d), 0.0, 1.0) * a
    if dash > 0:
        cov *= (((xx + yy) // dash) % 2 == 0).astype(np.float32)
    blend(img, x0, y0, cov, rgb)


def circ(img: np.ndarray, cx: float, cy: float, r: float, rgb: tuple[int, int, int], a: float = 1.0, stroke: float = 0.0, a_deg: tuple[float, float] | None = None) -> None:
    pad = int(math.ceil(r + stroke + 3))
    x0, y0, x1, y1 = max(0, int(cx) - pad), max(0, int(cy) - pad), min(W, int(cx) + pad), min(H, int(cy) + pad)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dx, dy = xx - cx, yy - cy
    d = np.hypot(dx, dy) - r
    cov = np.clip(0.5 - (np.abs(d) - stroke * 0.5 if stroke > 0 else d), 0.0, 1.0) * a
    if a_deg is not None:
        ang = (np.degrees(np.arctan2(dy, dx)) + 360.0) % 360.0
        s, e = a_deg[0] % 360.0, a_deg[1] % 360.0
        inside = (ang >= s) & (ang <= e) if s <= e else (ang >= s) | (ang <= e)
        cov *= inside.astype(np.float32)
    blend(img, x0, y0, cov, rgb)


def seg(img: np.ndarray, x1: float, y1: float, x2: float, y2: float, w: float, rgb: tuple[int, int, int], a: float = 1.0) -> None:
    pad = int(math.ceil(w + 3))
    bx0, by0 = max(0, int(min(x1, x2)) - pad), max(0, int(min(y1, y2)) - pad)
    bx1, by1 = min(W, int(max(x1, x2)) + pad), min(H, int(max(y1, y2)) + pad)
    yy, xx = np.mgrid[by0:by1, bx0:bx1]
    px, py, vx, vy = xx - x1, yy - y1, x2 - x1, y2 - y1
    t = np.clip((px * vx + py * vy) / max(1e-6, vx * vx + vy * vy), 0.0, 1.0)
    cov = np.clip(0.5 - (np.hypot(px - t * vx, py - t * vy) - w * 0.5), 0.0, 1.0) * a
    blend(img, bx0, by0, cov, rgb)


def glyph_mask(ch: str, scale: int) -> np.ndarray:
    key = (ch, scale)
    if key in _GLYPH_CACHE:
        return _GLYPH_CACHE[key]
    code = GLYPHS.get(ch) or GLYPHS.get(ch.upper(), "0000000")
    grid = np.zeros((9, 7), dtype=np.float32)
    for r_idx, rc in enumerate(code):
        bits = int(rc, 32)
        for c_idx in range(5):
            grid[r_idx + 1, c_idx + 1] = float((bits >> (4 - c_idx)) & 1)
    oh, ow = 9 * scale, 7 * scale
    ys = np.clip((np.arange(oh, dtype=np.float32) + 0.5) / scale - 0.5, 0, 8)
    xs = np.clip((np.arange(ow, dtype=np.float32) + 0.5) / scale - 0.5, 0, 6)
    y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
    y1, x1 = np.minimum(y0 + 1, 8), np.minimum(x0 + 1, 6)
    wy, wx = (ys - y0)[:, None], (xs - x0)[None, :]
    up = (1 - wy) * ((1 - wx) * grid[y0[:, None], x0[None, :]] + wx * grid[y0[:, None], x1[None, :]]) + wy * (
        (1 - wx) * grid[y1[:, None], x0[None, :]] + wx * grid[y1[:, None], x1[None, :]]
    )
    res = np.clip((up - 0.31) * 3.6, 0.0, 1.0) if scale >= 2 else up
    _GLYPH_CACHE[key] = res
    return res


def draw_text(img: np.ndarray, text: str, x: int, y: int, scale: int = 3, rgb: tuple[int, int, int] = (255, 255, 255), a: float = 0.96, shadow: bool = True, center: bool = False) -> int:
    adv = 6 * scale
    tw = len(text) * adv
    cx = x - tw // 2 if center else x
    for ch in text:
        if ch != " ":
            m = glyph_mask(ch, scale)
            if shadow:
                blend(img, cx + 1, y + 2, m * (a * 0.55), (0, 0, 0))
            blend(img, cx, y, m * a, rgb)
        cx += adv
    return tw


def dashed_seg(
    img: np.ndarray,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    w: float,
    rgb: tuple[int, int, int],
    a: float = 1.0,
    dash: float = 12.0,
) -> None:
    length = math.hypot(x2 - x1, y2 - y1)
    if length <= 1e-6:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end = min(length, pos + dash)
        seg(img, x1 + ux * pos, y1 + uy * pos, x1 + ux * end, y1 + uy * end, w, rgb, a)
        pos += dash * 2.0


def draw_notched_safe_envelope(img: np.ndarray) -> None:
    # Exact notched iPhone Reels safe envelope: x:80..1000 for y:192..1015, stepping to x:80..956 for y:1015..1480
    pts = [
        (80.0, 192.0),
        (1000.0, 192.0),
        (1000.0, 1015.0),
        (956.0, 1015.0),
        (956.0, 1480.0),
        (80.0, 1480.0),
    ]
    emerald = (34, 197, 94)
    for idx in range(len(pts)):
        x1, y1 = pts[idx]
        x2, y2 = pts[(idx + 1) % len(pts)]
        dashed_seg(img, x1, y1, x2, y2, 2.2, emerald, a=0.58, dash=12.0)


def draw_right_rail_icons(img: np.ndarray, avatar_path: Path) -> None:
    # Authentic iPhone 390pt -> 1080px right action rail: x: 956..1080 (124px), y: 1020..1580, centerX = 1018
    cx, col, sh = 1018.0, (255, 255, 255), (0, 0, 0)

    # 1. Like / Heart (52px icon centered around y=1045) + count "48.2K"
    for dx, dy, c, al in [(1.8, 2.8, sh, 0.44), (0.0, 0.0, col, 0.96)]:
        circ(img, cx - 12.0 + dx, 1037 + dy, 13.5, c, al, stroke=3.8, a_deg=(138, 355))
        circ(img, cx + 12.0 + dx, 1037 + dy, 13.5, c, al, stroke=3.8, a_deg=(185, 42))
        seg(img, cx - 22.8 + dx, 1046 + dy, cx + dx, 1070 + dy, 3.8, c, al)
        seg(img, cx + 22.8 + dx, 1046 + dy, cx + dx, 1070 + dy, 3.8, c, al)
    draw_text(img, "48.2K", int(cx), 1080, scale=3, a=0.96, center=True)

    # 2. Comment bubble (52px icon centered at y=1185) + count "6,410"
    for dx, dy, c, al in [(1.8, 2.8, sh, 0.44), (0.0, 0.0, col, 0.96)]:
        circ(img, cx + dx, 1183 + dy, 23.5, c, al, stroke=3.8, a_deg=(76, 36))
        seg(img, cx + 18.8 + dx, 1196 + dy, cx + 25.0 + dx, 1210 + dy, 3.6, c, al)
        seg(img, cx + 5.6 + dx, 1206 + dy, cx + 25.0 + dx, 1210 + dy, 3.6, c, al)
    draw_text(img, "6,410", int(cx), 1220, scale=3, a=0.96, center=True)

    # 3. Share / Paper-plane (52px icon centered at y=1325) + count "19.4K"
    for dx, dy, c, al in [(1.8, 2.8, sh, 0.44), (0.0, 0.0, col, 0.96)]:
        pts = [
            (cx - 24.0 + dx, 1311 + dy),
            (cx + 24.0 + dx, 1305 + dy),
            (cx + 4.0 + dx, 1348 + dy),
            (cx - 4.0 + dx, 1326 + dy),
        ]
        for i in range(4):
            seg(img, pts[i][0], pts[i][1], pts[(i + 1) % 4][0], pts[(i + 1) % 4][1], 3.6, c, al)
        seg(img, pts[3][0], pts[3][1], pts[1][0], pts[1][1], 3.1, c, al)
    draw_text(img, "19.4K", int(cx), 1358, scale=3, a=0.96, center=True)

    # 4. Save Bookmark + More dots around y=1450
    for dx, dy, c, al in [(1.8, 2.8, sh, 0.44), (0.0, 0.0, col, 0.96)]:
        seg(img, cx - 18.5 + dx, 1418 + dy, cx + 18.5 + dx, 1418 + dy, 3.6, c, al)
        seg(img, cx - 18.5 + dx, 1418 + dy, cx - 18.5 + dx, 1468 + dy, 3.6, c, al)
        seg(img, cx + 18.5 + dx, 1418 + dy, cx + 18.5 + dx, 1468 + dy, 3.6, c, al)
        seg(img, cx - 18.5 + dx, 1468 + dy, cx + dx, 1451 + dy, 3.6, c, al)
        seg(img, cx + 18.5 + dx, 1468 + dy, cx + dx, 1451 + dy, 3.6, c, al)
    for ox in (-12, 0, 12):
        circ(img, cx + ox, 1490, 3.2, col, 0.94)

    # 5. 50x50 Audio Disc centered at y=1535 (y: 1510..1560, x: 993..1043)
    ax, ay = int(cx - 25), 1510
    if avatar_path.is_file():
        img[ay : ay + 50, ax : ax + 50] = decode_rgb(avatar_path, 50, 50) * 0.86
    else:
        rrect(img, ax, ay, 50, 50, 12, (28, 16, 26), 0.95)
    rrect(img, ax, ay, 50, 50, 12, (255, 255, 255), 0.96, stroke=2.8)
    circ(img, cx, ay + 25, 7.5, (12, 16, 26), 0.92)
    circ(img, cx, ay + 25, 3.0, (250, 204, 21), 0.96)


def _sanitize_glyph_text(raw: str) -> str:
    txt = (
        raw.replace("₹", "Rs ")
        .replace("—", " - ")
        .replace("–", "-")
        .replace("…", "...")
        .replace("’", "'")
        .replace("‘", "'")
        .replace("“", " ")
        .replace("”", " ")
        .replace('"', " ")
    )
    cleaned = "".join(ch if (ch == " " or ch in GLYPHS or ch.upper() in GLYPHS) else " " for ch in txt)
    return re.sub(r"\s+", " ", cleaned).strip()


def _clamp_caption_line(line: str, max_chars: int = MAX_CAPTION_CHARS, with_more: bool = False) -> str:
    clean = _sanitize_glyph_text(line)
    if not clean:
        return ""
    suffix = "... more" if with_more else ""
    if len(clean) + len(suffix) <= max_chars:
        return f"{clean}{suffix}" if (suffix and not clean.lower().endswith("more")) else clean
    budget = max(8, max_chars - (len(suffix) if suffix else 3))
    cut = clean[:budget].rsplit(" ", 1)[0] if " " in clean[:budget] else clean[:budget]
    cut = cut.rstrip(" .,-:·!?")
    return f"{cut}{suffix or '...'}"[:max_chars]


def resolve_episode_manifest(episode_arg: str | Path | None, input_png: Path | None = None) -> dict | None:
    candidates: list[Path] = []
    if episode_arg:
        ep_p = Path(episode_arg)
        candidates.append(ep_p if ep_p.is_absolute() else REPO_ROOT / ep_p)
    elif input_png is not None:
        m = re.search(r"(s\d{2}e\d{2})", input_png.name, flags=re.IGNORECASE)
        if m:
            prefix = m.group(1).lower()
            ep_root = REPO_ROOT / "episodes"
            if ep_root.is_dir():
                for p in sorted(ep_root.glob("*/*.json")) + sorted(ep_root.glob("*.json")):
                    if p.name != "schema.json" and p.name.lower().startswith(prefix):
                        candidates.append(p)
    for cand in candidates:
        try:
            if cand.is_file():
                data = json.loads(cand.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
        except (OSError, ValueError):
            continue
    return None


def extract_instagram_caption_lines(
    manifest: dict | None,
    max_chars: int = MAX_CAPTION_CHARS,
) -> tuple[str, str]:
    raw_caption = ""
    if isinstance(manifest, dict):
        post_copy = manifest.get("postCopy")
        if isinstance(post_copy, dict):
            raw_caption = str(post_copy.get("instagramCaption") or "")
    raw_lines = [ln.strip() for ln in raw_caption.splitlines() if ln.strip()]
    prose_lines = [ln for ln in raw_lines if not ln.startswith("#")] or raw_lines
    sanitized = [_sanitize_glyph_text(ln) for ln in prose_lines]
    sanitized = [ln for ln in sanitized if ln]
    if not sanitized:
        return (
            _clamp_caption_line(DEFAULT_CAPTION_1, max_chars=max_chars),
            _clamp_caption_line(DEFAULT_CAPTION_2, max_chars=max_chars),
        )
    if len(sanitized) == 1 and len(sanitized[0]) > max_chars:
        words = sanitized[0].split(" ")
        line1_words: list[str] = []
        idx = 0
        while idx < len(words) and len(" ".join(line1_words + [words[idx]])) <= max_chars:
            line1_words.append(words[idx])
            idx += 1
        first = " ".join(line1_words) if line1_words else sanitized[0][:max_chars]
        rest = " ".join(words[idx:])
        return (
            _clamp_caption_line(first, max_chars=max_chars),
            _clamp_caption_line(rest or DEFAULT_CAPTION_2, max_chars=max_chars, with_more=True),
        )
    first_line = _clamp_caption_line(sanitized[0], max_chars=max_chars)
    second_raw = " · ".join(sanitized[1:]) if len(sanitized) > 1 else DEFAULT_CAPTION_2
    has_extra = len(sanitized) > 2 or len(second_raw) > max_chars - 8
    second_line = _clamp_caption_line(second_raw, max_chars=max_chars, with_more=has_extra)
    return first_line, second_line


def measure_right_rail_overlap_pct(frame_rgb: np.ndarray, caption_right_x: int = 0) -> int | float:
    """Measure UI card / glyph pixel intrusion into x >= 956 (y: 1000..1460) plus caption rail intrusion."""
    rail_w = max(1, W - RIGHT_RAIL_X)
    cap_intrusion_px = max(0, int(caption_right_x) - RIGHT_RAIL_X)
    cap_pct = (cap_intrusion_px / float(rail_w)) * 100.0

    rail = frame_rgb[1000:1460, RIGHT_RAIL_X:W]
    left_bg = frame_rgb[1000:1460, 0:48]
    right_edge = frame_rgb[1000:1460, 1052:W]
    rail_lum = 0.2126 * rail[..., 0] + 0.7152 * rail[..., 1] + 0.0722 * rail[..., 2]
    edge_lum = 0.2126 * right_edge[..., 0] + 0.7152 * right_edge[..., 1] + 0.0722 * right_edge[..., 2]
    left_lum = 0.2126 * left_bg[..., 0] + 0.7152 * left_bg[..., 1] + 0.0722 * left_bg[..., 2]
    bg_p95 = float(np.percentile(edge_lum, 95))
    bg_med = float(np.median(left_lum))

    gx = np.abs(np.diff(rail_lum[:, :96], axis=1))[:-1, :]
    gy = np.abs(np.diff(rail_lum[:, :95], axis=0))
    bright_card = rail_lum[:-1, :95] > max(215.0, bg_p95 + 55.0)
    sharp_ui = ((gx + gy) > 95.0) & (np.abs(rail_lum[:-1, :95] - bg_med) > 75.0)
    raw_card_pct = float((bright_card | sharp_ui).mean() * 100.0)
    card_pct = raw_card_pct if raw_card_pct >= 1.2 else 0.0

    total_pct = max(cap_pct, card_pct)
    if total_pct <= 0.0:
        return 0
    rounded = round(total_pct, 1)
    return int(rounded) if rounded.is_integer() else rounded


def build_mockup_array(
    input_png: Path,
    avatar_png: Path,
    caption1: str | None = None,
    caption2: str | None = None,
    manifest: dict | None = None,
) -> np.ndarray:
    dyn_c1, dyn_c2 = extract_instagram_caption_lines(manifest)
    safe_c1 = _clamp_caption_line(caption1 if caption1 is not None else dyn_c1, max_chars=MAX_CAPTION_CHARS)
    safe_c2 = _clamp_caption_line(caption2 if caption2 is not None else dyn_c2, max_chars=MAX_CAPTION_CHARS)

    img = decode_rgb(input_png, W, H)
    est_cap_right_x = CAPTION_X + max(len(safe_c1), len(safe_c2)) * 6 * CAPTION_SCALE
    measured_overlap_pct = measure_right_rail_overlap_pct(img, caption_right_x=est_cap_right_x)
    overlap_label = f"IG REELS SAFE-ZONE SIMULATOR · 124PX RAIL · {measured_overlap_pct}% OVERLAP"
    if measured_overlap_pct > 0:
        raise ValueError(f"{overlap_label} (intrusion detected in x >= {RIGHT_RAIL_X}, y: 1000..1460)")

    vgrad(img, 0, 185, 0.56, 0.0)
    vgrad(img, 1485, 1840, 0.0, 0.84)
    rrect(img, 0, 1840, W, 80, 0, (5, 7, 12), 0.96)

    draw_text(img, "9:41", 72, 36, scale=3, a=0.95)
    rrect(img, 428, 26, 224, 38, 19, (4, 5, 8), 0.96)
    for idx, bh in enumerate((8, 12, 16, 20)):
        rrect(img, 888 + idx * 9, 58 - bh, 5, bh, 2, (255, 255, 255), 0.94)
    circ(img, 944, 56, 13, (255, 255, 255), 0.92, stroke=2.6, a_deg=(225, 315))
    circ(img, 944, 56, 7, (255, 255, 255), 0.92, stroke=2.6, a_deg=(225, 315))
    circ(img, 944, 57, 2.2, (255, 255, 255), 0.95)
    rrect(img, 968, 39, 38, 19, 5, (255, 255, 255), 0.92, stroke=2.2)
    rrect(img, 972, 43, 28, 11, 3, (255, 255, 255), 0.94)

    draw_text(img, "Reels", 64, 108, scale=5, a=0.97)
    seg(img, 226, 126, 236, 136, 3.2, (255, 255, 255), 0.92)
    seg(img, 246, 126, 236, 136, 3.2, (255, 255, 255), 0.92)
    rrect(img, 984, 108, 46, 36, 9, (255, 255, 255), 0.94, stroke=3.0)
    circ(img, 1007, 126, 8.5, (255, 255, 255), 0.94, stroke=2.8)
    rrect(img, 995, 101, 24, 7, 3, (255, 255, 255), 0.94)

    rrect(img, 256, 106, 696, 42, 21, (6, 42, 28), 0.88)
    rrect(img, 256, 106, 696, 42, 21, (34, 197, 94), 0.95, stroke=2.2, dash=8)
    draw_text(
        img,
        overlap_label,
        604,
        118,
        scale=2,
        rgb=(134, 239, 172),
        a=0.98,
        center=True,
    )
    draw_notched_safe_envelope(img)
    draw_right_rail_icons(img, avatar_png)

    if avatar_png.is_file():
        dp = decode_rgb(avatar_png, 50, 50)
        yy, xx = np.mgrid[0:50, 0:50]
        cm = np.clip(24.5 - np.hypot(xx - 24.5, yy - 24.5), 0.0, 1.0)[..., None]
        img[1518:1568, 56:106] = img[1518:1568, 56:106] * (1.0 - cm) + dp * cm
    circ(img, 81, 1543, 26, (250, 204, 21), 0.95, stroke=2.4)
    hw = draw_text(img, "@cyberjasoos ·", 120, 1530, scale=3, a=0.97)
    fx = 120 + hw + 8
    rrect(img, fx, 1522, 126, 40, 10, (255, 255, 255), 0.16)
    rrect(img, fx, 1522, 126, 40, 10, (255, 255, 255), 0.88, stroke=2.0)
    draw_text(img, "Follow", fx + 63, 1531, scale=3, a=0.97, center=True)

    w1 = draw_text(img, safe_c1, CAPTION_X, 1588, scale=CAPTION_SCALE, rgb=(241, 245, 249), a=0.94)
    w2 = draw_text(img, safe_c2, CAPTION_X, 1626, scale=CAPTION_SCALE, rgb=(203, 213, 225), a=0.88)
    assert CAPTION_X + max(w1, w2) < RIGHT_RAIL_X, "Caption text intruded into 124px right action rail"

    rrect(img, 56, 1682, 554, 44, 22, (15, 23, 42), 0.72)
    rrect(img, 56, 1682, 554, 44, 22, (255, 255, 255), 0.24, stroke=1.5)
    for bi, bh in enumerate((12, 20, 15)):
        rrect(img, 80 + bi * 8, 1714 - bh, 4, bh, 2, (255, 255, 255), 0.92)
    draw_text(img, "cyberjasoos · Original Noir Audio", 114, 1695, scale=2, rgb=(248, 250, 252), a=0.95)

    rrect(img, 0, 1836, W, 4, 0, (255, 255, 255), 0.24)
    rrect(img, 0, 1836, 740, 4, 0, (255, 255, 255), 0.92)
    seg(img, 108, 1872, 124, 1858, 2.6, (180, 190, 205), 0.82)
    seg(img, 140, 1872, 124, 1858, 2.6, (180, 190, 205), 0.82)
    rrect(img, 112, 1870, 24, 18, 3, (180, 190, 205), 0.82, stroke=2.4)
    circ(img, 329, 1870, 11, (180, 190, 205), 0.82, stroke=2.6)
    seg(img, 337, 1878, 346, 1887, 2.8, (180, 190, 205), 0.82)
    rrect(img, 524, 1857, 32, 32, 9, (180, 190, 205), 0.82, stroke=2.5)
    seg(img, 540, 1865, 540, 1881, 2.6, (180, 190, 205), 0.82)
    seg(img, 532, 1873, 548, 1873, 2.6, (180, 190, 205), 0.82)
    rrect(img, 731, 1858, 34, 30, 8, (255, 255, 255), 0.97, stroke=2.8)
    seg(img, 744, 1867, 756, 1873, 2.8, (255, 255, 255), 0.97)
    seg(img, 744, 1879, 756, 1873, 2.8, (255, 255, 255), 0.97)
    circ(img, 956, 1873, 15, (250, 204, 21), 0.94, stroke=2.5)
    rrect(img, 395, 1903, 290, 6, 3, (255, 255, 255), 0.85)
    return img


def render_mockup(
    input_png: Path,
    output_png: Path,
    avatar_png: Path,
    caption1: str | None = None,
    caption2: str | None = None,
    manifest: dict | None = None,
) -> None:
    resolved = manifest if manifest is not None else resolve_episode_manifest(None, input_png)
    img = build_mockup_array(input_png, avatar_png, caption1=caption1, caption2=caption2, manifest=resolved)
    encode_png(img, output_png)


def _resize_bilinear(img: np.ndarray, out_w: int, out_h: int) -> np.ndarray:
    ih, iw = img.shape[:2]
    if (iw, ih) == (out_w, out_h):
        return img
    ys = np.clip((np.arange(out_h, dtype=np.float32) + 0.5) * (ih / out_h) - 0.5, 0.0, ih - 1.0)
    xs = np.clip((np.arange(out_w, dtype=np.float32) + 0.5) * (iw / out_w) - 0.5, 0.0, iw - 1.0)
    y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
    y1, x1 = np.minimum(y0 + 1, ih - 1), np.minimum(x0 + 1, iw - 1)
    wy, wx = (ys - y0)[:, None, None], (xs - x0)[None, :, None]
    top = (1.0 - wx) * img[y0[:, None], x0[None, :]] + wx * img[y0[:, None], x1[None, :]]
    bot = (1.0 - wx) * img[y1[:, None], x0[None, :]] + wx * img[y1[:, None], x1[None, :]]
    return (1.0 - wy) * top + wy * bot


def render_multi_shot_grid(
    input_pngs: list[Path],
    output_png: Path,
    avatar_png: Path,
    caption1: str | None = None,
    caption2: str | None = None,
    manifest: dict | None = None,
    cols: int | None = None,
    tile_scale: float = 0.5,
) -> None:
    if not input_pngs:
        raise ValueError("render_multi_shot_grid requires at least one input PNG")
    resolved = manifest if manifest is not None else resolve_episode_manifest(None, input_pngs[0])
    tw = max(180, int(round(W * tile_scale)))
    th = max(320, int(round(H * tile_scale)))
    ncols = max(1, min(len(input_pngs), cols if cols and cols > 0 else 4))
    nrows = int(math.ceil(len(input_pngs) / ncols))
    pad = 24
    gw = pad + ncols * (tw + pad)
    gh = pad + nrows * (th + pad)
    canvas = np.full((gh, gw, 3), (6.0, 9.0, 18.0), dtype=np.float32)
    border_rgb = np.array((34.0, 197.0, 94.0), dtype=np.float32)

    for idx, frame_p in enumerate(input_pngs):
        r_idx, c_idx = divmod(idx, ncols)
        tx = pad + c_idx * (tw + pad)
        ty = pad + r_idx * (th + pad)
        full_mockup = build_mockup_array(
            frame_p,
            avatar_png,
            caption1=caption1,
            caption2=caption2,
            manifest=resolved,
        )
        tile = _resize_bilinear(full_mockup, tw, th)
        canvas[ty - 2 : ty + th + 2, tx - 2 : tx + tw + 2] = border_rgb * 0.65
        canvas[ty : ty + th, tx : tx + tw] = tile

    encode_png(canvas, output_png)


def _discover_episode_frames(manifest: dict | None, fallback_input: Path) -> list[Path]:
    prefix = ""
    if isinstance(manifest, dict) and manifest.get("id"):
        m = re.match(r"(s\d{2}e\d{2})", str(manifest["id"]), flags=re.IGNORECASE)
        prefix = m.group(1).lower() if m else str(manifest["id"]).lower()
    if not prefix:
        m = re.search(r"(s\d{2}e\d{2})", fallback_input.name, flags=re.IGNORECASE)
        prefix = m.group(1).lower() if m else ""
    found: list[Path] = []
    if prefix:
        for search_dir in (REPO_ROOT / "renders", REPO_ROOT / "renders" / "uat"):
            if search_dir.is_dir():
                for p in sorted(search_dir.glob("*.png")):
                    low = p.name.lower()
                    if prefix in low and "mockup" not in low and "grid" not in low:
                        found.append(p)
    return found if found else ([fallback_input] if fallback_input.is_file() else [])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", "-i", default="renders/s01e01-preview-frame.png")
    ap.add_argument("--inputs", nargs="+", default=None, help="Multiple frame PNGs for --multi-shot-grid")
    ap.add_argument("--episode", "-e", default=None, help="Episode manifest JSON path (auto-detected if omitted)")
    ap.add_argument("--output", "-o", default="renders/s01e01-instagram-ui-mockup.png")
    ap.add_argument("--avatar", default="engine/public/brand/kabir-avatar.png")
    ap.add_argument("--caption1", default=None, help="Override caption line 1 (defaults to manifest instagramCaption)")
    ap.add_argument("--caption2", default=None, help="Override caption line 2 (defaults to manifest instagramCaption)")
    ap.add_argument("--multi-shot-grid", action="store_true", help="Composite multiple mocked-up shots into a QA grid PNG")
    ap.add_argument("--grid-cols", type=int, default=None, help="Columns in --multi-shot-grid mode (default: up to 4)")
    ap.add_argument("--grid-scale", type=float, default=0.5, help="Per-tile scale in --multi-shot-grid mode (default: 0.5)")
    args = ap.parse_args()

    resolve_p = lambda raw: Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw
    in_p = resolve_p(args.input)
    out_p = resolve_p(args.output)
    av_p = resolve_p(args.avatar)
    seed_p = resolve_p(args.inputs[0]) if args.inputs else in_p
    manifest = resolve_episode_manifest(args.episode, seed_p)

    if args.multi_shot_grid:
        frames = [resolve_p(p) for p in args.inputs] if args.inputs else _discover_episode_frames(manifest, in_p)
        render_multi_shot_grid(
            frames,
            out_p,
            av_p,
            caption1=args.caption1,
            caption2=args.caption2,
            manifest=manifest,
            cols=args.grid_cols,
            tile_scale=args.grid_scale,
        )
        print(f"Rendered Instagram Reels multi-shot grid ({len(frames)} shots) -> {out_p}")
    else:
        render_mockup(in_p, out_p, av_p, caption1=args.caption1, caption2=args.caption2, manifest=manifest)
        print(f"Rendered Instagram Reels UI mockup -> {out_p}")


if __name__ == "__main__":
    main()
