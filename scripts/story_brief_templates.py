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


def build_post_copy(title: str, concept: str, real_inc: dict, hook_line: str, suspects: list[dict], part: int) -> dict:
    s_lines = [f"{s['key']} = {s['name']} ({s['role']} · {s['clue']})" for s in suspects]
    s_inline = ", ".join(f"{s['key']}) {s['name']}" for s in suspects)
    cta = "Asli jaal kaunsa hai? Neeche A, B, ya C comment kijiye!" if part == 1 else "Agla Case A, B, ya C comment kijiye!"
    return {
        "instagramCaption": f"{hook_line} Cyber Jasoos (@cyberjasoos) ki jaanch mein 3 suraag saamne aaye: {s_inline}. {real_inc['lesson']} {cta}",
        "youtubeShortsTitle": f"{title[:88].rstrip()} #Shorts"[:100],
        "linkedinPost": f"{title} — Cyber Jasoos ({concept}):\n\n{real_inc['incident']} ({real_inc['year']}): {real_inc['impact']}\n\nSuraksha Kavach: {real_inc['lesson']}\n\nSuspects: {s_inline}.",
        "pinnedCommentVote": "CYBER JASOOS LIVE POLL — SABOOT MILAIYE:\n" + "\n".join(s_lines) + f"\n{cta}",
        "hashtags": ["#CyberJasoos", "#AsliGaddarKaun", "#CyberSafetyIndia", "#UPIFraudAlert", "#1930Helpline", "#HindiCrimeStory"],
    }


def expand_poll_branches(raw_branches: dict, title: str, concept: str, real_inc: dict, suspects: list[dict]) -> dict:
    expanded: dict[str, dict] = {}
    for key in ("A", "B", "C"):
        src = raw_branches.get(key) or {}
        opening = " ".join(str(src.get("openingLine") or src.get("narration") or "").split())
        ep_title = str(src.get("episodeTitle") or f"{{pct}}% Vote Reveal — {title}")
        expanded[key] = {
            "episodeTitle": ep_title,
            "coldOpenTag": str(src.get("coldOpenTag") or "{pct}% VOTE · PARDAFAASH"),
            "outcomeVerdict": str(src.get("outcomeVerdict") or f"{{pct}}% selected Option {key} before forensic trace revealed the full chain."),
            "openingLine": opening,
            "seg01": src.get("seg01") or {
                "narration": opening,
                "ttsClauses": build_clauses(opening, "narrator", suspend_end=False),
                "highlightKeywords": src.get("highlightKeywords") or ["{pct_word} percent", *extract_keywords(opening, 4)],
            },
            "scene01Props": src.get("scene01Props") or {
                "phoneStatus": str(src.get("phoneStatus") or "{pct}% Logon Ka Faisla Saamne Aaya!"),
                "scrollStopper": src.get("scrollStopper") or {
                    "badge": f"POLL RESULT · {{pct}}% VOTED {key}",
                    "text": str(src.get("stopperText") or "Asli Forensic Sach Khula!"),
                    "tone": "emerald",
                },
                "shotTitles": src.get("shotTitles") or [f"{{pct}}% VOTED {key}", "FORENSIC CLUE MATCH", "ASLI SACH BE-NAQAAB!"],
            },
            "postCopy": src.get("postCopy") or build_post_copy(ep_title, concept, real_inc, opening, suspects, 2),
        }
    return expanded


