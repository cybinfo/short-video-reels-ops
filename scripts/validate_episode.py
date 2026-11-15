#!/usr/bin/env python3
"""Formula-driven manifest & retention validator for Cyber Jasoos / BreachZero short episodes."""

import argparse, json, os, re, sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from apply_poll_result import _pct_words, _render_templates, apply_poll_branch  # noqa: E402

REPO_ROOT = SCRIPTS_DIR.parent
ID_PATTERN, TIMELINE_EPS = re.compile(r"^s\d{2}e\d{2}-[a-z0-9-]+$"), 1e-3
REQUIRED_TOP_FIELDS = (
    "id", "season", "episode", "totalEpisodesInSeason", "seasonTitle", "episodeTitle", "companyName",
    "securityDomain", "realBreachParallel", "voiceConfig", "durationSeconds", "fps", "hook", "scriptSegments",
    "scenes", "postCopy",
)
ALLOWED_VOICE_LICENSES = {
    "OWN_VOICE", "COMMERCIAL_API", "APACHE_2_0", "MIT", "EDGE_READ_ALOUD_PREVIEW", "MACOS_DRAFT",
}
PREVIEW_VOICE_LICENSES = {"EDGE_READ_ALOUD_PREVIEW", "MACOS_DRAFT"}
ALLOWED_VOICE_MODES = {"recorded", "commercial_clone", "draft_say", "kokoro_neural", "edge_neural"}
ALLOWED_VISUAL_THEMES = {"bright_detective", "dark_cyber", "noir_cinema"}
ALLOWED_HOOK_PATTERNS = {"comment_callout", "mid_breach_timestamp", "contradiction_shock"}
ALLOWED_SPEAKERS = {"jyoti", "rajat", "narrator", "kabir", "sharma", "chachu"}
REQUIRED_PHASES = ("hook", "escalation", "framework", "micro_payoff", "cliffhanger_vote")
ALLOWED_SCENE_KINDS = {
    "comment_spotlight", "breach_terminal", "network_attack_graph",
    "asset_tier_matrix", "risk_heatmap", "payoff_proof_card", "vote_cliffhanger",
    "detective_crime_hook", "detective_wifi_clue", "detective_evidence_twist", "detective_suspect_board",
}
GENERIC_HOOK_FILLERS = (
    "in this video", "welcome back", "today we will", "hey guys",
    "let's explore", "lets explore", "have you ever wondered what",
)


def _is_num(val: object) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _starts_with_filler(text: str) -> str | None:
    cleaned = re.sub(r"^[\s\"'“”‘’(\[]+", "", text).lower()
    return next((f for f in GENERIC_HOOK_FILLERS if cleaned.startswith(f)), None)


def _ends_with_pitch_drop_stop(text: str) -> bool:
    s = re.sub(r"[\s\"'”’)\]]+$", "", str(text))
    if not s:
        return False
    if s.endswith(("۔", "।")):
        return True
    return s.endswith(".") and not s.endswith("...")


def _iter_strings(obj: object):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_strings(v)


def _resolve_caption_path(cap_file: str) -> Path | None:
    raw_p = Path(cap_file)
    candidates = [raw_p] if raw_p.is_absolute() else [REPO_ROOT / "engine" / "public" / cap_file, REPO_ROOT / cap_file]
    return next((p for p in candidates if p.is_file()), None)


def _check_timeline(items: list, duration: float, label: str, errors: list[str]) -> None:
    if not items:
        errors.append(f"{label} must be a non-empty list.")
        return
    prev_end = 0.0
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{idx}] must be an object.")
            return
        start = item.get("startSec")
        end = item.get("endSec")
        if not (_is_num(start) and _is_num(end)):
            errors.append(f"{label}[{idx}] startSec/endSec must be numbers.")
            return
        if end <= start:
            errors.append(f"{label}[{idx}] endSec ({end}) must exceed startSec ({start}).")
        if idx == 0 and abs(float(start) - 0.0) > TIMELINE_EPS:
            errors.append(f"{label}[0] must start at 0s (got {start}).")
        elif idx > 0:
            diff = float(start) - prev_end
            if diff < -TIMELINE_EPS:
                errors.append(f"{label}[{idx}] overlaps previous end ({start} < {prev_end}).")
            elif diff > TIMELINE_EPS:
                errors.append(f"{label}[{idx}] leaves timeline gap ({prev_end} -> {start}).")
        prev_end = float(end)
    if abs(prev_end - duration) > TIMELINE_EPS:
        errors.append(f"{label} end ({prev_end}) must equal durationSeconds ({duration}).")


