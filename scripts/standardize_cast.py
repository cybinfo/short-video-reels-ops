#!/usr/bin/env python3
"""Standardize Case #01 primary cast portraits & B-roll plates to a unified 1080x1920 grid."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import pathlib
from pathlib import Path
import shutil
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CASE_DIR = REPO_ROOT / "assets" / "characters" / "case01"
RAW_DIR = CASE_DIR / "raw"
PUBLIC_DIR = REPO_ROOT / "engine" / "public" / "characters"

W, H = 1080, 1920
DST_EYE_PCT = 0.365

# Measured on raw 768x1376 plates: (scale, src_face_center_x_pct, src_eye_y_pct)
# Standardized target grid: 1080x1920, crown = 20.0%, eye_y = 36.5%, chin = 52.5%, center_x = 50.0%
CAST_SPECS: dict[str, tuple[float, float, float]] = {
    "kabir-investigating.png": (1.18, 0.500, 0.358),
    "sharma-shock.png": (1.27, 0.512, 0.384),
    "golu.png": (1.13, 0.455, 0.376),
    "ramu-kaka.png": (0.97, 0.505, 0.442),
    "pappu-chachu.png": (0.965, 0.478, 0.303),
    "golu-caught-tanki.png": (1.02, 0.523, 0.380),
    "sharma-relief-dawn.png": (0.99, 0.504, 0.372),
}

BROLL_PLATES: tuple[str, ...] = (
    "shaadi-baraat-gate.png",
    "sharma-eyes-closeup.png",
    "puja-phone.png",
    "puja-otp-divert.png",
    "handoff-shadow.png",
    "kabir-closeup.png",
    "case02-hotel-wifi.png",
    "case02-smart-printer.png",
    "case02-shaadi-qr.png",
)

# Rooftop suspect B-roll plates pixel-locked to crimson phone centroid: (scale, dst_tx, dst_ty)
TARGETED_BROLL_SPECS: dict[str, tuple[float, float, float]] = {
    "shaadi-chhat-wide.png": (1.06, 0.500, 0.3463),
    "shaadi-chhat-signal.png": (1.02, 0.500, 0.3463),
    "tanki-burner-phone.png": (1.16, 0.537, 0.3672),
}


def _load_rgb(path: pathlib.Path, width: int, height: int):
    import numpy as np

    raw = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-vf",
            f"scale={width}:{height}:flags=lanczos",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ]
    )
    return np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3)


def _save_png(arr, path: pathlib.Path) -> None:
    height, width, _ = arr.shape
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-i",
            "-",
            str(path),
        ],
        input=arr.tobytes(),
        check=True,
    )


def conform_portrait(raw_path: pathlib.Path, scale: float, src_cx: float, src_eye: float):
    import numpy as np

    sw, sh = int(round(W * scale)), int(round(H * scale))
    src = _load_rgb(raw_path, sw, sh).copy()
    x0 = int(round(src_cx * sw - W * 0.5))
    y0 = int(round(src_eye * sh - DST_EYE_PCT * H))

    pad_l, pad_r = max(0, -x0), max(0, (x0 + W) - sw)
    pad_t, pad_b = max(0, -y0), max(0, (y0 + H) - sh)
    if pad_l or pad_r or pad_t or pad_b:
        src = np.pad(src, ((pad_t, pad_b), (pad_l, pad_r), (0, 0)), mode="edge")
        if pad_t > 0:
            band = pad_t + 36
            strip = src[:band].astype(np.float32)
            for _ in range(10):
                strip[1:-1] = 0.25 * strip[:-2] + 0.5 * strip[1:-1] + 0.25 * strip[2:]
            fade = np.linspace(0.45, 1.0, band, dtype=np.float32)[:, None, None]
            src[:band] = np.clip(strip * fade, 0, 255).astype(np.uint8)
        if pad_b > 0:
            band = pad_b + 64
            strip = src[-band:].astype(np.float32)
            for _ in range(12):
                strip[1:-1] = 0.25 * strip[:-2] + 0.5 * strip[1:-1] + 0.25 * strip[2:]
            fade = np.linspace(1.0, 0.12, band, dtype=np.float32)[:, None, None]
            src[-band:] = np.clip(strip * fade, 0, 255).astype(np.uint8)
        x0 += pad_l
        y0 += pad_t

    out = src[y0 : y0 + H, x0 : x0 + W].copy()
    # Apply subtle bottom studio vignette (y: 82%..100%) so lower card labels sit on rich dark shadow
    vignette_rows = int(H * 0.18)
    v_curve = np.linspace(1.0, 0.18, vignette_rows, dtype=np.float32)[:, None, None]
    out[-vignette_rows:] = np.clip(out[-vignette_rows:].astype(np.float32) * v_curve, 0, 255).astype(np.uint8)
    return out


def inpaint_tank_trademark(arr):
    """Remove cropped white brand stencil on dark water tank (x: 755..1080, y: 190..380)."""
    import numpy as np
    from scipy.ndimage import binary_dilation, gaussian_filter

    out = arr.copy().astype(np.float32)
    roi = out[190:380, 755:1080]
    luma = 0.299 * roi[:, :, 0] + 0.587 * roi[:, :, 1] + 0.114 * roi[:, :, 2]
    ry, rx = np.mgrid[190:380, 755:1080]
    core_mask = (luma > 36.0) | ((ry <= 348) & (luma > 18.0))
    dilated = binary_dilation(core_mask, iterations=7)
    feather = gaussian_filter(dilated.astype(np.float32), sigma=4.5)
    feather = np.clip(np.maximum(feather, core_mask.astype(np.float32)), 0.0, 1.0)[:, :, None]

    rng = np.random.default_rng(1080)
    x_norm = np.clip((rx - 755.0) / 325.0, 0.0, 1.0)
    tank_plate = np.stack(
        [6.0 + 5.0 * x_norm, 11.0 + 4.5 * x_norm, 16.0 + 6.5 * x_norm],
        axis=-1,
    )
    grain = gaussian_filter(rng.normal(0.0, 2.2, size=roi.shape).astype(np.float32), sigma=(0.55, 0.55, 0.0)) * 1.45
    tank_plate = np.clip(tank_plate + grain, 2.0, 28.0)

    out[190:380, 755:1080] = roi * (1.0 - feather) + tank_plate * feather
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def conform_golu_phone_dial(raw_path: pathlib.Path):
    """Frame Golu's dialing hands + glowing smartphone at y = 760..935 above lower clue cards."""
    import numpy as np

    sw, sh = int(round(W * 1.05)), int(round(H * 1.05))
    src = _load_rgb(raw_path, sw, sh)
    x0 = (sw - W) // 2
    y0 = 388  # Upward framing shift so glowing smartphone sits cleanly inside y = 735..935
    pad_b = max(0, (y0 + H) - sh)
    work = np.pad(src, ((0, pad_b), (0, 0), (0, 0)), mode="reflect")
    cropped = work[y0 : y0 + H, x0 : x0 + W].astype(np.float32)

    noir = np.array([4.0, 6.0, 12.0], dtype=np.float32)
    y_idx = np.arange(H, dtype=np.float32)
    alpha_bot = np.interp(
        y_idx,
        [0.0, 975.0, 1050.0, 1190.0, 1420.0, float(H)],
        [0.0, 0.0, 0.40, 0.78, 0.92, 0.95],
    ).astype(np.float32)[:, None, None]
    alpha_top = np.interp(y_idx, [0.0, 85.0, 200.0, float(H)], [0.38, 0.15, 0.0, 0.0]).astype(np.float32)[:, None, None]
    shaded = cropped * (1.0 - alpha_bot) + noir * alpha_bot
    shaded = shaded * (1.0 - alpha_top) + noir * alpha_top
    return np.clip(np.rint(shaded), 0, 255).astype(np.uint8)


