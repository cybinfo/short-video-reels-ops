#!/usr/bin/env python3
"""Pure, deterministic self-healing rules and launch copy-pack generator for Cyber Jasoos."""

from __future__ import annotations

import copy, json, re, sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from instagram_ops import draft_socratic_reply  # noqa: E402

OVERLAY_CAPS: dict[str, int] = {
    "badge": 26, "caseBadge": 26, "radarPinLabel": 26, "crossedOutLabel": 26,
    "verdictPillLeft": 24, "verdictPillRight": 24,
    "headline": 38, "matchHeadline": 38, "forensicClueBar": 38, "bankAlertTitle": 38, "prompt": 38,
    "subline": 42, "matchSubline": 42, "followHandleLine": 32,
}


def _bump_pct_str(rate_str: object, delta_pct: int) -> str:
    m = re.match(r"^\s*([+-]?\d+)\s*%?\s*$", str(rate_str or ""))
    return f"{max(-20, min(30, (int(m.group(1)) if m else 0) + delta_pct)):+d}%"


def _word_compact(text: str, max_chars: int) -> str:
    s = " ".join(str(text).split())
    if len(s) <= max_chars:
        return s
    kept: list[str] = []
    for w in s.split(" "):
        cand = f"{' '.join(kept)} {w}".strip() if kept else w
        if len(cand) <= max_chars:
            kept.append(w)
        else:
            break
    return (" ".join(kept).rstrip(" ·—|,-:")) if kept else s[:max_chars].rstrip()


def compute_rate_heal_adjustment(
    manifest: dict, actual_duration: float, actual_wpm: float,
    target_sec: float = 51.5, min_sec: float = 42.5, max_sec: float = 57.5,
    min_wpm: float = 132.0, max_wpm: float = 192.0,
) -> tuple[dict, str | None]:
    if min_sec <= actual_duration <= max_sec and min_wpm <= actual_wpm <= max_wpm:
        return manifest, None
    if not (min_sec <= actual_duration <= max_sec) and actual_duration > 0 and target_sec > 0:
        ratio, trigger = float(actual_duration) / float(target_sec), f"duration {actual_duration:.2f}s outside [{min_sec}, {max_sec}]s"
    else:
        ratio = (0.5 * (min_wpm + max_wpm)) / max(1.0, float(actual_wpm))
        trigger = f"WPM {actual_wpm:.1f} outside [{min_wpm}, {max_wpm}]"

    delta_pct = int(round((ratio - 1.0) * 100)) or (1 if ratio >= 1.0 else -1)
    out = copy.deepcopy(manifest)
    vc = out.setdefault("voiceConfig", {})
    raw_rates = vc.get("edgeRates") if isinstance(vc.get("edgeRates"), dict) and vc.get("edgeRates") else {"narrator": "+8%"}
    vc["edgeRates"] = {str(k): _bump_pct_str(v, delta_pct) for k, v in raw_rates.items()}
    for seg in out.get("scriptSegments") or []:
        for cl in (seg.get("ttsClauses") or []) if isinstance(seg, dict) else []:
            if isinstance(cl, dict) and isinstance(cl.get("rate"), str):
                cl["rate"] = _bump_pct_str(cl["rate"], delta_pct)

    vc["kokoroSpeed"] = round(max(0.85, min(1.30, float(vc.get("kokoroSpeed") or 1.08) * ratio)), 3)
    if isinstance(vc.get("kokoroSpeeds"), dict):
        vc["kokoroSpeeds"] = {k: round(max(0.85, min(1.30, float(v) * ratio)), 3) for k, v in vc["kokoroSpeeds"].items()}
    vc["targetWpm"] = int(max(140, min(185, round(float(vc.get("targetWpm") or 165) * ratio))))
    return out, f"{trigger} -> ratio={ratio:.3f}, edgeDelta={delta_pct:+d}%, kokoroSpeed={vc['kokoroSpeed']}, targetWpm={vc['targetWpm']}"


def _suspend_tail(text: str, force: bool = False) -> str:
    s = str(text)
    if s.rstrip().endswith("..."):
        return s
    if re.search(r"[.।۔!?؟…]\s*$", s) or force:
        stem = re.sub(r"[\s.।۔!?؟…]+$", "", s)
        return f"{stem}..." if stem else "..."
    return s