def validate_manifest(data: dict, publish_ready: bool = False) -> list[str]:
    if not isinstance(data, dict):
        return ["Manifest root must be a JSON object."]
    errors = [f"Missing required top-level field: '{f}'." for f in REQUIRED_TOP_FIELDS if data.get(f) is None]

    ep_id = data.get("id")
    if not isinstance(ep_id, str) or not ID_PATTERN.match(ep_id):
        errors.append(f"Invalid 'id' '{ep_id}': must match ^s\\d{{2}}e\\d{{2}}-[a-z0-9-]+$.")

    vis_theme = data.get("visualTheme")
    if vis_theme is not None and vis_theme not in ALLOWED_VISUAL_THEMES:
        errors.append(f"Invalid 'visualTheme' '{vis_theme}': must be in {sorted(ALLOWED_VISUAL_THEMES)}.")
    if vis_theme == "noir_cinema":
        for req_noir in ("coldOpenTag", "hudPartBadge"):
            if not isinstance(data.get(req_noir), str) or not data[req_noir].strip():
                errors.append(f"noir_cinema requires non-empty top-level '{req_noir}'.")
    if (intro_sfx := data.get("introSfx")) is not None:
        if not isinstance(intro_sfx, dict) or not isinstance(intro_sfx.get("file"), str) or not intro_sfx["file"].strip():
            errors.append("introSfx must be an object with non-empty 'file'.")

    duration = data.get("durationSeconds")
    valid_duration = _is_num(duration) and 42 <= float(duration) <= 58
    if not valid_duration:
        errors.append(f"'durationSeconds' ({duration}) must be in [42, 58].")
    if not (isinstance(data.get("fps"), int) and not isinstance(data.get("fps"), bool) and data.get("fps") == 30):
        errors.append(f"'fps' ({data.get('fps')}) must equal 30.")

    voice = data.get("voiceConfig")
    if isinstance(voice, dict):
        lic, v_mode, az_reg = voice.get("engineLicense"), voice.get("mode"), voice.get("azureSpeechRegion")
        if az_reg is not None and not isinstance(az_reg, str):
            errors.append("voiceConfig.azureSpeechRegion must be a string.")
        if lic == "CC-BY-NC" or lic not in ALLOWED_VOICE_LICENSES:
            errors.append(f"Commercial Voice License Guard: engineLicense '{lic}' blocked.")
        if v_mode not in ALLOWED_VOICE_MODES:
            errors.append(f"voiceConfig.mode '{v_mode}' invalid.")
        elif lic in ALLOWED_VOICE_LICENSES:
            if v_mode == "edge_neural":
                has_azure = isinstance(az_reg, str) and bool(az_reg.strip())
                allowed_edge = {"EDGE_READ_ALOUD_PREVIEW", "COMMERCIAL_API"} if has_azure else {"EDGE_READ_ALOUD_PREVIEW"}
                if lic not in allowed_edge:
                    errors.append(
                        f"Commercial Voice License Guard: mode 'edge_neural' requires 'EDGE_READ_ALOUD_PREVIEW' "
                        f"(or 'COMMERCIAL_API' with non-empty azureSpeechRegion), got '{lic}'."
                    )
            elif v_mode == "draft_say" and lic != "MACOS_DRAFT":
                errors.append(f"Commercial Voice License Guard: mode 'draft_say' requires 'MACOS_DRAFT', got '{lic}'.")
            elif v_mode == "recorded" and lic != "OWN_VOICE":
                errors.append(f"Commercial Voice License Guard: mode 'recorded' requires 'OWN_VOICE', got '{lic}'.")
            elif v_mode == "kokoro_neural" and lic != "APACHE_2_0":
                errors.append(f"Commercial Voice License Guard: mode 'kokoro_neural' requires 'APACHE_2_0', got '{lic}'.")
        if publish_ready and lic in PREVIEW_VOICE_LICENSES:
            errors.append(
                f"Publish-Ready License Guard: engineLicense '{lic}' is preview/draft only and cannot be published commercially."
            )
        for edge_field in ("edgeVoices", "edgeRates", "edgePitches"):
            if voice.get(edge_field) is not None and not isinstance(voice.get(edge_field), dict):
                errors.append(f"voiceConfig.{edge_field} must be an object.")
        if (edge_formants := voice.get("edgeFormants")) is not None:
            if not isinstance(edge_formants, dict):
                errors.append("voiceConfig.edgeFormants must be an object.")
            else:
                for spk_k, fmt_v in edge_formants.items():
                    if not (_is_num(fmt_v) and 0.85 <= float(fmt_v) <= 1.25):
                        errors.append(f"voiceConfig.edgeFormants.{spk_k} ({fmt_v}) must be a number in [0.85, 1.25].")
        if isinstance(voice.get("captionsFile"), str) and voice["captionsFile"].strip():
            if (cap_path := _resolve_caption_path(voice["captionsFile"].strip())) is not None:
                try:
                    cap_words = json.loads(cap_path.read_text(encoding="utf-8"))
                    if isinstance(cap_words, list):
                        for w_i, w_obj in enumerate(cap_words):
                            if not isinstance(w_obj, dict):
                                continue
                            pks = w_obj.get("peak")
                            if isinstance(pks, list) and pks:
                                max_pk = max((float(x) for x in pks if _is_num(x)), default=0.0)
                                if max_pk < 0.04:
                                    errors.append(
                                        f"Caption Silence Guard: {cap_path.name} word[{w_i}] {w_obj.get('word')!r} "
                                        f"(@{w_obj.get('startSec')}s) has max(peak)={max_pk:.3f} < 0.04."
                                    )
                            elif vis_theme == "noir_cinema":
                                errors.append(f"Caption Silence Guard: {cap_path.name} word[{w_i}] missing loudness 'peak' array.")
                except Exception as exc:
                    errors.append(f"Caption Silence Guard: failed to parse '{cap_path}': {exc}")
    else:
        errors.append("'voiceConfig' must be an object.")

    hook = data.get("hook")
    if isinstance(hook, dict):
        opening, pattern, prev_vote = hook.get("openingLine", ""), hook.get("hookPattern"), hook.get("previousVoteResult")
        if not isinstance(opening, str) or len(opening.strip()) < 15:
            errors.append("hook.openingLine must be at least 15 chars.")
        elif bad := _starts_with_filler(opening):
            errors.append(f"Anti-Swipe Hook Guard: hook.openingLine starts with '{bad}'.")
        if pattern not in ALLOWED_HOOK_PATTERNS:
            errors.append(f"hook.hookPattern '{pattern}' invalid.")
        if pattern == "comment_callout" and not isinstance(prev_vote, dict):
            errors.append("hook.previousVoteResult is required when hookPattern is 'comment_callout'.")
        if prev_vote is not None:
            if not isinstance(prev_vote, dict):
                errors.append("hook.previousVoteResult must be an object.")
            else:
                if prev_vote.get("winningOption") not in {"A", "B", "C"}:
                    errors.append("hook.previousVoteResult.winningOption must be A, B, or C.")
                if not (_is_num(prev_vote.get("percentage")) and 1 <= float(prev_vote["percentage"]) <= 99):
                    errors.append("hook.previousVoteResult.percentage must be in [1, 99].")
    else:
        errors.append("'hook' must be an object.")

    segments = data.get("scriptSegments")
    if isinstance(segments, list) and segments:
        if valid_duration:
            _check_timeline(segments, float(duration), "scriptSegments", errors)
        first_narr = segments[0].get("narration", "") if isinstance(segments[0], dict) else ""
        if isinstance(first_narr, str) and (bad_seg := _starts_with_filler(first_narr)):
            errors.append(f"Anti-Swipe Hook Guard: scriptSegments[0] starts with '{bad_seg}'.")
        if vis_theme == "noir_cinema" and isinstance(hook, dict) and isinstance(hook.get("openingLine"), str) and isinstance(first_narr, str):
            if hook["openingLine"].strip() != first_narr.strip():
                errors.append("noir_cinema requires hook.openingLine to match scriptSegments[0].narration verbatim.")
        phases_seen, total_words = set(), 0
        for idx, seg in enumerate(segments):
            if not isinstance(seg, dict):
                continue
            if seg.get("phase") not in REQUIRED_PHASES:
                errors.append(f"scriptSegments[{idx}] has invalid phase '{seg.get('phase')}'.")
            else:
                phases_seen.add(seg["phase"])
            if (seg_spk := seg.get("speaker")) is not None and seg_spk not in ALLOWED_SPEAKERS:
                errors.append(f"scriptSegments[{idx}] has invalid speaker '{seg_spk}'.")
            if isinstance(seg.get("ttsClauses"), list):
                for c_idx, cl in enumerate(seg["ttsClauses"]):
                    if isinstance(cl, dict) and (cl_spk := cl.get("speaker")) is not None and cl_spk not in ALLOWED_SPEAKERS:
                        errors.append(f"scriptSegments[{idx}].ttsClauses[{c_idx}] has invalid speaker '{cl_spk}'.")
            total_words += len(seg["narration"].split()) if isinstance(seg.get("narration"), str) else 0
        if vis_theme == "noir_cinema" and isinstance(segments[-1], dict):
            last_clauses = segments[-1].get("ttsClauses")
            if isinstance(last_clauses, list) and last_clauses and isinstance(last_clauses[-1], dict):
                last_cl = last_clauses[-1]
                tts_end = str(last_cl.get("tts") if last_cl.get("tts") is not None else last_cl.get("hi", ""))
                rom_end = str(last_cl.get("roman", ""))
                if _ends_with_pitch_drop_stop(tts_end) or _ends_with_pitch_drop_stop(rom_end):
                    errors.append(
                        "Loop Suspension Guard: noir_cinema final ttsClauses[-1] must not end with pitch-dropping stop ('۔', '।', or single '.')."
                    )
        if missing := [p for p in REQUIRED_PHASES if p not in phases_seen]:
            errors.append(f"scriptSegments missing required phases: {missing}.")
        if _is_num(duration) and float(duration) > 0 and not (130.0 <= (wpm := total_words / (float(duration) / 60.0)) <= 195.0):
            errors.append(f"Speaking rate {wpm:.1f} WPM outside [130, 195] WPM.")
    else:
        errors.append("'scriptSegments' must be a non-empty list.")

    scenes = data.get("scenes")
    if isinstance(scenes, list) and scenes:
        if valid_duration:
            _check_timeline(scenes, float(duration), "scenes", errors)
        kinds = [sc.get("kind") if isinstance(sc, dict) else None for sc in scenes]
        for idx, sc in enumerate(scenes):
            sc_props = sc.get("props") if isinstance(sc, dict) and isinstance(sc.get("props"), dict) else {}
            if isinstance(sc, dict) and (sfx_cues := sc.get("sfxCues")) is not None:
                if not isinstance(sfx_cues, list) or not all(isinstance(c, dict) and isinstance(c.get("file"), str) and c["file"].strip() for c in sfx_cues):
                    errors.append(f"scenes[{idx}].sfxCues must be a list of objects with non-empty 'file'.")
            if kinds[idx] not in ALLOWED_SCENE_KINDS:
                errors.append(f"scenes[{idx}] has invalid kind '{kinds[idx]}'.")
            elif kinds[idx] == "comment_spotlight":
                if sc_props.get("optionPicked") not in {"A", "B", "C"}:
                    errors.append(f"scenes[{idx}] comment_spotlight.optionPicked must be A, B, or C.")
                if sc_props.get("verdictTone") not in {"danger", "success", "warning"}:
                    errors.append(f"scenes[{idx}] comment_spotlight.verdictTone must be danger, success, or warning.")
            elif kinds[idx] == "asset_tier_matrix":
                active_tier, tiers = sc_props.get("activeTier"), sc_props.get("tiers")
                if isinstance(active_tier, str) and active_tier.strip() and isinstance(tiers, list) and tiers:
                    active_q = active_tier.strip().lower()
                    if not any(
                        isinstance(t, dict) and (
                            str(t.get("name", "")).strip().lower() == active_q
                            or str(t.get("tag", "")).strip().lower() == active_q
                            or f"tier {t.get('rank')}".lower() == active_q
                        )
                        for t in tiers
                    ):
                        errors.append(
                            f"scenes[{idx}] asset_tier_matrix.activeTier '{active_tier}' matches no tier name, tag, or 'Tier <rank>'."
                        )
            if vis_theme == "noir_cinema":
                if kinds[idx] == "detective_crime_hook":
                    for req_p in ("mode", "cutRatios", "scrollStopper", "shotTitles", "shotTags"):
                        if not sc_props.get(req_p):
                            errors.append(f"scenes[{idx}] noir_cinema detective_crime_hook missing required prop '{req_p}'.")
                elif kinds[idx] == "detective_suspect_board":
                    for req_p in ("boardMode", "followHandleLine"):
                        if not isinstance(sc_props.get(req_p), str) or not sc_props[req_p].strip():
                            errors.append(f"scenes[{idx}] noir_cinema detective_suspect_board missing required prop '{req_p}'.")
                for s_val in _iter_strings(sc_props):
                    if s_val.startswith("characters/") and s_val.endswith(".png"):
                        if not (REPO_ROOT / "engine" / "public" / s_val).is_file():
                            errors.append(f"scenes[{idx}] missing character asset under engine/public/: '{s_val}'.")
        if "payoff_proof_card" not in kinds and "detective_evidence_twist" not in kinds:
            errors.append("scenes must include at least one 'payoff_proof_card' or 'detective_evidence_twist'.")
        last_sc = scenes[-1] if isinstance(scenes[-1], dict) else {}
        last_kind = last_sc.get("kind")
        if last_kind not in {"vote_cliffhanger", "detective_suspect_board"}:
            errors.append("Final scene must be 'vote_cliffhanger' or 'detective_suspect_board'.")
        else:
            last_props = last_sc.get("props") if isinstance(last_sc.get("props"), dict) else {}
            opts = last_props.get("options") if last_kind == "vote_cliffhanger" else last_props.get("suspects")
            keys = [o.get("key") if isinstance(o, dict) else None for o in (opts if isinstance(opts, list) else [])]
            if len(keys) != 3 or set(keys) != {"A", "B", "C"}:
                errors.append(f"{last_kind} must contain exactly 3 options/suspects (A, B, C).")
    else:
        errors.append("'scenes' must be a non-empty list.")

    post = data.get("postCopy")
    if isinstance(post, dict):
        if not isinstance(post.get("youtubeShortsTitle"), str) or not (0 < len(post["youtubeShortsTitle"]) <= 100):
            errors.append("postCopy.youtubeShortsTitle must be 1..100 characters.")
        if not isinstance(post.get("hashtags"), list) or not (4 <= len(post["hashtags"]) <= 10):
            errors.append("postCopy.hashtags must contain between 4 and 10 hashtags.")
        pinned = post.get("pinnedCommentVote", "")
        if not isinstance(pinned, str) or not all(re.search(rf"\b{opt}\b", pinned) for opt in ("A", "B", "C")):
            errors.append("postCopy.pinnedCommentVote must mention options A, B, and C.")
    else:
        errors.append("'postCopy' must be an object.")

    if (poll_branches := data.get("pollBranches")) is not None:
        if not isinstance(poll_branches, dict):
            errors.append("'pollBranches' must be an object containing keys A, B, and C.")
        else:
            missing_b = [k for k in ("A", "B", "C") if k not in poll_branches]
            extra_b = [k for k in poll_branches if k not in {"A", "B", "C"}]
            if missing_b:
                errors.append(f"pollBranches missing required branch key(s): {missing_b}.")
            if extra_b:
                errors.append(f"pollBranches has unknown branch key(s): {extra_b}.")
            req_branch_fields = ("episodeTitle", "coldOpenTag", "outcomeVerdict", "openingLine", "seg01", "scene01Props", "postCopy")
            for b_key in ("A", "B", "C"):
                b_obj = poll_branches.get(b_key)
                if b_key not in poll_branches:
                    continue
                if not isinstance(b_obj, dict):
                    errors.append(f"pollBranches.{b_key} must be an object.")
                    continue
                for bf in req_branch_fields:
                    if b_obj.get(bf) is None:
                        errors.append(f"pollBranches.{b_key} missing required field '{bf}'.")
                b_seg = b_obj.get("seg01")
                if isinstance(b_seg, dict):
                    for sf in ("narration", "ttsClauses", "highlightKeywords"):
                        if not b_seg.get(sf):
                            errors.append(f"pollBranches.{b_key}.seg01 missing required field '{sf}'.")
                elif b_seg is not None:
                    errors.append(f"pollBranches.{b_key}.seg01 must be an object.")
                b_sc1 = b_obj.get("scene01Props")
                if isinstance(b_sc1, dict):
                    for pf in ("phoneStatus", "scrollStopper", "shotTitles"):
                        if not b_sc1.get(pf):
                            errors.append(f"pollBranches.{b_key}.scene01Props missing required field '{pf}'.")
                elif b_sc1 is not None:
                    errors.append(f"pollBranches.{b_key}.scene01Props must be an object.")
                b_post = b_obj.get("postCopy")
                if isinstance(b_post, dict):
                    for cpf in ("instagramCaption", "youtubeShortsTitle", "linkedinPost", "pinnedCommentVote", "hashtags"):
                        if not b_post.get(cpf):
                            errors.append(f"pollBranches.{b_key}.postCopy missing required field '{cpf}'.")
                elif b_post is not None:
                    errors.append(f"pollBranches.{b_key}.postCopy must be an object.")

                for sample_pct in (38, 74):
                    try:
                        pw, pu = _pct_words(sample_pct)
                        rendered_branch = _render_templates(b_obj, {"pct": str(sample_pct), "pct_word": pw, "pct_urdu": pu})
                        branched = apply_poll_branch(data, b_key, sample_pct)
                    except Exception as exc:
                        errors.append(f"pollBranches.{b_key}@{sample_pct}% failed to render: {exc}")
                        continue
                    active_view = {k: v for k, v in branched.items() if k != "pollBranches"}
                    for s_txt in list(_iter_strings(rendered_branch)) + list(_iter_strings(active_view)):
                        if "{pct" in s_txt:
                            errors.append(f"pollBranches.{b_key}@{sample_pct}% left unresolved placeholder in: {s_txt[:80]!r}.")
                            break
                    b_segs = branched.get("scriptSegments")
                    if isinstance(b_segs, list) and b_segs and _is_num(duration) and float(duration) > 0:
                        b_words = sum(len(s["narration"].split()) for s in b_segs if isinstance(s, dict) and isinstance(s.get("narration"), str))
                        b_wpm = b_words / (float(duration) / 60.0)
                        if not (130.0 <= b_wpm <= 195.0):
                            errors.append(f"pollBranches.{b_key}@{sample_pct}% speaking rate {b_wpm:.1f} WPM outside [130, 195] WPM.")
                        if vis_theme == "noir_cinema":
                            b_open = (branched.get("hook") or {}).get("openingLine", "")
                            b_first = b_segs[0].get("narration", "") if isinstance(b_segs[0], dict) else ""
                            if str(b_open).strip() != str(b_first).strip():
                                errors.append(f"pollBranches.{b_key}@{sample_pct}% openingLine does not match seg01.narration verbatim.")

    return errors


