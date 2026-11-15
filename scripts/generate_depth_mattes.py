#!/usr/bin/env python3
"""Generate neural 2.5D foreground RGBA mattes for all standardized 9:16 cinema plates.

Uses Apache-2.0 licensed `onnx-community/depth-anything-v2-small` (`onnx/model_fp16.onnx`)
via ONNX Runtime to separate foreground subjects/clues from background depth planes for
distortion-free 2.5D camera parallax and optical rack-focus in Remotion.
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

import numpy as np
from huggingface_hub import hf_hub_download
import onnxruntime as ort
from scipy.ndimage import gaussian_filter, zoom

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CHAR_DIR = REPO_ROOT / "engine" / "public" / "characters"
FG_DIR = CHAR_DIR / "fg"
BG_DIR = CHAR_DIR / "bg"

INFER_W, INFER_H = 518, 924  # Exact multiples of ViT patch size 14 (37x14, 66x14)
OUT_W, OUT_H = 1080, 1920


def _load_rgb(path: pathlib.Path, width: int, height: int) -> np.ndarray:
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


def _save_rgba_png(rgba: np.ndarray, path: pathlib.Path) -> None:
    height, width, _ = rgba.shape
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
            "rgba",
            "-s",
            f"{width}x{height}",
            "-i",
            "-",
            "-compression_level",
            "6",
            str(path),
        ],
        input=rgba.tobytes(),
        check=True,
    )


def _predict_foreground_alpha(session: ort.InferenceSession, rgb_infer: np.ndarray) -> np.ndarray:
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    norm = (rgb_infer.astype(np.float32) / 255.0 - mean) / std
    inp = np.transpose(norm, (2, 0, 1))[None, :, :, :].astype(np.float32)

    pred = session.run(None, {"pixel_values": inp})[0]
    # Depth-Anything-V2 outputs affine-invariant inverse depth (higher = closer to camera)
    depth = np.squeeze(pred).astype(np.float32)

    lo = float(np.percentile(depth, 5.0))
    hi = float(np.percentile(depth, 98.0))
    norm_d = np.clip((depth - lo) / max(1e-5, hi - lo), 0.0, 1.0)

    # Tightened optical foreground separation curve (zero double-edge halo on hair/shoulders against bg/*.jpg)
    alpha = 1.0 / (1.0 + np.exp(-(norm_d - 0.48) * 13.5))
    alpha = gaussian_filter(alpha, sigma=1.45)
    alpha = np.clip((alpha - 0.12) / 0.82, 0.0, 1.0)

    alpha_hi = zoom(alpha, (OUT_H / depth.shape[0], OUT_W / depth.shape[1]), order=1)
    return np.clip(alpha_hi, 0.0, 1.0)


def build_qa_strip(qa_out: pathlib.Path, samples: list[str]) -> None:
    panels: list[np.ndarray] = []
    for name in samples:
        bg = _load_rgb(CHAR_DIR / name, 360, 640).astype(np.float32)
        raw_fg = subprocess.check_output(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(FG_DIR / name),
                "-vf",
                "scale=360:640:flags=lanczos",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgba",
                "-",
            ]
        )
        fg = np.frombuffer(raw_fg, dtype=np.uint8).reshape(640, 360, 4).astype(np.float32)
        alpha = fg[:, :, 3:4] / 255.0

        # Visualize matte alpha in cyan-gold tint next to simulated parallax rack-focus composite
        matte_vis = np.zeros((640, 360, 3), dtype=np.float32)
        matte_vis[:, :, 0] = fg[:, :, 0] * alpha[:, :, 0]
        matte_vis[:, :, 1] = fg[:, :, 1] * alpha[:, :, 0] + 35.0 * alpha[:, :, 0]
        matte_vis[:, :, 2] = fg[:, :, 2] * alpha[:, :, 0] + 55.0 * alpha[:, :, 0]

        bg_blur = np.stack([gaussian_filter(bg[:, :, c], sigma=3.5) for c in range(3)], axis=-1) * 0.78
        shifted_fg = np.roll(fg[:, :, :3], shift=10, axis=1)
        shifted_a = np.roll(alpha, shift=10, axis=1)
        comp = bg_blur * (1.0 - shifted_a) + shifted_fg * shifted_a

        row = np.concatenate(
            [
                np.clip(bg, 0, 255).astype(np.uint8),
                np.clip(matte_vis, 0, 255).astype(np.uint8),
                np.clip(comp, 0, 255).astype(np.uint8),
            ],
            axis=1,
        )
        panels.append(row)

    grid = np.concatenate(panels, axis=0)
    qa_out.parent.mkdir(parents=True, exist_ok=True)
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
            f"{grid.shape[1]}x{grid.shape[0]}",
            "-i",
            "-",
            str(qa_out),
        ],
        input=grid.tobytes(),
        check=True,
    )


from collections.abc import Sequence


def _normalize_plate_names(items: Sequence[str] | None) -> set[str]:
    names: set[str] = set()
    for raw in items or ():
        for part in raw.split(","):
            tok = part.strip()
            if not tok:
                continue
            base = pathlib.Path(tok).name
            names.add(base if base.lower().endswith(".png") else f"{base}.png")
    return names


def _load_depth_session() -> ort.InferenceSession:
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
    return ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="PLATE_NAME",
        help="Generate depth mattes only for specified plate(s) (repeatable; .png optional)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip plates whose fg/<plate>.png and bg/<stem>.jpg already exist",
    )
    parser.add_argument("--qa-out", type=pathlib.Path, default=None, help="Optional QA contact strip PNG")
    args = parser.parse_args(argv)

    FG_DIR.mkdir(parents=True, exist_ok=True)
    BG_DIR.mkdir(parents=True, exist_ok=True)
    plates = sorted(p for p in CHAR_DIR.glob("*.png") if p.is_file())
    if not plates:
        raise RuntimeError(f"No character plates found in {CHAR_DIR}")

    only_set = _normalize_plate_names(args.only)
    if only_set:
        plates = [p for p in plates if p.name in only_set]
        if not plates:
            raise RuntimeError(f"Requested --only plate(s) not found in {CHAR_DIR}: {sorted(only_set)}")

    if args.skip_existing:
        pending_plates = [
            p
            for p in plates
            if not ((FG_DIR / p.name).is_file() and (BG_DIR / f"{p.stem}.jpg").is_file())
        ]
        skipped_count = len(plates) - len(pending_plates)
        if skipped_count and not pending_plates:
            print(f"Skipped {skipped_count} existing depth matte(s) (--skip-existing); 0 pending.")
    else:
        pending_plates = plates

    if pending_plates:
        session = _load_depth_session()
        for plate in pending_plates:
            bg_dst = BG_DIR / f"{plate.stem}.jpg"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-i",
                    str(plate),
                    "-vf",
                    "scale=540:960:flags=lanczos,gblur=sigma=2.4,eq=contrast=0.98:brightness=-0.05",
                    "-q:v",
                    "3",
                    str(bg_dst),
                ],
                check=True,
            )
            rgb_infer = _load_rgb(plate, INFER_W, INFER_H)
            rgb_out = _load_rgb(plate, OUT_W, OUT_H)
            alpha = _predict_foreground_alpha(session, rgb_infer)
            rgba = np.zeros((OUT_H, OUT_W, 4), dtype=np.uint8)
            rgba[:, :, :3] = rgb_out
            rgba[:, :, 3] = np.clip(np.rint(alpha * 255.0), 0, 255).astype(np.uint8)
            dst = FG_DIR / plate.name
            _save_rgba_png(rgba, dst)
            fg_cov = float((alpha > 0.5).mean() * 100.0)
            print(f"Depth matte {plate.name:26s} -> fg/{plate.name} ({OUT_W}x{OUT_H}, fg_cov={fg_cov:4.1f}%)")

    if args.qa_out is not None:
        sample_names = [
            n
            for n in ("golu-phone-dial.png", "handoff-shadow.png", "tanki-burner-phone.png")
            if (FG_DIR / n).exists()
        ]
        if sample_names:
            build_qa_strip(args.qa_out, sample_names)
            print(f"Wrote QA strip -> {args.qa_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