def heal_manifest_text_guards(manifest: dict, validation_errors: list[str] | None = None) -> tuple[dict, list[str]]:
    errs = validation_errors or []
    out, actions = copy.deepcopy(manifest), []
    segs = out.get("scriptSegments") if isinstance(out.get("scriptSegments"), list) else []
    force_loop = any("Loop Suspension" in e for e in errs)
    if segs and isinstance(segs[-1], dict):
        last_seg = segs[-1]
        if isinstance(narr := last_seg.get("narration"), str) and (hn := _suspend_tail(narr, force_loop)) != narr:
            last_seg["narration"] = hn
            actions.append("loop_suspension: appended '...' to scriptSegments[-1].narration")
        clauses = last_seg.get("ttsClauses") if isinstance(last_seg.get("ttsClauses"), list) else []
        if clauses and isinstance(clauses[-1], dict):
            last_cl = clauses[-1]
            for fld in ("hi", "tts", "roman"):
                if isinstance(val := last_cl.get(fld), str) and val.strip():
                    hv = _suspend_tail(val, force=(force_loop and fld in ("hi", "roman")))
                    if hv != val:
                        last_cl[fld] = hv
                        actions.append(f"loop_suspension: appended '...' to final ttsClauses[-1].{fld}")

    has_open_err = any("openingLine" in e for e in errs)
    first_narr = str(segs[0].get("narration") or "").strip() if (segs and isinstance(segs[0], dict)) else ""
    hook = out.setdefault("hook", {})
    if isinstance(hook, dict) and first_narr:
        cur_open = str(hook.get("openingLine") or "").strip()
        if cur_open != first_narr and (has_open_err or out.get("visualTheme") == "noir_cinema" or len(cur_open) < 15):
            hook["openingLine"] = first_narr
            actions.append("opening_line_parity: synced hook.openingLine to scriptSegments[0].narration")
    if isinstance(pb := out.get("pollBranches"), dict) and (has_open_err or out.get("visualTheme") == "noir_cinema"):
        for bk, bobj in pb.items():
            if isinstance(bobj, dict) and isinstance(bseg := bobj.get("seg01"), dict) and (bn := str(bseg.get("narration") or "").strip()):
                if str(bobj.get("openingLine") or "").strip() != bn:
                    bobj["openingLine"] = bn
                    actions.append(f"opening_line_parity: synced pollBranches.{bk}.openingLine")

    ep_id = str(out.get("id") or "").strip()
    vc = out.setdefault("voiceConfig", {})
    if isinstance(vc, dict) and ep_id:
        for key, suffix in (("audioFile", ".wav"), ("captionsFile", ".captions.json")):
            if not isinstance(vc.get(key), str) or not vc[key].strip():
                vc[key] = f"audio/{ep_id}{suffix}"
                actions.append(f"voice_paths: set voiceConfig.{key}='{vc[key]}'")
    return (out if actions else manifest), actions


def _compact_str(val: str, cap: int, scale: float = 1.0) -> str:
    s = " ".join(str(val).split())
    eff_cap = max(10, int(round(cap * scale)))
    if len(s) <= eff_cap:
        return s
    s = re.sub(r"(?i)PART\s*2\s+REVEAL\s+KE\s+LIYE\s+FOLLOW", "PART 2: FOLLOW", s)
    s = re.sub(r"(?i)AGLA\s+CASE\s+\S+\s+KE\s+LIYE\s+FOLLOW", "NEXT CASE: FOLLOW", s)
    if len(s) <= eff_cap:
        return s
    for sep in (" · ", " — ", " | "):
        if sep in s:
            parts = [p.strip() for p in s.split(sep) if p.strip()]
            if parts:
                s = parts[0] if len(parts[0]) >= 5 else parts[-1]
                break
    return _word_compact(s, eff_cap)


LAYOUT_DEFECT_CODES: frozenset[str] = frozenset({
    "STAGE_CAPTION_OVERLAP",
    "HORIZONTAL_OFF_CENTER",
    "ASYMMETRIC_NOIR_RAIL",
    "GRAPH_PILL_NODE_OVERLAP",
})

_OVERRUN_FILLER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:sach\s+toh\s+yeh\s+hai\s+ki|dekha\s+jaaye\s+toh|poori\s+tarah\s+se|asal\s+mein)\b\s*,?\s*", re.I),
    re.compile(r"\b(?:bilkul|darasal|ekdum|yaani\s+ki|basically|actually|literally)\b\s*,?\s*", re.I),
)