def validate_season_continuity(manifests: list[dict]) -> list[str]:
    errors, by_season = [], {}
    for m in manifests:
        if isinstance(m, dict) and isinstance(m.get("season"), int) and isinstance(m.get("episode"), int):
            by_season.setdefault(m["season"], []).append(m)
    for eps in by_season.values():
        ordered = sorted(eps, key=lambda x: x["episode"])
        for ep_prev, ep_next in zip(ordered, ordered[1:]):
            if ep_next["episode"] != ep_prev["episode"] + 1:
                continue
            prev_scenes = ep_prev.get("scenes") if isinstance(ep_prev.get("scenes"), list) else []
            last_sc = prev_scenes[-1] if prev_scenes and isinstance(prev_scenes[-1], dict) else {}
            last_props = last_sc.get("props") if isinstance(last_sc.get("props"), dict) else {}
            raw_choices = (
                last_props.get("options") if last_sc.get("kind") == "vote_cliffhanger"
                else last_props.get("suspects") if last_sc.get("kind") == "detective_suspect_board"
                else []
            )
            prev_opts = {
                o["key"] for o in (raw_choices or [])
                if isinstance(o, dict) and isinstance(o.get("key"), str)
            }
            next_hook = ep_next.get("hook") if isinstance(ep_next.get("hook"), dict) else {}
            if isinstance(prev_vote := next_hook.get("previousVoteResult"), dict):
                win_opt = prev_vote.get("winningOption")
                if win_opt not in prev_opts:
                    errors.append(
                        f"Continuity ({ep_prev.get('id')} -> {ep_next.get('id')}): "
                        f"hook.previousVoteResult.winningOption '{win_opt}' not in {sorted(prev_opts)}."
                    )
            for idx, sc in enumerate(ep_next.get("scenes") or []):
                if isinstance(sc, dict) and sc.get("kind") == "comment_spotlight":
                    picked = (sc.get("props") if isinstance(sc.get("props"), dict) else {}).get("optionPicked")
                    if picked not in prev_opts:
                        errors.append(
                            f"Continuity ({ep_prev.get('id')} -> {ep_next.get('id')}): "
                            f"scenes[{idx}] comment_spotlight optionPicked '{picked}' not in {sorted(prev_opts)}."
                        )
    return errors