def conform_targeted_broll(
    raw_path: pathlib.Path,
    scale: float,
    dst_tx: float = 0.500,
    dst_ty: float = 0.3463,
    crimson_phone_body: bool = False,
):
    import numpy as np
    from scipy.ndimage import gaussian_filter

    sw, sh = int(round(W * scale)), int(round(H * scale))
    src = _load_rgb(raw_path, sw, sh).astype(np.float32)

    # Keep warm background marigold/tungsten bulbs golden so crimson detection isolates the red phone glow
    amber_bg = (src[:, :, 1] >= 62.0) & ((src[:, :, 0] - src[:, :, 1]) > 80.0)
    if np.any(amber_bg):
        src[:, :, 1] = np.where(amber_bg, np.maximum(src[:, :, 1], src[:, :, 0] - 80.0), src[:, :, 1])

    r = src[:, :, 0].astype(int)
    g = src[:, :, 1].astype(int)
    b = src[:, :, 2].astype(int)
    yy, xx = np.mgrid[0:sh, 0:sw]
    phone_mask = (
        (r >= 145)
        & ((r - g) >= 85)
        & ((r - b) >= 85)
        & (xx >= int(sw * 0.32))
        & (xx <= int(sw * 0.82))
        & (yy >= int(sh * 0.36))
        & (yy <= int(sh * 0.66))
    )
    src_rx = float(xx[phone_mask].mean())
    src_ry = float(yy[phone_mask].mean())

    src_u8 = np.clip(np.rint(src), 0, 255).astype(np.uint8)
    noir = np.array([4.0, 7.0, 15.0], dtype=np.float32)
    y_idx = np.arange(H, dtype=np.float32)
    fade_start = min(855.0, dst_ty * H + 190.0)
    alpha = np.interp(
        y_idx,
        [0.0, fade_start, 915.0, 965.0, 1100.0, 1450.0, float(H)],
        [0.0, 0.0, 0.42, 0.64, 0.83, 0.885, 0.90],
    ).astype(np.float32)[:, None, None]

    def _crop_and_shade(orig_x0: int, orig_y0: int):
        pad_l, pad_r = max(0, -orig_x0), max(0, (orig_x0 + W) - sw)
        pad_t, pad_b = max(0, -orig_y0), max(0, (orig_y0 + H) - sh)
        work = src_u8
        cx0, cy0 = orig_x0, orig_y0
        if pad_l or pad_r or pad_t or pad_b:
            work = np.pad(work, ((pad_t, pad_b), (pad_l, pad_r), (0, 0)), mode="reflect")
            cx0 += pad_l
            cy0 += pad_t
        cropped = work[cy0 : cy0 + H, cx0 : cx0 + W].astype(np.float32)
        rng = np.random.default_rng(1920)

        if pad_l > 0:
            band_l = min(W, pad_l + 96)
            lx = np.linspace(1.0, 0.0, band_l, dtype=np.float32)[None, :, None]
            l_blur = np.stack([gaussian_filter(cropped[:, :band_l, c], sigma=(2.5, 6.0)) for c in range(3)], axis=-1)
            l_vig = (lx ** 1.25) * 0.92
            cropped[:, :band_l] = (cropped[:, :band_l] * (1.0 - lx) + l_blur * lx) * (1.0 - l_vig) + noir[None, None, :] * l_vig
            cropped[:, :band_l] += rng.normal(0.0, 1.3, size=(H, band_l, 3)).astype(np.float32)

        if pad_r > 0:
            # Vignette smoothly from right edge of vertical pipe into dark rooftop shadow so zero smear/mirror shows
            band_r = min(W, pad_r + 108)
            rx_lin = np.linspace(0.0, 1.0, band_r, dtype=np.float32)[None, :, None]
            r_blur = np.stack([gaussian_filter(cropped[:, -band_r:, c], sigma=(3.0, 7.0)) for c in range(3)], axis=-1)
            b_w = np.clip(rx_lin * 1.35, 0.0, 1.0)
            r_vig = np.clip((rx_lin - 0.10) / 0.90, 0.0, 1.0) ** 1.15 * 0.94
            dark_r = np.array([5.0, 8.0, 15.0], dtype=np.float32)[None, None, :]
            mixed_r = cropped[:, -band_r:] * (1.0 - b_w) + r_blur * b_w
            mixed_r = mixed_r * (1.0 - r_vig) + dark_r * r_vig
            mixed_r += rng.normal(0.0, 1.4, size=(H, band_r, 3)).astype(np.float32) * np.clip(rx_lin * 1.4, 0.25, 1.0)
            cropped[:, -band_r:] = mixed_r

        if crimson_phone_body:
            oy_m, ox_m = np.mgrid[0:H, 0:W]
            t_y = np.clip((oy_m - 590.0) / (912.0 - 590.0), 0.0, 1.0)
            x_left = 514.0 - 54.0 * t_y
            x_right = 656.0 - 52.0 * t_y
            in_poly = (oy_m >= 590) & (oy_m <= 912) & (ox_m >= x_left) & (ox_m <= x_right)
            poly_w = gaussian_filter(in_poly.astype(np.float32), sigma=2.2)
            cr, cg, cb = cropped[:, :, 0], cropped[:, :, 1], cropped[:, :, 2]
            neutral_body = poly_w * np.clip(1.0 - np.maximum(0.0, (cr - cg) - 45.0) / 45.0, 0.0, 1.0)
            body_luma = 0.299 * cr + 0.587 * cg + 0.114 * cb
            crimson_rgb = np.stack(
                [
                    np.clip(body_luma * 1.52 + 30.0, 22.0, 220.0),
                    np.clip(body_luma * 0.36 + 3.0, 3.0, 88.0),
                    np.clip(body_luma * 0.42 + 5.0, 4.0, 96.0),
                ],
                axis=-1,
            )
            tint_w = (neutral_body * 0.85)[:, :, None]
            cropped = cropped * (1.0 - tint_w) + crimson_rgb * tint_w

        shaded = cropped * (1.0 - alpha) + noir[None, None, :] * alpha
        # Add subtle film/rooftop grain in deep lower vignette so below y=1100 never quantizes to flat bands
        lower_grain = rng.normal(0.0, 1.1, size=shaded.shape).astype(np.float32) * (alpha * 0.65)
        return np.clip(np.rint(shaded + lower_grain), 0, 255).astype(np.uint8)

    target_x, target_y = dst_tx * W, dst_ty * H
    x0 = int(round(src_rx - target_x))
    y0 = int(round(src_ry - target_y))
    out = _crop_and_shade(x0, y0)

    # Sub-pixel centroid refinement inside target phone viewport (y: 450..880)
    oy, ox = np.mgrid[0:H, 0:W]
    or_ch, og_ch = out[:, :, 0].astype(int), out[:, :, 1].astype(int)
    band_lo, band_hi = max(0, int(round(target_y - 215))), min(H, int(round(target_y + 215)))
    lock_mask = (or_ch >= 150) & ((or_ch - og_ch) >= 90) & (oy >= band_lo) & (oy <= band_hi)
    if np.any(lock_mask):
        dx = int(round(float(ox[lock_mask].mean()) - target_x))
        dy = int(round(float(oy[lock_mask].mean()) - target_y))
        if dx or dy:
            out = _crop_and_shade(x0 + dx, y0 + dy)
    return out