def build_noir_scenes(
    ep_id: str, season: int, part: int, title: str, concept: str, case_tag: str,
    real_inc: dict, brief: dict, seg_specs: list[dict], suspects: list[dict], stopper: dict,
) -> list[dict]:
    plates = brief.get("plates") or {}
    b = [(seg_specs[i]["startSec"], seg_specs[i]["endSec"]) for i in range(5)]
    sc5_dur = max(6.0, float(b[4][1]) - float(b[4][0]))
    return [
        {
            "id": f"{ep_id}-sc-01", "startSec": b[0][0], "endSec": b[0][1], "kind": "detective_crime_hook",
            "sfxCues": [{"file": "sfx/bank-sms-chime.wav", "offsetFrames": 4, "volume": 0.42}, {"file": "sfx/cash-drain-ticks.wav", "offsetRatio": 0.35, "volume": 0.34}],
            "props": {
                "caseBadge": f"CASE #{season:02d} · PART {part}",
                "timeLabel": str(brief.get("timeLabel") or "RAAT 10:15 PM"),
                "locationLabel": str(brief.get("locationLabel") or case_tag.split("·")[0].strip()),
                "phoneStatus": str(brief.get("phoneStatus") or title),
                "bankAlertTitle": str(brief.get("bankAlertTitle") or case_tag),
                "amountLost": str(brief.get("amountLost") or "Rs 8,40,000"),
                "mode": "loss_drain" if part == 1 else "suspect_unmask",
                "cutRatios": [0.24, 0.64], "scrollStopper": stopper,
                "shotTitles": list(brief.get("shotTitles") or [case_tag, "KHAATA KHALI!", "LIVE CYBER JAAL!"]),
                "shotTags": list(brief.get("shotTags") or ["CRIME SCENE", "DRAINING LIVE!", "ZERO OTP CALL!"]),
                "heroImage": str(plates.get("hookHero") or "characters/case02-shaadi-qr.png"),
                "secondaryImage": str(plates.get("hookSecondary") or "characters/sharma-shock.png"),
                "tertiaryImage": str(plates.get("hookTertiary") or "characters/kabir-closeup.png"),
                "shockPills": list(brief.get("shockPills") or ["0 CALL", "INSTANT DRAIN", "3 SURAAG!"]),
            },
        },
        {
            "id": f"{ep_id}-sc-02", "startSec": b[1][0], "endSec": b[1][1], "kind": "detective_wifi_clue",
            "sfxCues": [{"file": "sfx/puja-phone-vibrate.wav", "offsetRatio": 0.42, "volume": 0.44}, {"file": "sfx/soc-alert-ping.wav", "offsetRatio": 0.5, "volume": 0.36}],
            "props": {
                "headline": str(brief.get("clueHeadline") or "3 MEHMAAN · 3 ALAG DIGITAL SURAAG!"),
                "subline": str(brief.get("clueSubline") or _word_trim(concept, 42)),
                "heroImage": str(plates.get("clueHero") or "characters/case02-hotel-wifi.png"),
                "secondaryImage": str(plates.get("clueSecondary") or "characters/case02-smart-printer.png"),
                "interceptBanner": {"badge": f"FORENSIC SCAN · CASE #{season:02d}", "text": _word_trim(stopper["text"], 40), "tone": "danger" if part == 1 else "amber"},
                "devices": [
                    {"name": s["name"], "status": _word_trim(f"{s['timestampBadge']} · {s['clue']}", 34), "icon": "alert" if i == 2 else "wifi", "suspicious": i == 2}
                    for i, s in enumerate(suspects[:3])
                ],
            },
        },
        {
            "id": f"{ep_id}-sc-03", "startSec": b[2][0], "endSec": b[2][1], "kind": "detective_evidence_twist",
            "sfxCues": [{"file": "sfx/keypad-tap-seq.wav", "offsetRatio": 0.16, "volume": 0.4}, {"file": "sfx/ussd-dial-tones.wav", "offsetRatio": 0.52, "volume": 0.58}],
            "props": {
                "variant": "cctv_backdoor", "tone": "amber" if part == 1 else "emerald",
                "badge": f"KABIR FORENSIC PIVOT · CASE #{season:02d}",
                "headline": str(brief.get("frameworkHeadline") or "Kabir Ki Jaanch Mein Chhupa Jaal Pakda Gaya!"),
                "heroImage": str(plates.get("twistHero") or "characters/handoff-shadow.png"),
                "secondaryImage": str(plates.get("twistSecondary") or "characters/kabir-investigating.png"),
                "stepOneTitle": str(brief.get("stepOneTitle") or "1 Scan / Free Connect"),
                "stepOneTag": str(brief.get("stepOneTag") or "SESSION OR UPI TRAP"),
                "stepTwoTitle": str(brief.get("stepTwoTitle") or "Silent Account Drain!"),
                "stepTwoTag": str(brief.get("stepTwoTag") or "TRACE WIPE ATTEMPT"),
                "exposedItems": list(brief.get("exposedItems") or [s["timestampBadge"] for s in suspects[:3]]),
            },
        },
        {
            "id": f"{ep_id}-sc-04", "startSec": b[3][0], "endSec": b[3][1], "kind": "detective_evidence_twist",
            "sfxCues": [{"file": "sfx/heartbeat-radar-ping.wav", "offsetFrames": 3, "volume": 0.46}, {"file": "sfx/stamp-slam.wav", "offsetRatio": 0.45, "volume": 0.36}],
            "props": {
                "variant": "contact_match", "tone": "crimson" if part == 1 else "emerald", "lockedParallax": True,
                "badge": "SURAKSHA KAVACH · 1930 GOLDEN HOUR",
                "headline": str(brief.get("payoffHeadline") or "UPI PIN Sirf Bhejne Par Lagta Hai · 1930 Milaiye!"),
                "heroImage": str(plates.get("payoffHero") or "characters/kabir-closeup.png"),
                "secondaryImage": str(plates.get("payoffSecondary") or "characters/kabir-investigating.png"),
                "radarPinLabel": "LIVE FORENSIC LOCK · 1930 SHIELD",
                "crossedOutLabel": "ANJAAN CALL SCAM NAHI",
                "matchHeadline": str(brief.get("matchHeadline") or "LOBBY KE ANDAR HI ASLI JAAL HAI!"),
                "matchSubline": _word_trim(real_inc["lesson"], 68),
                "verdictPillLeft": "▲ VERIFY PAYEE & WIFI",
                "verdictPillRight": "CALL 1930 GOLDEN HOUR",
            },
        },
        {
            "id": f"{ep_id}-sc-05", "startSec": b[4][0], "endSec": b[4][1], "kind": "detective_suspect_board",
            "sfxCues": [{"file": "sfx/cliffhanger-tick.wav", "offsetFrames": 4, "volume": 0.34}],
            "props": {
                "boardMode": "suspect_vote" if part == 1 else "next_case_vote",
                "prompt": str(brief.get("votePrompt") or ("ASLI JAAL KAUNSA HAI?" if part == 1 else "AGLA CASE KAUNSA KHOLEIN?")),
                "partBadge": "PART 2 JALD" if part == 1 else "NAYA CASE JALD",
                "spotlightRightBadge": f"CASE #{season:02d} LIVE",
                "followHandleLine": "PART 2 REVEAL KE LIYE FOLLOW @CYBERJASOOS" if part == 1 else "AGLA CASE DEKHNE KE LIYE FOLLOW @CYBERJASOOS",
                "forensicClueBar": f"CYBER JASOOS · {case_tag}",
                "suspects": suspects,
                "optionTimingsSec": [round(sc5_dur * 0.16, 2), round(sc5_dur * 0.34, 2), round(sc5_dur * 0.52, 2)],
                "ctaLine": "Asli jaal kaunsa? A, B, C comment!" if part == 1 else "Agla Case? A, B, C comment!",
                "loopBridgeText": seg_specs[-1]["ttsClauses"][-1]["roman"].split(",")[-1].strip(),
            },
        },
    ]
