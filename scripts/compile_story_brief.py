#!/usr/bin/env python3
"""Compile a compact 30-35 line YAML/JSON story brief into a schema-valid noir_cinema EpisodeManifest."""

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from apply_poll_result import apply_poll_branch  # noqa: E402
from growth_ledger import load_learned_defaults  # noqa: E402
from story_brief_templates import (  # noqa: E402
    build_clauses, build_noir_scenes, build_post_copy, ensure_loop_suspension, expand_poll_branches, extract_keywords,
)
from validate_episode import REQUIRED_PHASES, validate_manifest  # noqa: E402

REPO_ROOT = SCRIPTS_DIR.parent
VENV_PYTHON = REPO_ROOT / ".venv_audio" / "bin" / "python"


def load_brief(path: Path) -> dict:
    """Load a story brief from .json natively or .yaml/.yml (falling back to .venv_audio PyYAML)."""
    brief_path = Path(path)
    if not brief_path.is_file():
        raise FileNotFoundError(f"Story brief not found: {brief_path}")
    suffix = brief_path.suffix.lower()
    if suffix == ".json":
        data = json.loads(brief_path.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
            data = yaml.safe_load(brief_path.read_text(encoding="utf-8"))
        except ImportError:
            if not VENV_PYTHON.is_file():
                raise RuntimeError(f"PyYAML unavailable in system python and {VENV_PYTHON} missing.") from None
            cmd = [
                str(VENV_PYTHON), "-c",
                "import json, sys, yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding='utf-8'))))",
                str(brief_path),
            ]
            proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
            data = json.loads(proc.stdout)
    else:
        raise ValueError(f"Unsupported brief extension '{suffix}' (expected .yaml, .yml, or .json).")
    if not isinstance(data, dict):
        raise ValueError("Story brief root must be a mapping/object.")
    return data


_MODE_LICENSES = {"recorded": "OWN_VOICE", "kokoro_neural": "APACHE_2_0", "azure_commercial": "COMMERCIAL_API", "edge_neural": "EDGE_READ_ALOUD_PREVIEW", "draft_say": "MACOS_DRAFT"}


def compile_brief(brief: dict, defaults_path: Path | None = None) -> dict:
    """Compile a parsed brief dictionary into a validated noir_cinema EpisodeManifest."""
    learned = load_learned_defaults(defaults_path)
    is_guide = str(brief.get("preset") or "crime_case").strip().lower() == "guide_walkthrough"
    season = int(brief.get("season") or 1)
    ep_num = int(brief.get("episodeNumber") or brief.get("episode") or 1)
    part = int(brief.get("part") or (2 if brief.get("pollBranches") else 1))
    company_name = str(brief.get("companyName") or "CYBER JASOOS")
    slug = re.sub(r"[^a-z0-9-]+", "-", str(brief.get("slug") or brief.get("title") or ("guide" if is_guide else "case")).lower()).strip("-")[:28]
    ep_id = str(brief.get("id") or f"s{season:02d}e{ep_num:02d}-{slug}")
    title = str(brief.get("title") or brief.get("episodeTitle") or (f"Guide #{ep_num:02d} Walkthrough" if is_guide else f"Case #{season:02d} Mystery"))
    season_title = str(brief.get("seasonTitle") or (f"Guide #{ep_num:02d}: {title}" if is_guide else f"Case #{season:02d}: {title}"))
    concept = str(brief.get("cyberConcept") or brief.get("securityDomain") or (f"{company_name} · GUIDE #{ep_num:02d}" if is_guide else f"CYBER JASOOS · CASE #{season:02d}"))
    raw_dom = str(brief.get("securityDomain") or (f"{company_name} · GUIDE #{ep_num:02d}" if is_guide else (f"CYBER JASOOS · CASE #{season:02d}" + (" FINALE" if part == 2 else "")))).strip()
    hud_domain = (raw_dom[:32].rsplit(" ", 1)[0] if len(raw_dom) > 32 and " " in raw_dom[:32] else raw_dom[:32]).rstrip(" ·—|,-:")
    case_tag = str(brief.get("caseTag") or brief.get("coldOpenTag") or (f"GUIDE #{ep_num:02d} · ZERO-AI" if is_guide else f"CASE #{season:02d} · LIVE JAANCH"))

    raw_inc = brief.get("realIncident") or brief.get("realBreachParallel") or {}
    real_inc = raw_inc if isinstance(raw_inc, dict) else {"incident": str(raw_inc), "year": 2024, "impact": str(raw_inc), "lesson": "35-line YAML brief auto-heals DOM & rate." if is_guide else "Verify before scanning and dial 1930 immediately."}
    real_inc = {
        "incident": str(real_inc.get("incident") or ("Deterministic 9:16 Reel Pipeline" if is_guide else "MHA I4C 1930 Cyber Fraud Advisory")),
        "year": int(real_inc.get("year") or 2024),
        "impact": str(real_inc.get("impact") or ("Eliminates manual timeline, caption, and safe-zone rework" if is_guide else "Unauthorized instant digital payment drain via social/technical trap")),
        "lesson": str(real_inc.get("lesson") or ("35-line YAML brief compiles & self-heals DOM/audio automatically." if is_guide else "Never enter UPI PIN to receive money and call 1930 in the golden hour.")),
    }

    beats_in = brief.get("beats") or {}
    seg_specs: list[dict] = []
    for idx, phase in enumerate(REQUIRED_PHASES, 1):
        raw_b = beats_in.get(phase)
        if not raw_b:
            raise ValueError(f"Brief missing required beat: beats.{phase}")
        b_obj = raw_b if isinstance(raw_b, dict) else {"narration": str(raw_b)}
        narr = " ".join(str(b_obj.get("narration") or "").split())
        if phase == "cliffhanger_vote":
            narr = ensure_loop_suspension(narr)
        spk = str(b_obj.get("speaker") or "narrator")
        clauses = b_obj.get("ttsClauses") or build_clauses(narr, spk, suspend_end=(phase == "cliffhanger_vote"))
        kws = b_obj.get("highlightKeywords") or extract_keywords(narr)
        seg_specs.append({"id": f"{ep_id}-seg-{idx:02d}", "phase": phase, "speaker": spk, "narration": narr, "ttsClauses": clauses, "highlightKeywords": kws})

    total_words = sum(len(s["narration"].split()) for s in seg_specs)
    target_wpm = max(145, min(185, int(brief.get("targetWpm") or learned.get("targetWpm") or 168)))
    raw_dur = float(brief.get("durationSeconds") or brief.get("targetDurationSec") or learned.get("targetDurationSec") or 52.0)
    if "durationSeconds" not in brief:
        lo_dur = max(42.0, math.ceil((total_words * 60.0 / 190.0) * 100) / 100.0) if (total_words > 0) else 42.0
        hi_dur = min(58.0, math.floor((total_words * 60.0 / 134.0) * 100) / 100.0) if (total_words > 0) else 58.0
        if lo_dur <= hi_dur:
            raw_dur = min(hi_dur, max(lo_dur, raw_dur))
    duration = round(min(58.0, max(42.0, raw_dur)), 2)

    weights = [max(8, len(s["narration"].split())) for s in seg_specs]
    w_total, acc = sum(weights), 0.0
    for idx, seg in enumerate(seg_specs):
        seg["startSec"] = 0 if idx == 0 else seg_specs[idx - 1]["endSec"]
        acc += weights[idx]
        seg["endSec"] = duration if idx == len(seg_specs) - 1 else round(duration * (acc / w_total), 2)

    raw_suspects = brief.get("suspects") or []
    suspects = [
        {
            "key": str(s.get("key")).upper(),
            "name": str(s.get("name")),
            "role": str(s.get("role") or (f"Stage {s.get('key')}" if is_guide else f"Suspect {s.get('key')}")),
            "timestampBadge": str(s.get("timestampBadge") or s.get("time") or f"CLUE {s.get('key')}"),
            "clue": str(s.get("clue") or ("Auto-Verified!" if is_guide else "Forensic Match!")),
            "image": str(s.get("image") or "characters/handoff-shadow.png"),
            **({"icon": str(s["icon"])} if s.get("icon") is not None else {}),
            **({"suspicious": bool(s["suspicious"])} if s.get("suspicious") is not None else {}),
        }
        for s in raw_suspects if isinstance(s, dict)
    ]
    if not suspects and is_guide:
        suspects = [
            {"key": "A", "name": "YAML Brief Compiler", "role": "Stage 1", "timestampBadge": "GATE 01", "clue": "35-Line Spec!", "image": "characters/kabir-closeup.png"},
            {"key": "B", "name": "Audio & WPM Sync", "role": "Stage 2", "timestampBadge": "GATE 02", "clue": "42-58s Lock!", "image": "characters/kabir-investigating.png"},
            {"key": "C", "name": "Headless DOM Heal", "role": "Stage 3", "timestampBadge": "GATE 03", "clue": "0 Overflows!", "image": "characters/handoff-shadow.png"},
        ]

    raw_stop = brief.get("scrollStopper") or {}
    stopper = raw_stop if isinstance(raw_stop, dict) else {"badge": case_tag, "text": str(raw_stop), "tone": "emerald" if is_guide else "danger"}
    stopper = {
        "badge": str(stopper.get("badge") or case_tag),
        "text": str(stopper.get("text") or title),
        "tone": str(stopper.get("tone") or ("emerald" if (is_guide or part != 1) else "danger")),
    }
    scenes = build_noir_scenes(ep_id, season, part, title, concept, case_tag, real_inc, brief, seg_specs, suspects, stopper)

    pref_hook = str(brief.get("hookPattern") or ("comment_callout" if part == 2 else ("contradiction_shock" if learned.get("preferredHookStyle") == "contradiction_shock" else "mid_breach_timestamp")))
    hook_obj: dict[str, object] = {"openingLine": seg_specs[0]["narration"], "hookPattern": pref_hook}
    if part == 2:
        prev = brief.get("previousVoteResult") or {}
        hook_obj["previousVoteResult"] = {
            "winningOption": str(prev.get("winningOption") or "C").upper(),
            "percentage": int(prev.get("percentage") or 74),
            "outcomeVerdict": str(prev.get("outcomeVerdict") or "74% suspected Option C before Kabir traced the full forensic chain."),
        }

    default_sfx = {"file": "sfx/soc-alert-ping.wav", "durationSec": 2.4, "volume": 0.22} if is_guide else {"file": "sfx/shaadi-distant-intro.wav", "durationSec": 3.6, "volume": 0.25}
    raw_sfx = brief.get("introSfx")
    if isinstance(raw_sfx, str) and raw_sfx.strip():
        intro_sfx = {**default_sfx, "file": raw_sfx.strip()}
    elif isinstance(raw_sfx, dict):
        intro_sfx = {
            "file": str(raw_sfx.get("file") or default_sfx["file"]),
            "durationSec": float(raw_sfx["durationSec"]) if raw_sfx.get("durationSec") is not None else default_sfx["durationSec"],
            "volume": float(raw_sfx["volume"]) if raw_sfx.get("volume") is not None else default_sfx["volume"],
        }
    else:
        intro_sfx = default_sfx

    voice_cfg: dict[str, object] = {
        "mode": "edge_neural", "engineLicense": "EDGE_READ_ALOUD_PREVIEW",
        "edgeVoices": {"narrator": "ur-IN-SalmanNeural", "kabir": "hi-IN-MadhurNeural"},
        "edgeRates": {"narrator": "+8%"}, "edgePitches": {"narrator": "-3Hz"}, "edgeFormants": {"narrator": 1.0},
        "audioFile": f"audio/{ep_id}.wav", "captionsFile": f"audio/{ep_id}.captions.json", "targetWpm": target_wpm,
    }
    if isinstance(raw_vc := brief.get("voiceConfig"), dict):
        for vk, vv in raw_vc.items():
            if vv is None:
                continue
            if isinstance(vv, dict) and isinstance(voice_cfg.get(vk), dict):
                voice_cfg[vk] = {**voice_cfg[vk], **vv}  # type: ignore[dict-item]
            else:
                voice_cfg[vk] = vv
        if "mode" in raw_vc and "engineLicense" not in raw_vc and str(voice_cfg["mode"]) in _MODE_LICENSES:
            voice_cfg["engineLicense"] = _MODE_LICENSES[str(voice_cfg["mode"])]

    manifest: dict[str, object] = {
        "id": ep_id, "season": season, "episode": ep_num,
        "totalEpisodesInSeason": int(brief.get("totalEpisodesInSeason") or 4),
        "seasonTitle": season_title, "episodeTitle": title, "companyName": company_name,
        "visualTheme": "noir_cinema", "coldOpenTag": case_tag,
        "hudPartBadge": str(brief.get("hudPartBadge") or f"PART {part}/2"),
        "introSfx": intro_sfx, "securityDomain": hud_domain, "realBreachParallel": real_inc,
        "voiceConfig": voice_cfg, "durationSeconds": duration, "fps": 30, "hook": hook_obj,
        "scriptSegments": seg_specs, "scenes": scenes,
        "postCopy": build_post_copy(title, concept, real_inc, seg_specs[0]["narration"], suspects, part, brief),
    }
    if isinstance(raw_labels := brief.get("speakerLabels"), dict):
        manifest["speakerLabels"] = {str(k): str(v) for k, v in raw_labels.items()}
    if part == 2 and isinstance(brief.get("pollBranches"), dict):
        manifest["pollBranches"] = expand_poll_branches(brief["pollBranches"], title, concept, real_inc, suspects, brief)
        pvr = hook_obj["previousVoteResult"]
        assert isinstance(pvr, dict)
        manifest = apply_poll_branch(manifest, str(pvr["winningOption"]), int(pvr["percentage"]))

    if errs := [e for e in validate_manifest(manifest) if not e.startswith("Caption Silence Guard:")]:
        raise ValueError("Compiled manifest failed validation:\n- " + "\n- ".join(errs))
    return manifest


def compile_brief_file(brief_path: Path, output_path: Path | None = None, defaults_path: Path | None = None) -> Path:
    """Load a YAML/JSON brief, compile it to an EpisodeManifest, write to disk, and return output_path."""
    src_path = Path(brief_path)
    manifest = compile_brief(load_brief(src_path), defaults_path)
    dst = Path(output_path) if output_path else (REPO_ROOT / "episodes" / f"{manifest['id']}.json")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dst


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compile a YAML/JSON Cyber Jasoos story brief into an EpisodeManifest.")
    ap.add_argument("brief_pos", nargs="?", help="Path to .yaml/.yml/.json story brief.")
    ap.add_argument("--brief", "-b", dest="brief_opt", help="Path to .yaml/.yml/.json story brief.")
    ap.add_argument("--output", "-o", help="Output EpisodeManifest .json path (prints to stdout if omitted).")
    ap.add_argument("--defaults", help="Optional path to learned_defaults.json.")
    args = ap.parse_args(argv)
    src = args.brief_opt or args.brief_pos
    if not src:
        ap.error("Provide a brief path positionally or via --brief.")
    manifest = compile_brief(load_brief(Path(src)), Path(args.defaults) if args.defaults else None)
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(rendered, encoding="utf-8")
        print(f"Compiled {manifest['id']} -> {out_p}")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