def conform_broll(raw_path: pathlib.Path, dst_path: pathlib.Path) -> None:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(raw_path),
            "-vf",
            f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}",
            str(dst_path),
        ],
        check=True,
    )


RAW_IMAGE_EXTS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp")
_EXT_PRIORITY: dict[str, int] = {ext: idx for idx, ext in enumerate(RAW_IMAGE_EXTS)}

AUTO_BROLL_KEYWORDS: tuple[str, ...] = (
    "broll",
    "bg",
    "wide",
    "room",
    "wifi",
    "qr",
    "printer",
    "phone",
    "gate",
    "chhat",
    "ui",
    "cli",
    "hub",
    "portal",
    "brief",
    "terminal",
    "ledger",
    "guide",
    "screen",
    "stage",
    "safezone",
    "launch",
    "poll",
    "cover",
)
_AUTO_DEPTH_SESSION = None
_AUTO_DEPTH_UNAVAILABLE = False


def _get_auto_depth_session():
    global _AUTO_DEPTH_SESSION, _AUTO_DEPTH_UNAVAILABLE
    if _AUTO_DEPTH_UNAVAILABLE:
        return None
    if _AUTO_DEPTH_SESSION is not None:
        return _AUTO_DEPTH_SESSION
    try:
        from huggingface_hub import hf_hub_download
        import onnxruntime as ort

        try:
            onnx_path = hf_hub_download(
                repo_id="onnx-community/depth-anything-v2-small",
                filename="onnx/model_fp16.onnx",
                local_files_only=True,
            )
        except Exception:
            onnx_path = hf_hub_download(
                repo_id="onnx-community/depth-anything-v2-small",
                filename="onnx/model_fp16.onnx",
            )
        _AUTO_DEPTH_SESSION = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        return _AUTO_DEPTH_SESSION
    except Exception:
        _AUTO_DEPTH_UNAVAILABLE = True
        return None