def condense_narration_for_overrun(text: str, max_words: int | None = None) -> str:
    """Deterministically condense narration text when TTS rate hits +30% ceiling and duration still overruns."""
    raw = " ".join(str(text or "").split())
    if not raw:
        return ""
    tail_m = re.search(r"(\.{3}|[.!?।۔؟…]+)$", raw)
    tail_punct = tail_m.group(1) if tail_m else ""
    cleaned = raw
    for pat in _OVERRUN_FILLER_PATTERNS:
        cleaned = pat.sub("", cleaned)
    cleaned = re.sub(r"\s+([,.;!?])", r"\1", " ".join(cleaned.split()))
    words = cleaned.split()
    orig_words = raw.split()
    limit = max_words if (isinstance(max_words, int) and max_words > 0) else max(4, int(round(len(orig_words) * 0.82)))
    if len(words) > limit:
        words = words[:limit]
    result = " ".join(words).rstrip(" ,;:-—·|")
    if tail_punct and not result.endswith(tail_punct):
        result = re.sub(r"[.!?।۔؟…]+$", "", result).rstrip(" ,;:-—·|") + tail_punct
    return result


def heal_scene_for_defects(
    scene: dict,
    defect_codes: list[str] | set[str] | tuple[str, ...] | None = None,
    scale: float = 0.85,
) -> dict:
    """Deterministic layout-code healer for STAGE_CAPTION_OVERLAP, HORIZONTAL_OFF_CENTER, ASYMMETRIC_NOIR_RAIL, and GRAPH_PILL_NODE_OVERLAP."""
    if not isinstance(scene, dict):
        return scene
    codes = {str(c).strip().upper() for c in (defect_codes or LAYOUT_DEFECT_CODES) if c}
    props = scene.setdefault("props", {})
    if not isinstance(props, dict):
        props = {}
        scene["props"] = props

    for key, cap in (*OVERLAY_CAPS.items(), ("stepOneTitle", 26), ("stepTwoTitle", 26), ("stepOneTag", 24), ("stepTwoTag", 24), ("title", 32), ("subtitle", 38)):
        if isinstance(orig := props.get(key), str):
            props[key] = _compact_str(orig, cap, scale)

    for list_k, lcap in (("shotTitles", 28), ("shotTags", 22), ("shockPills", 18), ("exposedItems", 22), ("pills", 18)):
        if isinstance(arr := props.get(list_k), list):
            for idx, elem in enumerate(arr):
                if isinstance(elem, str):
                    arr[idx] = _compact_str(elem, lcap, scale)
                elif isinstance(elem, dict):
                    for fk in ("label", "text", "title", "name", "tag"):
                        if isinstance(fv := elem.get(fk), str):
                            elem[fk] = _compact_str(fv, lcap, scale)

    for b_key in ("scrollStopper", "interceptBanner"):
        if isinstance(bn := props.get(b_key), dict):
            for sub_k, sub_cap in (("badge", 26), ("text", 42)):
                if isinstance(orig := bn.get(sub_k), str):
                    bn[sub_k] = _compact_str(orig, sub_cap, scale)

    for item_list, fld_caps in (
        ("suspects", (("clue", 20), ("role", 20), ("name", 22))),
        ("options", (("label", 22), ("detail", 24))),
        ("devices", (("name", 24), ("status", 32))),
        ("nodes", (("label", 18), ("title", 18), ("name", 18), ("tag", 14), ("sublabel", 20), ("detail", 20))),
        ("edges", (("label", 16), ("pill", 16), ("text", 16), ("tag", 14))),
        ("tiers", (("name", 20), ("tag", 14), ("examples", 24), ("blastRadius", 20))),
    ):
        for item in props.get(item_list) or []:
            if isinstance(item, dict):
                for fk, fcap in fld_caps:
                    if isinstance(orig := item.get(fk), str):
                        item[fk] = _compact_str(orig, fcap, scale)

    if "STAGE_CAPTION_OVERLAP" in codes:
        props["compactStage"] = True
        for k_sub, cap_sub in (("subline", 34), ("matchSubline", 34), ("forensicClueBar", 32), ("prompt", 32), ("crisisPrompt", 32)):
            if isinstance(orig := props.get(k_sub), str):
                props[k_sub] = _compact_str(orig, cap_sub, min(scale, 0.8))

    if "HORIZONTAL_OFF_CENTER" in codes or "ASYMMETRIC_NOIR_RAIL" in codes:
        props["centerLockPx"] = 540
        props["noirRailInsetPx"] = 84

    if "GRAPH_PILL_NODE_OVERLAP" in codes:
        props["compactGraphPills"] = True

    if codes & LAYOUT_DEFECT_CODES or defect_codes is not None:
        scene["layoutHealed"] = True
        props["layoutHealed"] = True

    return scene


