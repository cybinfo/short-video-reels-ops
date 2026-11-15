#!/usr/bin/env python3
"""Scene, TTS-clause, post-copy, and poll-branch builders for Cyber Jasoos story briefs."""

import re

STOP_WORDS = {"aur", "par", "mein", "hai", "tha", "thi", "the", "ke", "ki", "ka", "se", "ko", "ne", "toh", "bhi", "ek", "hi", "ya"}


def _word_trim(text: str, limit: int) -> str:
    s = " ".join(str(text).split())
    out = s if len(s) <= limit else (s[:limit].rsplit(" ", 1)[0] if " " in s[:limit] else s[:limit])
    return out.rstrip(" ·—|,-:;")


def ensure_loop_suspension(text: str) -> str:
    clean = " ".join(str(text).split()).strip()
    if clean.endswith("..."):
        return clean
    clean = re.sub(r"[.।۔!?]+$", "", clean).rstrip()
    return f"{clean}..."


def build_clauses(narration: str, speaker: str = "narrator", suspend_end: bool = False) -> list[dict]:
    parts = [p.strip() for p in re.split(r"(?<=[!?:])\s+|(?<!\.)(?<=\.)(?!\.)\s+", narration) if p.strip()]
    if not parts or " ".join(parts) != narration:
        parts = [narration]
    clauses: list[dict] = []
    for idx, part in enumerate(parts):
        is_last_susp = suspend_end and idx == len(parts) - 1
        clauses.append({
            "speaker": speaker,
            "rate": "+9%" if is_last_susp else "+10%",
            "pitch": "-4Hz" if is_last_susp else "-3Hz",
            "pauseAfter": 0.16,
            "roman": part,
            "hi": ensure_loop_suspension(part) if is_last_susp else part,
        })
    return clauses


def extract_keywords(narration: str, limit: int = 5) -> list[str]:
    picks: list[str] = []
    for raw in narration.split():
        clean = re.sub(r"^[^A-Za-z0-9₹*#]+|[^A-Za-z0-9!?.]+$", "", raw)
        key = re.sub(r"[^A-Za-z0-9]", "", clean).lower()
        if len(key) >= 4 and key not in STOP_WORDS and clean not in picks:
            picks.append(clean)
        if len(picks) >= limit:
            break
    return picks or [w for w in narration.split()[:3] if w]


def _trim_poll_str(text: str, cap: int) -> str:
    return _word_trim(text, cap + (3 if "{pct}" in text else 0))