def _rgb_upper_silhouette_mask(rgb) -> object:
    import numpy as np

    ih, iw, _ = rgb.shape
    arr = rgb.astype(np.float32)
    tl = arr[int(0.02 * ih) : int(0.12 * ih), int(0.02 * iw) : int(0.14 * iw)]
    tr = arr[int(0.02 * ih) : int(0.12 * ih), int(0.86 * iw) : int(0.98 * iw)]
    bg_ref = 0.5 * (np.median(tl.reshape(-1, 3), axis=0) + np.median(tr.reshape(-1, 3), axis=0))
    color_dist = np.linalg.norm(arr - bg_ref[None, None, :], axis=-1)

    luma = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    gx = np.zeros_like(luma)
    gy = np.zeros_like(luma)
    gx[:, 1:-1] = np.abs(luma[:, 2:] - luma[:, :-2]) * 0.5
    gy[1:-1, :] = np.abs(luma[2:, :] - luma[:-2, :]) * 0.5
    sal = color_dist * 0.65 + (gx + gy) * 1.35
    central = sal[int(0.08 * ih) : int(0.88 * ih), int(0.18 * iw) : int(0.82 * iw)]
    thresh = float(np.percentile(central, 62.0))
    mask = sal > max(18.0, thresh)
    mask[:, : int(0.16 * iw)] = False
    mask[:, int(0.84 * iw) :] = False
    return mask


