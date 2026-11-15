#!/usr/bin/env python3
"""Cyber Hook Retention Scorer (0-100) and optional yt-dlp URL hook analyzer."""

import argparse
import json
import re
import shutil
import subprocess
import sys

TIMESTAMP_OR_NUMBER_RE = re.compile(
    r"(?:\b\d+(?:[:.,]\d+)*%?|\$\d+(?:\.\d+)?[kmbKMB]?|\b(?:zero-day|midnight|million|billion|thousand)\b)",
    re.IGNORECASE,
)

ACTIVE_BREACH_VERBS_RE = re.compile(
    r"\b(?:"
    r"breach\w*|hack\w*|compromis\w*|exfiltrat\w*|encrypt\w*|ransom\w*|"
    r"leak\w*|stole\w*|wiped|wiper|hijack\w*|exploit\w*|pivot\w*|escalat\w*|"
    r"lateral|untracked|rogue|exposed|offline|outage|alert\w*|paged|fired|"
    r"attacker\w*|intruder\w*|root|shell|credential\w*|token\w*|crown[- ]jewel\w*|"
    r"kill[- ]switch|isolat\w*|shut[- ]?down|drain\w*|bleeding|triggered"
    r")\b",
    re.IGNORECASE,
)

CURIOSITY_GAP_RE = re.compile(
    r"(?:\?|\b(?:"
    r"but|yet|instead|wrong|lied|failed|ignored|missed|nobody|never|"
    r"actually|secretly|while|until|everyone|still|without|you|your|voted|picked"
    r")\b)",
    re.IGNORECASE,
)

TEXTBOOK_FILLER_PATTERNS = (
    r"\bin this video\b",
    r"\bwelcome back\b",
    r"\btoday we will\b",
    r"\bwe will learn\b",
    r"\blearn about\b",
    r"\bhey guys\b",
    r"\blet'?s explore\b",
    r"\bhave you ever wondered\b",
    r"\bdelve(?:\s+into)?\b",
    r"\bin today'?s digital\b",
    r"\bis the process of\b",
    r"\bis defined as\b",
    r"\bis an? (?:important|essential|crucial)\b",
    r"\bcomprehensive guide\b",
    r"\bwhy it matters\b",
)

OPENING_SWIPE_RE = re.compile(
    r"^[\s\"'“”‘’]*(?:in this video|welcome back|today we will|hey guys|let'?s explore|have you ever wondered)",
    re.IGNORECASE,
)


def score_hook(text: str) -> dict:
    cleaned = (text or "").strip()
    words = [w for w in cleaned.split() if w]
    word_count = len(words)
    if word_count == 0:
        return {
            "hook": cleaned,
            "score": 0,
            "wordCount": 0,
            "breakdown": {
                "timestampOrNumbers": 0,
                "activeBreachVerbs": 0,
                "curiosityGap": 0,
                "conciseLength": 0,
                "zeroFiller": 0,
                "swipePenalty": 0,
            },
            "hints": ["Provide a non-empty opening hook (< 22 words)."],
        }

    has_numbers = bool(TIMESTAMP_OR_NUMBER_RE.search(cleaned))
    has_breach = bool(ACTIVE_BREACH_VERBS_RE.search(cleaned))
    has_gap = bool(CURIOSITY_GAP_RE.search(cleaned))
    is_concise = 3 <= word_count < 22
    filler_hits = [
        pat for pat in TEXTBOOK_FILLER_PATTERNS if re.search(pat, cleaned, re.IGNORECASE)
    ]
    zero_filler = len(filler_hits) == 0
    swipe_penalty = -10 if OPENING_SWIPE_RE.search(cleaned) else 0

    breakdown = {
        "timestampOrNumbers": 20 if has_numbers else 0,
        "activeBreachVerbs": 20 if has_breach else 0,
        "curiosityGap": 20 if has_gap else 0,
        "conciseLength": 20 if is_concise else 0,
        "zeroFiller": 20 if zero_filler else 0,
        "swipePenalty": swipe_penalty,
    }
    raw_total = sum(breakdown.values())
    final_score = max(0, min(100, raw_total))

    hints: list[str] = []
    if not has_numbers:
        hints.append("Anchor with a concrete timestamp or metric (e.g., '02:14 AM', '$4.2M', '64%').")
    if not has_breach:
        hints.append("Inject an active breach/stakes verb ('leaked', 'compromised', 'untracked', 'isolated').")
    if not has_gap:
        hints.append("Add a contradiction or viewer callout ('while every alert stayed green', '64% of you voted').")
    if not is_concise:
        hints.append(f"Trim hook to < 22 words (currently {word_count} words) so the punch lands in < 3.5s.")
    if not zero_filler:
        hints.append("Delete textbook/AI throat-clearing ('In this video', 'we will learn', 'let's explore').")

    return {
        "hook": cleaned,
        "score": final_score,
        "wordCount": word_count,
        "breakdown": breakdown,
        "hints": hints,
    }


def calculate_hook_score(text: str) -> int:
    return int(score_hook(text)["score"])


def analyze_url_with_ytdlp(url: str) -> dict:
    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        raise RuntimeError("yt-dlp is not installed on PATH; install yt-dlp or use --score '<text>'.")
    res = subprocess.run(
        [ytdlp, "--dump-single-json", "--no-warnings", "--skip-download", url],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if res.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {res.stderr.strip() or 'unknown error'}")
    meta = json.loads(res.stdout)
    title = str(meta.get("title") or "").strip()
    desc = str(meta.get("description") or "").strip().splitlines()
    first_desc = desc[0].strip() if desc else ""
    candidate = title if len(title.split()) >= 5 else f"{title}. {first_desc}".strip(". ")
    result = score_hook(candidate)
    result["sourceUrl"] = url
    result["videoTitle"] = title
    return result


def _print_report(result: dict) -> None:
    print(f"Cyber Hook Retention Score: {result['score']}/100 ({result['wordCount']} words)")
    print(f"Hook: \"{result['hook']}\"")
    bd = result["breakdown"]
    print(
        "Breakdown: "
        f"numbers={bd['timestampOrNumbers']:+d}, "
        f"breach_verbs={bd['activeBreachVerbs']:+d}, "
        f"curiosity_gap={bd['curiosityGap']:+d}, "
        f"concise={bd['conciseLength']:+d}, "
        f"zero_filler={bd['zeroFiller']:+d}"
        + (f", swipe_penalty={bd['swipePenalty']:+d}" if bd["swipePenalty"] else "")
    )
    if result["hints"]:
        print("Rewrite Hints:")
        for hint in result["hints"]:
            print(f"  - {hint}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score short-form cyber hooks (0-100).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--score", dest="hook_text", help="Hook sentence to score directly.")
    group.add_argument("--analyze-url", dest="url", help="Short/Reel/YouTube URL via yt-dlp.")
    parser.add_argument("--json", action="store_true", help="Output JSON payload.")
    args = parser.parse_args(argv)

    try:
        result = score_hook(args.hook_text) if args.hook_text is not None else analyze_url_with_ytdlp(args.url)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_report(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