def build_post_copy(title: str, concept: str, real_inc: dict, hook_line: str, suspects: list[dict], part: int, brief_overrides: dict | None = None) -> dict:
    ovr = brief_overrides if isinstance(brief_overrides, dict) else {}
    pc_ovr = ovr.get("postCopy") if isinstance(ovr.get("postCopy"), dict) else {}
    is_guide = str(ovr.get("preset") or "").strip().lower() == "guide_walkthrough"
    s_lines = [f"{s['key']} = {s['name']} ({s['role']} · {s['clue']})" for s in suspects]
    s_inline = ", ".join(f"{s['key']}) {s['name']}" for s in suspects)
    default_cta = "Kaunsa stage sabse powerful hai? Neeche A, B, ya C comment kijiye!" if is_guide else ("Asli jaal kaunsa hai? Neeche A, B, ya C comment kijiye!" if part == 1 else "Agla Case A, B, ya C comment kijiye!")
    cta = str(pc_ovr.get("ctaLine") or ovr.get("ctaLine") or default_cta)
    default_ig = f"{hook_line} Cyber Jasoos (@cyberjasoos) Zero-AI pipeline ke 3 pillars: {s_inline}. {real_inc['lesson']} {cta}" if is_guide else f"{hook_line} Cyber Jasoos (@cyberjasoos) ki jaanch mein 3 suraag saamne aaye: {s_inline}. {real_inc['lesson']} {cta}"
    default_li = (
        f"{title} — Cyber Jasoos ({concept}):\n\n{real_inc['incident']} ({real_inc['year']}): {real_inc['impact']}\n\nArchitecture Takeaway: {real_inc['lesson']}\n\nStages: {s_inline}."
        if is_guide else f"{title} — Cyber Jasoos ({concept}):\n\n{real_inc['incident']} ({real_inc['year']}): {real_inc['impact']}\n\nSuraksha Kavach: {real_inc['lesson']}\n\nSuspects: {s_inline}."
    )
    default_pin = ("CYBER JASOOS PIPELINE POLL — APNA STAGE CHUNIYE:\n" if is_guide else "CYBER JASOOS LIVE POLL — SABOOT MILAIYE:\n") + "\n".join(s_lines) + f"\n{cta}"
    raw_tags = pc_ovr.get("hashtags") or ovr.get("hashtags")
    default_tags = ["#CyberJasoos", "#Remotion", "#VideoAutomation", "#SelfHealingCode", "#ReelsEngine", "#BuildInPublic"] if is_guide else ["#CyberJasoos", "#AsliGaddarKaun", "#CyberSafetyIndia", "#UPIFraudAlert", "#1930Helpline", "#HindiCrimeStory"]
    tags = [str(t) for t in raw_tags] if isinstance(raw_tags, list) and raw_tags else default_tags
    yt_raw = str(pc_ovr.get("youtubeShortsTitle") or ovr.get("youtubeShortsTitle") or f"{title[:88].rstrip()} #Shorts")
    return {
        "instagramCaption": str(pc_ovr.get("instagramCaption") or ovr.get("instagramCaption") or default_ig),
        "youtubeShortsTitle": yt_raw[:100],
        "linkedinPost": str(pc_ovr.get("linkedinPost") or ovr.get("linkedinPost") or default_li),
        "pinnedCommentVote": str(pc_ovr.get("pinnedCommentVote") or ovr.get("pinnedCommentVote") or default_pin),
        "hashtags": tags,
    }


def expand_poll_branches(
    raw_branches: dict, title: str, concept: str, real_inc: dict,
    suspects: list[dict], brief_overrides: dict | None = None,
) -> dict:
    ovr = brief_overrides if isinstance(brief_overrides, dict) else {}
    is_guide = str(ovr.get("preset") or "").strip().lower() == "guide_walkthrough"
    expanded: dict[str, dict] = {}
    for key in ("A", "B", "C"):
        src = raw_branches.get(key) or {}
        opening = " ".join(str(src.get("openingLine") or src.get("narration") or "").split())
        ep_title = str(src.get("episodeTitle") or f"{{pct}}% Vote Reveal — {title}")
        raw_ss = src.get("scrollStopper") if isinstance(src.get("scrollStopper"), dict) else {}
        ss_badge = _trim_poll_str(str(raw_ss.get("badge") or src.get("stopperBadge") or f"POLL · {{pct}}% VOTED {key}"), 26)
        ss_text = _trim_poll_str(str(raw_ss.get("text") or src.get("stopperText") or ("Next Chapter Unlocked!" if is_guide else "Asli Forensic Sach Khula!")), 42)
        sc01 = dict(src["scene01Props"]) if isinstance(src.get("scene01Props"), dict) else {
            "phoneStatus": str(src.get("phoneStatus") or ("{pct}% Builders Chose This Stage!" if is_guide else "{pct}% Logon Ka Faisla Saamne Aaya!")),
            "scrollStopper": {"badge": ss_badge, "text": ss_text, "tone": str(raw_ss.get("tone") or "emerald")},
            "shotTitles": src.get("shotTitles") or (
                [f"{{pct}}% VOTED {key}", "PIPELINE DEEP DIVE", "ZERO-AI LOCK!"]
                if is_guide
                else [f"{{pct}}% VOTED {key}", "FORENSIC CLUE MATCH", "ASLI SACH BE-NAQAAB!"]
            ),
        }
        if isinstance(sc01.get("scrollStopper"), dict):
            sc01["scrollStopper"] = {
                **sc01["scrollStopper"],
                "badge": _trim_poll_str(str(sc01["scrollStopper"].get("badge") or ss_badge), 26),
                "text": _trim_poll_str(str(sc01["scrollStopper"].get("text") or ss_text), 42),
            }
        expanded[key] = {
            "episodeTitle": ep_title,
            "coldOpenTag": str(src.get("coldOpenTag") or ("{pct}% VOTE · NEXT STAGE" if is_guide else "{pct}% VOTE · PARDAFAASH")),
            "outcomeVerdict": str(src.get("outcomeVerdict") or (
                f"{{pct}}% picked Option {key} as the top automation gate."
                if is_guide
                else f"{{pct}}% selected Option {key} before forensic trace revealed the full chain."
            )),
            "openingLine": opening,
            "seg01": src.get("seg01") or {
                "narration": opening,
                "ttsClauses": build_clauses(opening, "narrator", suspend_end=False),
                "highlightKeywords": src.get("highlightKeywords") or ["{pct_word} percent", *extract_keywords(opening, 4)],
            },
            "scene01Props": sc01,
            "postCopy": src.get("postCopy") or build_post_copy(ep_title, concept, real_inc, opening, suspects, 2, ovr),
        }
    return expanded


