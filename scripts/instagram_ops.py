#!/usr/bin/env python3
"""Cyber Jasoos (@cyberjasoos) Instagram Reels publish gate, poll tally, and Socratic reply CLI."""

import argparse, datetime as dt, json, re, sys
from pathlib import Path
from zoneinfo import ZoneInfo

if str(SCRIPTS_DIR := Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from apply_poll_result import apply_poll_branch  # noqa: E402
from growth_ledger import DEFAULT_DEFAULTS_PATH, learn_optimal_defaults, record_episode_outcome  # noqa: E402
from ig_graph_client import InstagramGraphClient  # noqa: E402
from validate_episode import validate_manifest  # noqa: E402

OWNER_HANDLES = {"cyberjasoos", "thecyberjasoos", "realcyberjasoos", "thecyberjasoos.in", "cyberjasoos.official", "askcyberjasoos"}
IST = ZoneInfo("Asia/Kolkata")
ALIAS_STOPWORDS = {"ka", "ki", "ke", "ko", "se", "mein", "par", "the", "and", "for", "trap", "case", "option", "pados", "smart"}
NON_USER_PREFIXES = {"option", "opt", "vote", "pick", "ans", "answer", "case", "suspect", "choice"}
STANDALONE_RE = re.compile(r"^[\s(\[{'\"*#]*([abcABC])[\s)\]}'\"*!?.0-9%]*$")
MULTI_OPT_RE = re.compile(r"(?<![a-z0-9])([abc])\s*(?:ya|or|aur|and|/|vs|,)\s*([abc])(?![a-z0-9])", re.I)
CUE_BEFORE_RE = re.compile(r"(?:option|opt|choice|case|suspect|vote(?:\s+for)?|pick|ans|answer|meri\s+taraf\s+se|mera\s+vote|mere\s+hisab\s+se|lagta\s+hai|i\s+think|definitely|surely|pakka|lock|team|bhai|yaar)\s*[:=\-(]*\s*(?<![a-z0-9])([abc])(?![a-z0-9])", re.I)
CUE_AFTER_RE = re.compile(r"(?<![a-z0-9])([abc])(?![a-z0-9])\s*[\).:\-]*\s*(?:pakka|lock|confirm|confirmed|100%|hi\s+hai|hai|hoga|niklega|gaddar|chor|culprit|suspect|option|choice|wala|wali)", re.I)
ENGLISH_ARTICLE_A_RE = re.compile(r"^\s*A\s+(?:great|good|nice|super|very|real|true|lot|bit|few|little|must|new|big|huge|masterpiece|brilliant|fantastic)\b")
SOCRATIC_TEMPLATES: dict[str, tuple[str, ...]] = {
    "A": ("{p}{label} par shak tez hai, par {clue} ke baad saboot kisne mitaya hoga?",
          "{p}teekhi nazar! Kya {label} akele yeh khel rach sakta tha, ya peeche koi aur hai?",
          "{p}agar {label} par lock karein, toh baaqi dono ki chhupi ghabrahat ka raaz kya hai?"),
    "B": ("{p}{label} ka suraag chubhta hai, magar kya dikhne wala har saboot asli gunahgaar hota hai?",
          "{p}sochne wali baat! {clue} par {label} ki maujoodgi ittefaq thi ya gehri saazish?",
          "{p}{label} par ungli uthi hai, par is chori se sabse bada fayda kisko tha?"),
    "C": ("{p}{label} sabse zyada ghere mein hai, par kahin yeh dhyaan bhatkane ka jaal toh nahi?",
          "{p}kya baat! {clue} wala suraag {label} ko phansata hai, ya kahani mein chhupa mor hai?",
          "{p}agar {label} mauke par dikha, toh pehla khufiya kadam kisne uthaya hoga? Sochiye!"),
    "NONE": ("{p}shukriya Jasoos saathi! A, B, ya C, sabooton ko jodkar aapka shak kis par hai?",
             "{p}asli raaz barikiyon mein hai! Teeno suraagon mein sabse badi chook kisne ki: A, B, C?",
             "{p}Part 2 mein har parda uthega, tab tak bataiye aapki nazar A, B, ya C chunti hai?"),
}


def extract_option_aliases(part1_manifest: dict | None) -> dict[str, list[str]]:
    if not isinstance(part1_manifest, dict) or not (scenes := part1_manifest.get("scenes") or []):
        return {}
    suspects = (scenes[-1].get("props") or {}).get("suspects") or [] if isinstance(scenes[-1], dict) else []
    raw_tokens, token_owners = {}, {}
    for item in (s for s in suspects if isinstance(s, dict)):
        key, name = str(item.get("key") or "").strip().upper(), str(item.get("name") or "").strip().lower()
        if key not in {"A", "B", "C"} or not name:
            continue
        phrases = [name, name.replace("-", " "), name.replace("-", "")]
        words = [w for w in re.split(r"[^a-z0-9-]+", name) if (len(w) >= 3 or w == "qr") and w not in ALIAS_STOPWORDS]
        for w in words + [w.replace("-", "") for w in words if "-" in w]:
            token_owners.setdefault(w, set()).add(key)
        raw_tokens[key] = list(dict.fromkeys([p for p in phrases if p] + words))
    return {k: [t for t in v if " " in t or len(token_owners.get(t.replace("-", ""), {k})) == 1] for k, v in raw_tokens.items()}


def classify_poll_vote(text: str, option_aliases: dict[str, list[str]] | None = None) -> str | None:
    if not isinstance(text, str) or not text.strip():
        return None
    if isinstance(option_aliases, dict) and "scenes" in option_aliases and not ({"A", "B", "C"} & option_aliases.keys()):
        option_aliases = extract_option_aliases(option_aliases)
    ascii_clean = re.sub(r"[^\x20-\x7E]+", " ", text).strip()
    if m_solo := STANDALONE_RE.match(ascii_clean):
        return m_solo.group(1).upper()
    found: set[str] = {opt.upper() for m in MULTI_OPT_RE.finditer(ascii_clean) for opt in m.groups()}
    for rx in (CUE_BEFORE_RE, CUE_AFTER_RE):
        found.update(m.group(1).upper() for m in rx.finditer(ascii_clean))
    found.update((m.group(1) or m.group(2)).upper() for m in re.finditer(r"^\s*\(?([abcABC])[\)\.:!\-]+(?:\s|$)|\(\s*([abcABC])\s*\)", ascii_clean))
    found.update(m.group(1).upper() for m in re.finditer(r"(?<![a-zA-Z0-9])([bBcC])(?![a-zA-Z0-9])", ascii_clean))
    if not ENGLISH_ARTICLE_A_RE.match(ascii_clean) and re.search(r"(?<![a-zA-Z0-9])A(?![a-zA-Z0-9])", ascii_clean):
        found.add("A")
    lowered = text.lower()
    for opt_key in ("A", "B", "C"):
        for alias in (option_aliases or {}).get(opt_key, []):
            if (na := str(alias).strip().lower()) and re.search(rf"(?<![a-z0-9]){re.escape(na)}(?![a-z0-9])", lowered):
                found.add(opt_key)
    return next(iter(found)) if len(found) == 1 else None


def tally_poll_comments(comments: list[dict], part1_manifest: dict | None = None) -> dict:
    aliases, counts, unclassified, voted_users = extract_option_aliases(part1_manifest), {"A": 0, "B": 0, "C": 0}, 0, set()
    indexed = sorted(
        [(i, c) for i, c in enumerate(comments or []) if isinstance(c, dict)],
        key=lambda p: (0, str(p[1]["timestamp"]), p[0]) if p[1].get("timestamp") else (1, "", p[0]),
    )
    for _, item in indexed:
        user = str(item.get("username") or "").strip().lstrip("@").lower()
        if user in OWNER_HANDLES:
            continue
        if (vote := classify_poll_vote(str(item.get("text") or ""), aliases)) is None:
            unclassified += 1
            continue
        if user:
            if user in voted_users:
                continue
            voted_users.add(user)
        counts[vote] += 1
    total = sum(counts.values())
    winner = max(("A", "B", "C"), key=lambda k: (counts[k], -ord(k))) if total > 0 else None
    pct = max(1, min(99, int(round((counts[winner] * 100) / total)))) if winner and total > 0 else None
    return {"counts": counts, "totalVotes": total, "winner": winner, "winnerPct": pct, "unclassifiedCount": unclassified}


def draft_socratic_reply(comment: dict, vote: str | None, part1_manifest: dict | None = None, idx: int = 0) -> str:
    meta: dict[str, tuple[str, str]] = {"A": ("Option A", "us waqt"), "B": ("Option B", "us pal"), "C": ("Option C", "us raat")}
    if isinstance(part1_manifest, dict) and (scenes := part1_manifest.get("scenes") or []):
        for s in (scenes[-1].get("props") or {}).get("suspects") or []:
            if isinstance(s, dict) and s.get("key") in meta:
                meta[s["key"]] = (str(s.get("name") or f"Option {s['key']}"), str(s.get("timestampBadge") or "us waqt"))
    user = str((comment or {}).get("username") or "").strip().lstrip("@")
    prefix = f"@{user}, " if user and user.lower() not in OWNER_HANDLES else ""
    bucket = vote if vote in {"A", "B", "C"} else "NONE"
    label, clue = meta.get(bucket, ("is shak", "us waqt"))
    reply = SOCRATIC_TEMPLATES[bucket][idx % len(SOCRATIC_TEMPLATES[bucket])].format(p=prefix, label=label, clue=clue).strip()
    reply = reply[0].upper() + reply[1:] if not prefix and reply else reply
    words = reply.split()
    return " ".join(words[:22]) if len(words) > 22 else reply


def recommend_ist_upload_slots(now_utc: dt.datetime | None = None) -> dict:
    ref = now_utc if now_utc is not None else dt.datetime.now(dt.timezone.utc)
    now_ist = (ref if ref.tzinfo else ref.replace(tzinfo=dt.timezone.utc)).astimezone(IST)
    mk = lambda h, m, win, role: (  # noqa: E731
        lambda nxt: {
            "targetIst": f"{h:02d}:{m:02d} IST", "windowIst": win, "nextSlotIst": nxt.isoformat(),
            "hoursUntil": round((nxt - now_ist).total_seconds() / 3600.0, 2), "role": role,
        }
    )((s := now_ist.replace(hour=h, minute=m, second=0, microsecond=0)) + dt.timedelta(days=int(s <= now_ist)))
    return {
        "timezone": "Asia/Kolkata", "nowIst": now_ist.isoformat(),
        "primarySlot": mk(19, 45, "19:30-20:45 IST", "Part 1 whodunit launch (peak family/post-work Saves & Shares)"),
        "secondarySlot": mk(12, 30, "12:15-13:15 IST", "Part 2 poll reveal & midday scroll spike"),
    }


def _load_comments_source(media_id: str | None, comments_file: str | None) -> list[dict]:
    if media_id:
        return InstagramGraphClient().fetch_all_comments(media_id)
    raw_text = Path(str(comments_file)).read_text(encoding="utf-8")
    if str(comments_file).lower().endswith(".json"):
        parsed = json.loads(raw_text)
        return [r if isinstance(r, dict) else {"text": str(r)} for r in (parsed.get("data", []) if isinstance(parsed, dict) else parsed)]
    out: list[dict] = []
    for i, s in ((idx, ln.strip()) for idx, ln in enumerate(raw_text.splitlines(), 1) if ln.strip()):
        m = re.match(r"^@?([A-Za-z0-9._]{2,30})\s*:\s*(.+)$", s)
        entry = {"id": f"local-{i}", "username": m.group(1), "text": m.group(2).strip()} if (m and m.group(1).lower() not in NON_USER_PREFIXES) else {"id": f"local-{i}", "text": s}
        out.append(entry)
    return out


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cyber Jasoos Instagram Graph API & Poll-Tally CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("best-time", help="Recommend next IST Reels upload windows.")
    p_pub = sub.add_parser("publish-reel", help="Validate --publish-ready gate and publish 9:16 Reel.")
    for flag in ("--episode", "--video"):
        p_pub.add_argument(flag, required=True)
    for flag in ("--dry-run", "--post-poll-comment"):
        p_pub.add_argument(flag, action="store_true")
    sub.add_parser("insights", help="Fetch Reel metrics plus save/share rates.").add_argument("--media-id", required=True)
    for name, extra in (("poll-tally", ("--apply-to",)), ("reply-comments", ("--limit", "--approve"))):
        p = sub.add_parser(name)
        grp = p.add_mutually_exclusive_group(required=True)
        grp.add_argument("--media-id")
        grp.add_argument("--comments-file")
        p.add_argument("--part1")
        if "--apply-to" in extra:
            p.add_argument("--apply-to")
        else:
            p.add_argument("--limit", type=int, default=15)
            p.add_argument("--approve", action="store_true")
            p.add_argument("--yes", action="store_true", help="Skip interactive y/N prompt when --approve is set.")
    p_rec = sub.add_parser("record-metrics", help="Record Reel telemetry into SQLite growth ledger.")
    p_rec.add_argument("--episode", required=True)
    p_rec.add_argument("--media-id")
    p_rec.add_argument("--metrics-json")
    p_rec.add_argument("--poll-votes", type=int, default=None)
    p_rec.add_argument("--posted-hour-ist", type=int, default=19)
    p_rec.add_argument("--hook-style", default="mid_crime_shock")
    p_rec.add_argument("--db")
    p_lrn = sub.add_parser("learn", help="Learn optimal duration, WPM, hook, and IST hour from top Reels.")
    p_lrn.add_argument("--db")
    p_lrn.add_argument("--out", default=str(DEFAULT_DEFAULTS_PATH))
    return ap


def _parse_metrics_arg(raw: str) -> dict:
    s = raw.strip()
    if not s.startswith("{") and Path(s).is_file():
        return json.loads(Path(s).read_text(encoding="utf-8"))
    return json.loads(s)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd == "best-time":
        print(json.dumps(recommend_ist_upload_slots(), indent=2))
        return 0
    if args.cmd == "record-metrics":
        if not args.media_id and not args.metrics_json:
            print("record-metrics requires --media-id and/or --metrics-json.", file=sys.stderr)
            return 1
        manifest = json.loads(Path(args.episode).read_text(encoding="utf-8"))
        metrics: dict = InstagramGraphClient().get_media_insights(args.media_id) if args.media_id else {}
        if args.metrics_json:
            metrics.update(_parse_metrics_arg(args.metrics_json))
        if args.poll_votes is not None:
            metrics["poll_votes"] = args.poll_votes
        rec = record_episode_outcome(
            manifest, metrics, db_path=Path(args.db) if args.db else None,
            posted_hour_ist=args.posted_hour_ist, hook_style=args.hook_style,
        )
        print(json.dumps(rec, indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "learn":
        summary = learn_optimal_defaults(Path(args.db) if args.db else None, Path(args.out) if args.out else None)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "publish-reel":
        manifest = json.loads(Path(args.episode).read_text(encoding="utf-8"))
        if errs := validate_manifest(manifest, publish_ready=True):
            print("Publish-Ready Gate Blocked:\n- " + "\n- ".join(errs), file=sys.stderr)
            return 2
        mp4, post_copy = Path(args.video), manifest.get("postCopy") or {}
        caption = f"{post_copy.get('instagramCaption', '').strip()}\n\n{' '.join(post_copy.get('hashtags') or [])}".strip()
        if not mp4.is_file() or mp4.stat().st_size <= 0 or not (0 < len(caption) <= 2200):
            print(f"Invalid video ({mp4}) or caption length ({len(caption)}/2200).", file=sys.stderr)
            return 1
        if args.dry_run:
            print(json.dumps({"status": "dry_run_ok", "episodeId": manifest["id"], "captionLength": len(caption)}, indent=2))
            return 0
        client = InstagramGraphClient()
        res = client.publish_reel_resumable(mp4, caption=caption)
        if args.post_poll_comment and (pin := str(post_copy.get("pinnedCommentVote") or "").strip()) and res.get("media_id"):
            res["pollComment"] = client.post_comment(str(res["media_id"]), pin)
        print(json.dumps(res, indent=2))
        return 0
    if args.cmd == "insights":
        print(json.dumps(InstagramGraphClient().get_media_insights(args.media_id), indent=2))
        return 0
    p1 = json.loads(Path(args.part1).read_text(encoding="utf-8")) if args.part1 else None
    comments = _load_comments_source(args.media_id, args.comments_file)
    if args.cmd == "poll-tally":
        tally = tally_poll_comments(comments, p1)
        if args.apply_to and tally["totalVotes"] > 0 and tally["winner"]:
            p2_path = Path(args.apply_to)
            updated = apply_poll_branch(json.loads(p2_path.read_text(encoding="utf-8")), tally["winner"], tally["winnerPct"])
            p2_path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            tally["appliedTo"] = str(p2_path)
        print(json.dumps(tally, indent=2, ensure_ascii=False))
        return 0
    aliases, seen_users, drafts, client = extract_option_aliases(p1), set(), [], (InstagramGraphClient() if args.approve else None)
    for c in comments:
        user = str(c.get("username") or "").strip().lstrip("@").lower()
        if user in OWNER_HANDLES or (user and user in seen_users):
            continue
        if user:
            seen_users.add(user)
        vote = classify_poll_vote(str(c.get("text") or ""), aliases)
        reply_txt = draft_socratic_reply(c, vote, p1, idx=len(drafts))
        entry = {"commentId": c.get("id"), "username": user or None, "vote": vote, "reply": reply_txt}
        if client is not None:
            ok = args.yes or (sys.stdin.isatty() and input(f"Post reply to @{user or c.get('id')}: '{reply_txt}'? [y/N]: ").strip().lower() in {"y", "yes"})
            entry["apiResult"] = client.reply_to_comment(str(c["id"]), reply_txt) if ok else {"skipped": True}
        drafts.append(entry)
        if len(drafts) >= max(1, args.limit):
            break
    print(json.dumps({"approved": bool(args.approve), "count": len(drafts), "replies": drafts}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