def heal_dom_defects(manifest: dict, dom_report: dict) -> tuple[dict, list[str]]:
    ep_id = manifest.get("id")
    defects = [d for d in ((dom_report or {}).get("defects") or []) if isinstance(d, dict) and d.get("episode") in (None, "", ep_id)]
    if not defects or not isinstance(manifest.get("scenes"), list):
        return manifest, []
    sc_ids = {str(d["sceneId"]) for d in defects if d.get("sceneId") is not None}
    sc_idxs = {int(d["sceneIndex"]) for d in defects if isinstance(d.get("sceneIndex"), int)}
    codes_by_idx: dict[int, set[str]] = {}
    global_codes: set[str] = set()
    for d in defects:
        c_str = str(d.get("code") or d.get("type") or "").strip().upper()
        if not c_str:
            continue
        if isinstance(d.get("sceneIndex"), int):
            codes_by_idx.setdefault(int(d["sceneIndex"]), set()).add(c_str)
        else:
            global_codes.add(c_str)

    for scale in (1.0, 0.8):
        out, actions = copy.deepcopy(manifest), []
        for top_k, top_cap in (("securityDomain", 32), ("coldOpenTag", 32)):
            if isinstance(orig := out.get(top_k), str) and (nv := _compact_str(orig, top_cap, scale)) != orig:
                out[top_k] = nv
                actions.append(f"{top_k}: {orig!r} -> {nv!r}")
        scenes = out["scenes"]
        targets = [i for i, sc in enumerate(scenes) if isinstance(sc, dict) and (sc.get("id") in sc_ids or i in sc_idxs)]
        for idx in (targets or list(range(len(scenes)))):
            props = scenes[idx].get("props") if isinstance(scenes[idx], dict) else None
            if not isinstance(props, dict):
                continue
            for key, cap in (*OVERLAY_CAPS.items(), ("stepOneTitle", 26), ("stepTwoTitle", 26), ("stepOneTag", 24), ("stepTwoTag", 24)):
                if isinstance(orig := props.get(key), str) and (nv := _compact_str(orig, cap, scale)) != orig:
                    props[key] = nv
                    actions.append(f"scenes[{idx}].{key}: {orig!r} -> {nv!r}")
            for list_k, lcap in (("shotTitles", 28), ("shotTags", 22), ("shockPills", 18), ("exposedItems", 22)):
                if isinstance(arr := props.get(list_k), list):
                    for l_i, elem in enumerate(arr):
                        if isinstance(elem, str) and (nv := _compact_str(elem, lcap, scale)) != elem:
                            arr[l_i] = nv
                            actions.append(f"scenes[{idx}].{list_k}[{l_i}]: {elem!r} -> {nv!r}")
            for b_key in ("scrollStopper", "interceptBanner"):
                if isinstance(bn := props.get(b_key), dict):
                    for sub_k, sub_cap in (("badge", 26), ("text", 42)):
                        if isinstance(orig := bn.get(sub_k), str) and (nv := _compact_str(orig, sub_cap, scale)) != orig:
                            bn[sub_k] = nv
                            actions.append(f"scenes[{idx}].{b_key}.{sub_k}: {orig!r} -> {nv!r}")
            for item_list, fld_caps in (("suspects", (("clue", 20), ("role", 20))), ("options", (("label", 22), ("detail", 24))), ("devices", (("name", 24), ("status", 32)))):
                for s_i, item in enumerate(props.get(item_list) or []):
                    if isinstance(item, dict):
                        for fk, fcap in fld_caps:
                            if isinstance(orig := item.get(fk), str) and (nv := _compact_str(orig, fcap, scale)) != orig:
                                item[fk] = nv
                                actions.append(f"scenes[{idx}].{item_list}[{s_i}].{fk}: {orig!r} -> {nv!r}")
            sc_codes = (codes_by_idx.get(idx, set()) | global_codes) & LAYOUT_DEFECT_CODES
            if sc_codes:
                before_sc = copy.deepcopy(scenes[idx])
                heal_scene_for_defects(scenes[idx], sc_codes, scale=min(scale, 0.85))
                if scenes[idx] != before_sc:
                    actions.append(f"scenes[{idx}].layoutHealed: {sorted(sc_codes)}")
        if actions:
            return out, actions
    return manifest, []