def build_noir_scenes(
    ep_id: str, season: int, part: int, title: str, concept: str, case_tag: str,
    real_inc: dict, brief: dict, seg_specs: list[dict], suspects: list[dict], stopper: dict,
) -> list[dict]:
    is_guide = str(brief.get("preset") or "").strip().lower() == "guide_walkthrough"
    ep_num = int(brief.get("episodeNumber") or brief.get("episode") or 1)
    plates = brief.get("plates") or {}
    board_suspects = [{k: v for k, v in s.items() if k not in {"icon", "suspicious"}} for s in suspects]
    b = [(seg_specs[i]["startSec"], seg_specs[i]["endSec"]) for i in range(5)]
    sc5_dur = max(6.0, float(b[4][1]) - float(b[4][0]))
    return [
        {
            "id": f"{ep_id}-sc-01", "startSec": b[0][0], "endSec": b[0][1], "kind": "detective_crime_hook",
            "sfxCues": [{"file": "sfx/bank-sms-chime.wav", "offsetFrames": 4, "volume": 0.42}, {"file": "sfx/cash-drain-ticks.wav", "offsetRatio": 0.35, "volume": 0.34}],
            "props": {
                "caseBadge": str(brief.get("caseBadge") or (f"GUIDE #{ep_num:02d}" if is_guide else f"CASE #{season:02d} · PART {part}")),
                "timeLabel": str(brief.get("timeLabel") or ("ZERO-AI PIPELINE" if is_guide else "RAAT 10:15 PM")),
                "locationLabel": str(brief.get("locationLabel") or case_tag.split("·")[0].strip()),
                "phoneStatus": str(brief.get("phoneStatus") or title),
                "bankAlertTitle": str(brief.get("bankAlertTitle") or case_tag),
                "amountLost": str(brief.get("amountLost") or ("90% ZERO-AI" if is_guide else "Rs 8,40,000")),
                "mode": str(brief.get("hookMode") or ("loss_drain" if part == 1 else "suspect_unmask")),
                "cutRatios": [0.24, 0.64], "scrollStopper": stopper,
                "shotTitles": list(brief.get("shotTitles") or ([case_tag, "AUTO SELF-HEAL!", "1-CMD MP4 READY!"] if is_guide else [case_tag, "KHAATA KHALI!", "LIVE CYBER JAAL!"])),
                "shotTags": list(brief.get("shotTags") or (["REEL FACTORY", "AUTO-HEAL LOOP", "SAFE-ZONE LOCK"] if is_guide else ["CRIME SCENE", "DRAINING LIVE!", "ZERO OTP CALL!"])),
                "heroImage": str(plates.get("hookHero") or "characters/case02-shaadi-qr.png"),
                "secondaryImage": str(plates.get("hookSecondary") or "characters/sharma-shock.png"),
                "tertiaryImage": str(plates.get("hookTertiary") or "characters/kabir-closeup.png"),
                "shockPills": list(brief.get("shockPills") or (["35-LINE YAML", "0 DOM DEFECTS", "AUTO-LEARN"] if is_guide else ["0 CALL", "INSTANT DRAIN", "3 SURAAG!"])),
            },
        },
        {
            "id": f"{ep_id}-sc-02", "startSec": b[1][0], "endSec": b[1][1], "kind": "detective_wifi_clue",
            "sfxCues": [{"file": "sfx/puja-phone-vibrate.wav", "offsetRatio": 0.42, "volume": 0.44}, {"file": "sfx/soc-alert-ping.wav", "offsetRatio": 0.5, "volume": 0.36}],
            "props": {
                "headline": str(brief.get("clueHeadline") or ("3 AUTOMATION GATES · ZERO MANUAL WORK!" if is_guide else "3 MEHMAAN · 3 ALAG DIGITAL SURAAG!")),
                "subline": str(brief.get("clueSubline") or _word_trim(concept, 42)),
                "heroImage": str(plates.get("clueHero") or "characters/case02-hotel-wifi.png"),
                "secondaryImage": str(plates.get("clueSecondary") or "characters/case02-smart-printer.png"),
                "interceptBanner": {
                    "badge": str(brief.get("interceptBadge") or (f"PIPELINE SCAN · GUIDE #{ep_num:02d}" if is_guide else f"FORENSIC SCAN · CASE #{season:02d}")),
                    "text": str(brief.get("interceptText") or _word_trim(stopper["text"], 40)),
                    "tone": str(brief.get("interceptTone") or ("amber" if (is_guide or part != 1) else "danger")),
                },
                "devices": [
                    {
                        "name": s["name"],
                        "status": _word_trim(f"{s['timestampBadge']} · {s['clue']}", 34),
                        "icon": str(s.get("icon") or ("alert" if i == 2 else "wifi")),
                        "suspicious": bool(s["suspicious"]) if s.get("suspicious") is not None else (i == 2),
                    }
                    for i, s in enumerate(suspects[:3])
                ],
            },
        },
        {
            "id": f"{ep_id}-sc-03", "startSec": b[2][0], "endSec": b[2][1], "kind": "detective_evidence_twist",
            "sfxCues": [{"file": "sfx/keypad-tap-seq.wav", "offsetRatio": 0.16, "volume": 0.4}, {"file": "sfx/ussd-dial-tones.wav", "offsetRatio": 0.52, "volume": 0.58}],
            "props": {
                "variant": "cctv_backdoor", "tone": "amber" if part == 1 else "emerald",
                "badge": str(brief.get("frameworkBadge") or ("PIPELINE ENGINE · ZERO-AI" if is_guide else f"KABIR FORENSIC PIVOT · CASE #{season:02d}")),
                "headline": str(brief.get("frameworkHeadline") or ("35-Line Brief Se 1080p Reel Ready!" if is_guide else "Kabir Ki Jaanch Mein Chhupa Jaal Pakda Gaya!")),
                "heroImage": str(plates.get("twistHero") or "characters/handoff-shadow.png"),
                "secondaryImage": str(plates.get("twistSecondary") or "characters/kabir-investigating.png"),
                "stepOneTitle": str(brief.get("stepOneTitle") or ("35-Line YAML Brief" if is_guide else "1 Scan / Free Connect")),
                "stepOneTag": str(brief.get("stepOneTag") or ("SCHEMA + CLOCK GATE" if is_guide else "SESSION OR UPI TRAP")),
                "stepTwoTitle": str(brief.get("stepTwoTitle") or ("Auto Rate & DOM Heal" if is_guide else "Silent Account Drain!")),
                "stepTwoTag": str(brief.get("stepTwoTag") or ("ZERO MANUAL REWORK" if is_guide else "TRACE WIPE ATTEMPT")),
                "exposedItems": list(brief.get("exposedItems") or [s["timestampBadge"] for s in suspects[:3]]),
            },
        },
        {
            "id": f"{ep_id}-sc-04", "startSec": b[3][0], "endSec": b[3][1], "kind": "detective_evidence_twist",
            "sfxCues": [{"file": "sfx/heartbeat-radar-ping.wav", "offsetFrames": 3, "volume": 0.46}, {"file": "sfx/stamp-slam.wav", "offsetRatio": 0.45, "volume": 0.36}],
            "props": {
                "variant": "contact_match", "tone": "crimson" if part == 1 else "emerald", "lockedParallax": True,
                "badge": str(brief.get("payoffBadge") or ("AUTO-HEAL VERIFIED · SAFE ZONE" if is_guide else "SURAKSHA KAVACH · 1930 GOLDEN HOUR")),
                "headline": str(brief.get("payoffHeadline") or ("1 Command Se MP4 + Launch Pack Ready!" if is_guide else "UPI PIN Sirf Bhejne Par Lagta Hai · 1930 Milaiye!")),
                "heroImage": str(plates.get("payoffHero") or "characters/kabir-closeup.png"),
                "secondaryImage": str(plates.get("payoffSecondary") or "characters/kabir-investigating.png"),
                "radarPinLabel": str(brief.get("radarPinLabel") or ("HEADLESS CHROME · 0 DEFECTS" if is_guide else "LIVE FORENSIC LOCK · 1930 SHIELD")),
                "crossedOutLabel": str(brief.get("crossedOutLabel") or ("MANUAL HARDCODING BAND" if is_guide else "ANJAAN CALL SCAM NAHI")),
                "matchHeadline": str(brief.get("matchHeadline") or ("HAR GATE 100% AUTO-VERIFIED!" if is_guide else "LOBBY KE ANDAR HI ASLI JAAL HAI!")),
                "matchSubline": _word_trim(str(brief.get("matchSubline") or real_inc["lesson"]), 42),
                "verdictPillLeft": str(brief.get("verdictPillLeft") or ("1-CMD BUILDER" if is_guide else "▲ VERIFY PAYEE & WIFI")),
                "verdictPillRight": str(brief.get("verdictPillRight") or ("ZERO-AI SELF-HEAL" if is_guide else "CALL 1930 GOLDEN HOUR")),
            },
        },
        {
            "id": f"{ep_id}-sc-05", "startSec": b[4][0], "endSec": b[4][1], "kind": "detective_suspect_board",
            "sfxCues": [{"file": "sfx/cliffhanger-tick.wav", "offsetFrames": 4, "volume": 0.34}],
            "props": {
                "boardMode": str(brief.get("boardMode") or ("next_case_vote" if (is_guide or part != 1) else "suspect_vote")),
                "prompt": str(brief.get("votePrompt") or ("KAUNSA STAGE SABSE POWERFUL HAI?" if is_guide else ("ASLI JAAL KAUNSA HAI?" if part == 1 else "AGLA CASE KAUNSA KHOLEIN?"))),
                "partBadge": str(brief.get("partBadge") or ("NEXT CHAPTER" if is_guide else ("PART 2 JALD" if part == 1 else "NAYA CASE JALD"))),
                "spotlightRightBadge": str(brief.get("spotlightRightBadge") or (f"GUIDE #{ep_num:02d}" if is_guide else f"CASE #{season:02d} LIVE")),
                "followHandleLine": str(brief.get("followHandleLine") or ("FULL GUIDE: FOLLOW @CYBERJASOOS" if is_guide else ("PART 2 REVEAL KE LIYE FOLLOW @CYBERJASOOS" if part == 1 else "AGLA CASE DEKHNE KE LIYE FOLLOW @CYBERJASOOS"))),
                "forensicClueBar": str(brief.get("forensicClueBar") or (_word_trim(f"{str(brief.get('companyName') or 'CYBER JASOOS')} · {case_tag}", 38) if is_guide else f"CYBER JASOOS · {case_tag}")),
                "suspects": board_suspects,
                "optionTimingsSec": [round(sc5_dur * 0.16, 2), round(sc5_dur * 0.34, 2), round(sc5_dur * 0.52, 2)],
                "ctaLine": str(brief.get("ctaLine") or ("Agla chapter dekhiye @cyberjasoos!" if is_guide else ("Asli jaal kaunsa? A, B, C comment!" if part == 1 else "Agla Case? A, B, C comment!"))),
                "loopBridgeText": str(brief.get("loopBridgeText") or seg_specs[-1]["ttsClauses"][-1]["roman"].split(",")[-1].strip()),
            },
        },
    ]