WALK_SKIP_DIRS = {"briefs", "audio", "__pycache__", "node_modules"}


def _collect_targets(raw_args: list[str]) -> list[Path]:
    inputs = [Path(a) for a in raw_args] if raw_args else [REPO_ROOT / "episodes"]
    files: list[Path] = []
    for p in inputs:
        if not p.is_dir():
            files.append(p)
            continue
        resolved_p = p.resolve()
        allow_guides = resolved_p.name.lower() == "guides" or any(
            part.lower() == "guides" for part in resolved_p.parts
        )
        skip_dirs = WALK_SKIP_DIRS if allow_guides else (WALK_SKIP_DIRS | {"guides"})
        found: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = sorted(
                d for d in dirnames if not d.startswith(".") and d.lower() not in skip_dirs
            )
            cur_dir = Path(dirpath)
            for fname in sorted(filenames):
                if fname.startswith(".") or fname.endswith(("~", ".tmp")):
                    continue
                lower = fname.lower()
                if not lower.endswith(".json") or lower == "schema.json" or lower.endswith(".brief.json"):
                    continue
                found.append(cur_dir / fname)
        files.extend(sorted(found))
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Cyber Jasoos / BreachZero episode manifests.")
    parser.add_argument("--all", action="store_true", help="Validate all live episode manifests under episodes/.")
    parser.add_argument("--publish-ready", action="store_true", help="Reject preview/draft voice licenses (EDGE_READ_ALOUD_PREVIEW, MACOS_DRAFT).")
    parser.add_argument("targets", nargs="*", help="Episode JSON file(s) or directory.")
    args = parser.parse_args(argv)
    targets = _collect_targets([] if args.all and not args.targets else args.targets)
    if not targets:
        print("No episode manifests found.", file=sys.stderr)
        return 1
    failed, loaded = 0, []
    for path in targets:
        if not path.is_file():
            print(f"[FAIL] {path}: file not found", file=sys.stderr)
            failed += 1
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            errs = validate_manifest(data, publish_ready=args.publish_ready)
            loaded.append(data)
        except Exception as exc:
            print(f"[FAIL] {path}: invalid JSON ({exc})", file=sys.stderr)
            failed += 1
            continue
        if errs:
            failed += 1
            print(f"[FAIL] {path} ({len(errs)} violation(s)):\n" + "\n".join(f"  - {e}" for e in errs))
        else:
            print(f"[PASS] {path}")
    if len(loaded) > 1 and (cont_errs := validate_season_continuity(loaded)):
        failed += 1
        print(f"[FAIL] Season continuity ({len(cont_errs)} violation(s)):\n" + "\n".join(f"  - {e}" for e in cont_errs))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