def estimate_auto_cast_spec(raw_path: Path) -> tuple[float, float, float]:
    """Estimate (scale, src_face_center_x_pct, src_eye_y_pct) for an uncalibrated portrait plate."""
    import numpy as np

    ih, iw = 924, 518
    rgb = _load_rgb(Path(raw_path), iw, ih)
    sess = _get_auto_depth_session()
    subj = None

    if sess is not None:
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm = (rgb.astype(np.float32) / 255.0 - mean) / std
        inp = np.transpose(norm, (2, 0, 1))[None, :, :, :].astype(np.float32)
        depth = np.squeeze(sess.run(None, {"pixel_values": inp})[0]).astype(np.float32)
        c_slice = depth[int(0.08 * ih) : int(0.92 * ih), int(0.18 * iw) : int(0.82 * iw)]
        lo, hi = float(np.percentile(c_slice, 5.0)), float(np.percentile(c_slice, 98.0))
        nd = np.clip((depth - lo) / max(1e-5, hi - lo), 0.0, 1.0)
        mask = nd > 0.52
        mask[:, : int(0.14 * iw)] = False
        mask[:, int(0.86 * iw) :] = False
        try:
            from scipy.ndimage import label

            labeled, n_comp = label(mask)
            torso = labeled[int(0.35 * ih) : int(0.85 * ih), int(0.28 * iw) : int(0.72 * iw)]
            best_lbl, best_score = 0, -1
            for lbl_id in range(1, n_comp + 1):
                sc = int((torso == lbl_id).sum())
                if sc > best_score:
                    best_score, best_lbl = sc, lbl_id
            subj = (labeled == best_lbl) if best_lbl > 0 and best_score > 50 else mask
        except Exception:
            subj = mask

    if subj is None or int(subj.sum()) < 200:
        subj = _rgb_upper_silhouette_mask(rgb)

    corridor = subj[:, int(0.20 * iw) : int(0.76 * iw)]
    row_w = corridor.sum(axis=1) / float(iw)
    y_min, y_max = int(0.06 * ih), int(0.45 * ih)
    valid_row = (row_w >= 0.06) & (row_w <= 0.48)
    y_top = 0.21
    for r_idx in range(y_min, y_max - 2):
        if valid_row[r_idx] and valid_row[r_idx + 1] and valid_row[r_idx + 2]:
            y_top = float(r_idx) / float(ih)
            break

    h_y0 = int(min(0.60, y_top + 0.025) * ih)
    h_y1 = int(min(0.68, y_top + 0.19) * ih)
    head_band = subj[h_y0:h_y1, int(0.16 * iw) : int(0.84 * iw)]
    xs = np.where(head_band)[1]
    x_center = (float(np.median(xs)) + 0.16 * iw) / float(iw) if len(xs) >= 20 else 0.500
    x_center = float(np.clip(x_center, 0.35, 0.65))

    band_widths = head_band.sum(axis=1) / float(iw)
    head_w = float(np.clip(np.percentile(band_widths, 75.0) if band_widths.size else 0.30, 0.22, 0.36))
    eye_offset = float(np.clip(0.46 * head_w, 0.125, 0.168))
    src_eye_y = float(np.clip(y_top + eye_offset, 0.24, 0.50))
    scale = float(np.clip(0.165 / eye_offset, 0.90, 1.32))
    return (round(scale, 3), round(x_center, 3), round(src_eye_y, 3))