def generate_launch_copy_pack(manifest: dict, out_path: Path) -> Path:
    dst, ep_id = Path(out_path), str(manifest.get("id") or "episode")
    dst.parent.mkdir(parents=True, exist_ok=True)
    scenes = manifest.get("scenes") or []
    last_props = (scenes[-1].get("props") or {}) if (scenes and isinstance(scenes[-1], dict)) else {}
    choices = [
        {"key": it["key"], "name": str(it.get("name") or it.get("label") or f"Option {it['key']}").strip(),
         "summary": " · ".join(x for x in (str(it.get("role") or it.get("timestampBadge") or "").strip(), str(it.get("clue") or it.get("detail") or "").strip()) if x)}
        for it in (last_props.get("suspects") or last_props.get("options") or [])
        if isinstance(it, dict) and it.get("key") in {"A", "B", "C"}
    ]
    narr_body = " ".join(re.sub(r"\.{3,}$", "!", str(s.get("narration") or "").strip()).replace("—", "-") for s in (manifest.get("scriptSegments") or []) if isinstance(s, dict) and s.get("narration"))
    abc_inline = ", ".join(f"{c['key']}) {c['name']}" + (f" ({c['summary']})" if c["summary"] else "") for c in choices)
    tags = " ".join((manifest.get("postCopy") or {}).get("hashtags") or ["#CyberJasoos", "#CyberCrimeIndia", "#AsliGaddarKaun", "#CyberSafetyIndia"])
    cap_core = f"{narr_body} Suspects: {abc_inline}. Comment A, B, or C!".strip() if abc_inline else narr_body
    reel_caption = f"{_word_compact(cap_core, max(200, 2190 - len(tags)))}\n\n{tags}".strip()

    pin_hdr = str(last_props.get("forensicClueBar") or last_props.get("crisisPrompt") or manifest.get("coldOpenTag") or manifest.get("episodeTitle") or "CASE LIVE POLL").upper()
    pin_lines = [pin_hdr, *(f"{c['key']} = {c['name']}" + (f" ({c['summary']})" if c["summary"] else "") for c in choices), "Saboot milaiye aur A, B, ya C comment kijiye!"]
    poll_q = _word_compact(str(last_props.get("prompt") or last_props.get("crisisPrompt") or manifest.get("episodeTitle") or "Asli Gaddar Kaun?"), 76)
    poll_opts = [(c["key"], _word_compact(f"{c['key']}: {c['name']}", 22)[:22].rstrip()) for c in choices] or [(k, f"{k}: Option {k}") for k in ("A", "B", "C")]

    reply_view = copy.deepcopy(manifest)
    if scenes and isinstance(reply_view["scenes"][-1], dict) and not (reply_view["scenes"][-1].get("props") or {}).get("suspects") and choices:
        reply_view["scenes"][-1].setdefault("props", {})["suspects"] = [{"key": c["key"], "name": c["name"], "timestampBadge": c["summary"] or "us waqt"} for c in choices]
    replies = {k: draft_socratic_reply({"text": k}, k, part1_manifest=reply_view, idx=0) for k in ("A", "B", "C")}

    m_hdl = re.search(r"@[A-Za-z0-9_.]+", json.dumps(scenes))
    handle = (m_hdl.group(0).lower() if m_hdl else "@cyberjasoos")
    lines = [
        f"CYBER JASOOS ({handle}) - {str(manifest.get('seasonTitle') or ep_id).upper()} ({manifest.get('hudPartBadge') or 'REEL'}) LAUNCH PACK",
        "=" * 78, "",
        "[1] ACCOUNT PROFILE & BIO (<= 150 CHARS)",
        "Primary Handle : @cyberjasoos",
        "SEO Name       : Cyber Jasoos | Cyber Crime",
        "Bio            : Asli Cyber Fraud Cases | 60s Rahasya\n                 Saboot Dekho - A, B ya C Gaddar Pehchano!\n                 5-Sec Suraksha Kavach | Cyber Help: 1930", "",
        f"[2] REEL CAPTION + HASHTAGS ({len(reel_caption)}/2200 CHARS)",
        reel_caption, "",
        "[3] FIRST COMMENT TO POST & PIN WITHIN 60s",
        "\n".join(pin_lines), "",
        "[4] STORY 3-OPTION POLL STICKER (STRICTLY <= 22 CHARS EACH — NEVER QUIZ STICKER)",
        f"Question : {poll_q}",
        *(f"  Option {i} -> {opt} ({len(opt)} chars)" for i, (_, opt) in enumerate(poll_opts, 1)), "",
        "[5] 3 SOCRATIC VOTER REPLIES (ZERO SPOILERS)",
        *(f"Reply to Vote {k}:\n{replies[k]}\n" for k in ("A", "B", "C")),
        "[6] LAUNCH CHECKLIST",
        f"[ ] Upload {ep_id}.mp4 in Original 9:16 crop + attach {ep_id}-reel-cover.png + enable 'Made with AI' label if synthetic.",
        "[ ] Pin Block [3] comment within 60s, share Reel to Story with Block [4] 3-option POLL sticker, and reply using Block [5].",
    ]
    dst.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return dst
