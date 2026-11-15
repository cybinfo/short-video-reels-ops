#!/usr/bin/env python3
"""Single-command self-healing episode orchestrator & launch-pack builder for Cyber Jasoos."""

from __future__ import annotations

import argparse, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import sync_episode_registry  # noqa: E402
from self_heal_rules import compute_rate_heal_adjustment, generate_launch_copy_pack, heal_dom_defects, heal_manifest_text_guards  # noqa: E402
from validate_episode import validate_manifest  # noqa: E402

VENV_PYTHON = REPO_ROOT / ".venv_audio" / "bin" / "python"
CHAR_DIR = REPO_ROOT / "engine" / "public" / "characters"
VOICE_LICENSE_MAP: dict[str, tuple[str, str]] = {
    "edge": ("edge_neural", "EDGE_READ_ALOUD_PREVIEW"),
    "kokoro": ("kokoro_neural", "APACHE_2_0"),
    "recorded": ("recorded", "OWN_VOICE"),
    "draft_say": ("draft_say", "MACOS_DRAFT"),
}


def _py(prefer_venv: bool = True) -> str:
    return str(VENV_PYTHON) if prefer_venv and VENV_PYTHON.is_file() else sys.executable


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _iter_scene_plates(obj: object, seen: list[str] | None = None) -> list[str]:
    out = seen if seen is not None else []
    if isinstance(obj, str) and obj.startswith("characters/") and obj.endswith(".png"):
        if (name := Path(obj).name) not in out:
            out.append(name)
    elif isinstance(obj, dict):
        for v in obj.values():
            _iter_scene_plates(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _iter_scene_plates(v, out)
    return out


def _compile_brief(brief_path: Path, output_manifest: Path | None) -> Path:
    if output_manifest is not None:
        output_manifest.parent.mkdir(parents=True, exist_ok=True)
    try:
        import compile_story_brief  # type: ignore

        res = compile_story_brief.compile_brief_file(brief_path, output_manifest)
        if output_manifest is not None:
            return output_manifest.resolve()
        if isinstance(res, Path):
            return res.resolve()
        if isinstance(res, str) and Path(res).is_file():
            return Path(res).resolve()
        if isinstance(res, tuple):
            for item in res:
                if isinstance(item, Path):
                    return item.resolve()
            for item in res:
                if isinstance(item, dict) and item.get("id"):
                    return (REPO_ROOT / "episodes" / f"{item['id']}.json").resolve()
        if isinstance(res, dict) and res.get("id"):
            return (REPO_ROOT / "episodes" / f"{res['id']}.json").resolve()
    except ImportError:
        cmd = [_py(True), str(SCRIPTS_DIR / "compile_story_brief.py"), "--brief", str(brief_path)]
        if output_manifest is not None:
            cmd.extend(["--output", str(output_manifest)])
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if output_manifest is not None:
            return output_manifest.resolve()
        for m in re.findall(r"([^\s\"']+\.json)", proc.stdout):
            cand = Path(m) if Path(m).is_absolute() else (REPO_ROOT / m)
            if cand.is_file() and not cand.name.endswith(".brief.json"):
                return cand.resolve()
    return (REPO_ROOT / "episodes" / f"{brief_path.stem}.json").resolve()


def _ensure_character_assets(manifest: dict, case_dir: Path | None) -> list[str]:
    actions: list[str] = []
    for plate in _iter_scene_plates(manifest.get("scenes", [])):
        clean_p, fg_p, bg_p = CHAR_DIR / plate, CHAR_DIR / "fg" / plate, CHAR_DIR / "bg" / f"{Path(plate).stem}.jpg"
        if not clean_p.is_file() and case_dir and case_dir.is_dir():
            stem = Path(plate).stem
            if any((d / f"{stem}{ext}").is_file() for d in (case_dir, case_dir / "raw") for ext in (".png", ".jpg", ".jpeg", ".webp")):
                subprocess.run([_py(True), str(SCRIPTS_DIR / "standardize_cast.py"), "--case-dir", str(case_dir), "--auto-frame", "--only", plate], check=True)
                actions.append(f"standardized:{plate}")
        if clean_p.is_file() and (not fg_p.is_file() or not bg_p.is_file()):
            subprocess.run([_py(True), str(SCRIPTS_DIR / "generate_depth_mattes.py"), "--only", plate, "--skip-existing"], check=True)
            actions.append(f"depth_matte:{plate}")
    return actions


def _sync_registry() -> bool:
    reg_script = SCRIPTS_DIR / "sync_episode_registry.py"
    if reg_script.is_file():
        subprocess.run([_py(False), str(reg_script)], check=True)
        return True
    return False


def _apply_voice_mode_meta(manifest: dict, voice_mode: str) -> bool:
    vc = manifest.setdefault("voiceConfig", {})
    target_mode, target_lic = VOICE_LICENSE_MAP[voice_mode]
    keep_comm = voice_mode == "edge" and vc.get("engineLicense") == "COMMERCIAL_API" and vc.get("azureSpeechRegion")
    eff_lic = "COMMERCIAL_API" if keep_comm else target_lic
    changed = vc.get("mode") != target_mode or vc.get("engineLicense") != eff_lic
    vc["mode"], vc["engineLicense"] = target_mode, eff_lic
    return changed


def _word_count(manifest: dict) -> int:
    return sum(len(str(s.get("narration", "")).split()) for s in (manifest.get("scriptSegments") or []))


def _run_voice_heal_loop(manifest_path: Path, voice_mode: str, voice_input: Path | None, max_iters: int) -> tuple[dict, list[str]]:
    manifest, heals = json.loads(manifest_path.read_text(encoding="utf-8")), []
    mode_changed = _apply_voice_mode_meta(manifest, voice_mode)
    manifest, pre_acts = heal_manifest_text_guards(manifest, validate_manifest(manifest))
    if mode_changed or pre_acts:
        heals.extend(f"pre:{a}" for a in pre_acts)
        _write_json(manifest_path, manifest)

    pv_mode, last_errs = ("draft" if voice_mode == "draft_say" else voice_mode), []
    for it in range(1, max_iters + 1):
        cmd = [_py(True), str(SCRIPTS_DIR / "prepare_voice.py"), "--episode", str(manifest_path), "--mode", pv_mode, "--sync-manifest", *(("--input", str(voice_input)) if voice_input else ())]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            if (m_dur := re.search(r"\((\d+(?:\.\d+)?)s\)", f"{proc.stderr}\n{proc.stdout}")) and it < max_iters:
                raw_dur = float(m_dur.group(1))
                manifest, reason = compute_rate_heal_adjustment(manifest, raw_dur, _word_count(manifest) / max(0.05, raw_dur / 60.0))
                if reason:
                    heals.append(f"voice_iter{it}:{reason}")
                    _write_json(manifest_path, manifest)
                    continue
            raise RuntimeError(f"prepare_voice.py failed:\n{proc.stderr.strip() or proc.stdout.strip()}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if _apply_voice_mode_meta(manifest, voice_mode):
            _write_json(manifest_path, manifest)
        if not (last_errs := validate_manifest(manifest, publish_ready=False)):
            return manifest, heals
        if it < max_iters:
            manifest, t_acts = heal_manifest_text_guards(manifest, last_errs)
            dur = float(manifest.get("durationSeconds") or 0.0)
            rate_reason = None
            if any("WPM" in e or "durationSeconds" in e for e in last_errs):
                manifest, rate_reason = compute_rate_heal_adjustment(manifest, dur, _word_count(manifest) / (dur / 60.0) if dur > 0 else 0.0)
            if t_acts or rate_reason:
                heals.extend(f"voice_iter{it}:{a}" for a in (*t_acts, *( [rate_reason] if rate_reason else [] )))
                _write_json(manifest_path, manifest)
                continue
        break
    raise RuntimeError(f"Manifest validation failed after {max_iters} iter(s): {last_errs}")


def _run_dom_heal_loop(manifest_path: Path, manifest: dict, max_iters: int) -> tuple[dict, list[str]]:
    ep_id, dom_heals = str(manifest["id"]), []
    report_path = REPO_ROOT / "renders" / "uat" / f"dom-audit-{ep_id}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    for it in range(1, max_iters + 1):
        report_path.unlink(missing_ok=True)
        proc = subprocess.run(
            ["node", str(REPO_ROOT / "engine" / "scripts" / "uat-dom-audit.mjs"), "--episode", str(manifest_path), "--report", str(report_path)],
            cwd=str(REPO_ROOT / "engine"), capture_output=True, text=True,
        )
        src_report = report_path if report_path.is_file() else (REPO_ROOT / "renders" / "uat" / "dom-audit-report.json")
        if not src_report.is_file():
            raise RuntimeError(f"DOM audit produced no report (rc={proc.returncode}): {proc.stderr.strip()}")
        raw_rep = json.loads(src_report.read_text(encoding="utf-8"))
        ep_defects = [d for d in (raw_rep.get("defects") or []) if d.get("episode") in (None, ep_id)]
        ep_errs = [e for e in (raw_rep.get("consoleErrors") or []) if e.get("episode") in (None, ep_id)]
        if not ep_defects and not ep_errs:
            return manifest, dom_heals
        if it < max_iters and ep_defects:
            manifest, acts = heal_dom_defects(manifest, {"defects": ep_defects})
            if acts:
                dom_heals.extend(f"dom_iter{it}:{a}" for a in acts)
                _write_json(manifest_path, manifest)
                _sync_registry()
                continue
        raise RuntimeError(f"DOM audit failed ({len(ep_defects)} defects, {len(ep_errs)} console errors): {ep_defects[:3]}")
    return manifest, dom_heals


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Cyber Jasoos single-command self-healing episode builder.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--brief", type=Path, help="Story brief YAML/JSON to compile into an episode manifest.")
    src.add_argument("--episode", type=Path, help="Existing episode manifest JSON path.")
    for flag, hlp in (("--output-manifest", "Destination manifest JSON."), ("--case-dir", "Raw character plate directory."),
                      ("--voice-input", "Recorded narration WAV/M4A."), ("--launch-pack-dir", "Output directory for launch pack."),
                      ("--mp4-output", "Explicit destination path for rendered MP4")):
        p.add_argument(flag, type=Path, help=hlp)
    p.add_argument("--voice-mode", choices=("edge", "kokoro", "recorded", "draft_say"), default="edge")
    p.add_argument("--max-heal-iters", type=int, default=3, help="Max self-healing iterations per gate (default: 3).")
    p.add_argument("--skip-dom-audit", action="store_true", help="Skip Headless Chrome DOM safe-zone audit.")
    p.add_argument("--render-mp4", action="store_true", help="Render final 1080x1920 @ 30fps MP4 via Remotion.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    out_m = args.output_manifest.resolve() if args.output_manifest else None
    manifest_path = _compile_brief(args.brief.resolve(), out_m) if args.brief else (out_m or args.episode.resolve())
    if not args.brief and manifest_path != args.episode.resolve():
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.episode.resolve(), manifest_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plate_actions = _ensure_character_assets(manifest, args.case_dir.resolve() if args.case_dir else None)
    _sync_registry()
    manifest, voice_heals = _run_voice_heal_loop(manifest_path, args.voice_mode, args.voice_input.resolve() if args.voice_input else None, max(1, args.max_heal_iters))
    _sync_registry()
    dom_heals = [] if args.skip_dom_audit else _run_dom_heal_loop(manifest_path, manifest, max(1, args.max_heal_iters))[1]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    ep_id = str(manifest["id"])
    plates = [CHAR_DIR / pl for pl in _iter_scene_plates(manifest.get("scenes", [])) if (CHAR_DIR / pl).is_file()]
    frame_png = plates[0] if plates else (CHAR_DIR / "kabir-closeup.png")
    pack_dir = args.launch_pack_dir.resolve() if args.launch_pack_dir else (REPO_ROOT / "renders" / f"launch-pack-{ep_id}")
    pack_dir.mkdir(parents=True, exist_ok=True)
    cover_out = (pack_dir / f"{ep_id}-reel-cover.png") if args.launch_pack_dir else (REPO_ROOT / "renders" / f"{ep_id}-reel-cover.png")
    subprocess.run([_py(True), str(SCRIPTS_DIR / "generate_ig_brand_kit.py"), "--episode", str(manifest_path), "--frame", str(frame_png), "--output", str(cover_out)], check=True)
    copy_out = generate_launch_copy_pack(manifest, pack_dir / "POST_COPY_AND_PINNED_COMMENT.txt")

    mp4_out: str | None = None
    if args.render_mp4:
        mp4_path = args.mp4_output.resolve() if args.mp4_output else (REPO_ROOT / "renders" / f"{ep_id}.mp4").resolve()
        mp4_path.parent.mkdir(parents=True, exist_ok=True)
        vc = manifest.get("voiceConfig") if isinstance(manifest.get("voiceConfig"), dict) else {}
        cap_rel = vc.get("captionsFile") or f"audio/{ep_id}.captions.json"
        cap_path = REPO_ROOT / "engine" / "public" / str(cap_rel)
        words_list = json.loads(cap_path.read_text(encoding="utf-8")) if cap_path.is_file() else []
        audio_rel = vc.get("audioFile") or f"audio/{ep_id}.wav"
        render_props = {
            "manifest": manifest,
            "words": words_list,
            "audioPublicPath": audio_rel,
            "showSafeZone": False,
        }
        registered_paths = {p.resolve() for p in sync_episode_registry.discover_episode_manifests()}
        comp_id = ep_id if manifest_path.resolve() in registered_paths else "dynamic-episode"
        tmp_props_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as tf:
                json.dump(render_props, tf, ensure_ascii=False)
                tmp_props_path = Path(tf.name)
            subprocess.run(
                ["npx", "remotion", "render", "src/index.ts", comp_id, str(mp4_path), f"--props={tmp_props_path}"],
                cwd=str(REPO_ROOT / "engine"),
                check=True,
            )
        finally:
            if tmp_props_path is not None:
                tmp_props_path.unlink(missing_ok=True)
        pack_mp4 = (pack_dir / f"{ep_id}.mp4").resolve()
        if args.launch_pack_dir and mp4_path != pack_mp4:
            shutil.copy2(mp4_path, pack_mp4)
        mp4_out = str(mp4_path)

    print(json.dumps({
        "status": "ok", "episodeId": ep_id, "manifestPath": str(manifest_path), "durationSeconds": manifest.get("durationSeconds"),
        "voiceMode": args.voice_mode, "plateActions": plate_actions, "voiceHealActions": voice_heals,
        "domAuditSkipped": bool(args.skip_dom_audit), "domHealActions": dom_heals,
        "coverPath": str(cover_out), "copyPackPath": str(copy_out), "mp4Path": mp4_out,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