def _normalize_plate_set(items: Sequence[str] | None) -> set[str]:
    out: set[str] = set()
    for raw in items or ():
        for part in raw.split(","):
            tok = part.strip()
            if not tok:
                continue
            p_tok = Path(tok)
            stem = p_tok.stem if p_tok.suffix.lower() in _EXT_PRIORITY else p_tok.name
            out.add(f"{stem}.png")
    return out


def _apply_broll_lower_vignette(case_file: Path, pub_file: Path) -> None:
    import numpy as np

    arr_b = _load_rgb(case_file, W, H).copy()
    v_rows = int(H * 0.22)
    vc = np.linspace(1.0, 0.16, v_rows, dtype=np.float32)[:, None, None]
    arr_b[-v_rows:] = np.clip(arr_b[-v_rows:].astype(np.float32) * vc, 0, 255).astype(np.uint8)
    _save_png(arr_b, case_file)
    _save_png(arr_b, pub_file)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", type=Path, default=CASE_DIR, help="Character case directory")
    parser.add_argument("--only", action="append", default=[], metavar="PLATE", help="Only conform specified plate(s)")
    parser.add_argument("--broll", action="append", default=[], metavar="PLATE", help="Force center-cover B-roll mode")
    parser.add_argument("--auto-frame", action="store_true", help="Auto-frame uncalibrated plates in <case_dir>/raw/")
    args = parser.parse_args(argv)

    case_dir = args.case_dir.resolve()
    raw_dir = case_dir / "raw"
    only_set = _normalize_plate_set(args.only)
    broll_set = _normalize_plate_set(args.broll)

    raw_dir.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    if args.auto_frame or broll_set:
        top_imgs = [
            p
            for p in case_dir.iterdir()
            if p.is_file()
            and p.suffix.lower() in _EXT_PRIORITY
            and "cast-sheet" not in p.name.lower()
        ]
        top_imgs.sort(key=lambda p: (_EXT_PRIORITY[p.suffix.lower()], p.stem.lower(), p.name))
        for top_img in top_imgs:
            if not any((raw_dir / f"{top_img.stem}{ext}").exists() for ext in RAW_IMAGE_EXTS):
                shutil.copy2(top_img, raw_dir / top_img.name)

    processed: set[str] = set()

    for fname, (scale, cx, eye_y) in CAST_SPECS.items():
        if fname in broll_set or (only_set and fname not in only_set):
            continue
        raw_backup = raw_dir / fname
        if not raw_backup.exists():
            if not (case_dir / fname).exists():
                continue
            shutil.copy2(case_dir / fname, raw_backup)
        arr = conform_portrait(raw_backup, scale, cx, eye_y)
        if fname == "golu-caught-tanki.png":
            arr = inpaint_tank_trademark(arr)
        _save_png(arr, case_dir / fname)
        _save_png(arr, PUBLIC_DIR / fname)
        processed.add(fname)
        print(f"Standardized {fname:24s} -> 1080x1920 (eye_y={DST_EYE_PCT*100:.1f}%, center_x=50.0%)")

    golu_dial = "golu-phone-dial.png"
    if golu_dial not in broll_set and (not only_set or golu_dial in only_set):
        golu_dial_raw = raw_dir / golu_dial
        if golu_dial_raw.exists() or (case_dir / golu_dial).exists():
            if not golu_dial_raw.exists():
                shutil.copy2(case_dir / golu_dial, golu_dial_raw)
            arr_dial = conform_golu_phone_dial(golu_dial_raw)
            _save_png(arr_dial, case_dir / golu_dial)
            _save_png(arr_dial, PUBLIC_DIR / golu_dial)
            processed.add(golu_dial)
            print(f"Framed action B-roll {golu_dial:20s} -> 1080x1920 (phone_y=735..935, scale=1.05)")

    for fname in BROLL_PLATES:
        if only_set and fname not in only_set:
            continue
        raw_backup = raw_dir / fname
        if not raw_backup.exists():
            if not (case_dir / fname).exists():
                continue
            shutil.copy2(case_dir / fname, raw_backup)
        conform_broll(raw_backup, case_dir / fname)
        conform_broll(raw_backup, PUBLIC_DIR / fname)
        if fname.startswith("case02-"):
            _apply_broll_lower_vignette(case_dir / fname, PUBLIC_DIR / fname)
        processed.add(fname)
        print(f"Conformed B-roll {fname:20s} -> 1080x1920")

    for fname, (scale, dst_tx, dst_ty) in TARGETED_BROLL_SPECS.items():
        if fname in broll_set or (only_set and fname not in only_set):
            continue
        raw_backup = raw_dir / fname
        if not raw_backup.exists():
            if not (case_dir / fname).exists():
                continue
            shutil.copy2(case_dir / fname, raw_backup)
        arr = conform_targeted_broll(
            raw_backup,
            scale,
            dst_tx=dst_tx,
            dst_ty=dst_ty,
            crimson_phone_body=(fname == "tanki-burner-phone.png"),
        )
        _save_png(arr, case_dir / fname)
        _save_png(arr, PUBLIC_DIR / fname)
        processed.add(fname)
        print(
            f"Pixel-locked B-roll {fname:21s} -> 1080x1920 "
            f"(phone=({dst_tx*W:.0f}, {dst_ty*H:.0f}), scale={scale:.2f})"
        )

    known_case01 = set(CAST_SPECS) | {golu_dial} | set(BROLL_PLATES) | set(TARGETED_BROLL_SPECS)
    if args.auto_frame or broll_set:
        raw_candidates = [
            p
            for p in raw_dir.iterdir()
            if p.is_file()
            and p.suffix.lower() in _EXT_PRIORITY
            and "cast-sheet" not in p.name.lower()
        ]
        raw_candidates.sort(key=lambda p: (_EXT_PRIORITY[p.suffix.lower()], p.stem.lower(), p.name))
        raw_by_stem: dict[str, Path] = {}
        for cand in raw_candidates:
            raw_by_stem.setdefault(cand.stem, cand)

        for stem in sorted(raw_by_stem):
            raw_file = raw_by_stem[stem]
            out_fname = f"{raw_file.stem}.png"
            if out_fname in processed or (only_set and out_fname not in only_set):
                continue
            if out_fname in known_case01 and out_fname not in broll_set:
                continue
            lower_name = out_fname.lower()
            is_broll = out_fname in broll_set or any(kw in lower_name for kw in AUTO_BROLL_KEYWORDS)
            if is_broll:
                conform_broll(raw_file, case_dir / out_fname)
                conform_broll(raw_file, PUBLIC_DIR / out_fname)
                _apply_broll_lower_vignette(case_dir / out_fname, PUBLIC_DIR / out_fname)
                processed.add(out_fname)
                print(f"Conformed auto B-roll {out_fname:19s} -> 1080x1920")
            elif args.auto_frame:
                scale, cx, eye_y = estimate_auto_cast_spec(raw_file)
                arr = conform_portrait(raw_file, scale, cx, eye_y)
                _save_png(arr, case_dir / out_fname)
                _save_png(arr, PUBLIC_DIR / out_fname)
                processed.add(out_fname)
                print(f"Auto-framed cast {out_fname:24s} -> 1080x1920 (scale={scale:.3f}, cx={cx:.3f}, eye_y={eye_y:.3f})")

    # Rebuild 5-character standardized cast sheet on full default case01 runs
    cast_files = [
        case_dir / "kabir-investigating.png",
        case_dir / "sharma-shock.png",
        case_dir / "golu.png",
        case_dir / "ramu-kaka.png",
        case_dir / "pappu-chachu.png",
    ]
    if case_dir == CASE_DIR.resolve() and not only_set and all(cf.is_file() for cf in cast_files):
        sheet_out = case_dir / "case01-character-cast-sheet.png"
        inputs: list[str] = []
        for cf in cast_files:
            inputs.extend(["-i", str(cf)])
        filt = (
            "[0:v]scale=360:640:flags=lanczos[c0];"
            "[1:v]scale=360:640:flags=lanczos[c1];"
            "[2:v]scale=360:640:flags=lanczos[c2];"
            "[3:v]scale=360:640:flags=lanczos[c3];"
            "[4:v]scale=360:640:flags=lanczos[c4];"
            "[c0][c1][c2][c3][c4]hstack=inputs=5"
        )
        subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filt, str(sheet_out)], check=True)
        print(f"Updated cast sheet -> {sheet_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
