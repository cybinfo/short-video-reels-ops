#!/usr/bin/env python3
"""Apply live Part-1 audience poll results (A/B/C + percentage) to a Part-2 Cyber Jasoos episode manifest."""

import argparse, copy, json, sys
from pathlib import Path

HINDI_URDU_NUMS: dict[int, tuple[str, str]] = {
    1: ("Ek", "ایک"), 2: ("Do", "دو"), 3: ("Teen", "تین"),
    4: ("Chaar", "چار"), 5: ("Paanch", "پانچ"), 6: ("Chhah", "چھ"),
    7: ("Saat", "سات"), 8: ("Aath", "آٹھ"), 9: ("Nau", "نو"),
    10: ("Das", "دس"), 11: ("Gyaarah", "گیارہ"), 12: ("Baarah", "بارہ"),
    13: ("Terah", "تیرہ"), 14: ("Chaudah", "چودہ"), 15: ("Pandrah", "پندرہ"),
    16: ("Solah", "سولہ"), 17: ("Satrah", "سترہ"), 18: ("Athaarah", "اٹھارہ"),
    19: ("Unnees", "انیس"), 20: ("Bees", "بیس"), 21: ("Ikkis", "اکیس"),
    22: ("Baais", "بائیس"), 23: ("Teis", "تئیس"), 24: ("Chaubis", "چوبیس"),
    25: ("Pachchis", "پچیس"), 26: ("Chhabbis", "چھبیس"), 27: ("Sattaais", "ستائیس"),
    28: ("Athaais", "اٹھائیس"), 29: ("Untis", "انتیس"), 30: ("Tees", "تیس"),
    31: ("Iktis", "اکتیس"), 32: ("Battis", "بتیس"), 33: ("Taintis", "تینتیس"),
    34: ("Chauntis", "چونتیس"), 35: ("Paintis", "پینتیس"), 36: ("Chhattis", "چھتیس"),
    37: ("Saintis", "سینتیس"), 38: ("Artis", "اڑتیس"), 39: ("Untaalis", "انتالیس"),
    40: ("Chaalis", "چالیس"), 41: ("Iktaalis", "اکتالیس"), 42: ("Bayaalis", "بیالیس"),
    43: ("Taintaalis", "تینتالیس"), 44: ("Chauvaalis", "چوالیس"), 45: ("Paintaalis", "پینتالیس"),
    46: ("Chhiyaalis", "چھیالیس"), 47: ("Saintaalis", "سینتالیس"), 48: ("Artaalis", "اڑتالیس"),
    49: ("Unchaas", "انچاس"), 50: ("Pachaas", "پچاس"), 51: ("Ikyaavan", "اکیاون"),
    52: ("Baavan", "باون"), 53: ("Tirpan", "ترپن"), 54: ("Chauvan", "چوون"),
    55: ("Pachpan", "پچپن"), 56: ("Chhappan", "چھپن"), 57: ("Sattaavan", "ستاون"),
    58: ("Athavan", "اٹھاون"), 59: ("Unsath", "انسٹھ"), 60: ("Saath", "ساٹھ"),
    61: ("Iksath", "اکسٹھ"), 62: ("Baasath", "باسٹھ"), 63: ("Tirsath", "ترسٹھ"),
    64: ("Chausath", "چونسٹھ"), 65: ("Painsath", "پینسٹھ"), 66: ("Chhiyaasath", "چھیاسٹھ"),
    67: ("Sarsath", "سڑسٹھ"), 68: ("Arsath", "اڑسٹھ"), 69: ("Unhattar", "انہتر"),
    70: ("Sattar", "ستر"), 71: ("Ikhattar", "اکہتر"), 72: ("Bahattar", "بہتر"),
    73: ("Tihattar", "تہتر"), 74: ("Chauhattar", "چوہتر"), 75: ("Pachhattar", "پچہتر"),
    76: ("Chhihattar", "چھہتر"), 77: ("Sathattar", "ستتر"), 78: ("Athhattar", "اٹھہتر"),
    79: ("Unaasi", "اناسی"), 80: ("Assi", "اسی"), 81: ("Ikyaasi", "اکیاسی"),
    82: ("Bayaasi", "بیاسی"), 83: ("Tiraasi", "تراسی"), 84: ("Chauraasi", "چوراسی"),
    85: ("Pachaasi", "پچاسی"), 86: ("Chhiyaasi", "چھیاسی"), 87: ("Sattaasi", "ستاسی"),
    88: ("Athaasi", "اٹھاسی"), 89: ("Navaasi", "نواسی"), 90: ("Nabbe", "نوے"),
    91: ("Ikyaanve", "اکیانوے"), 92: ("Baanve", "بانوے"), 93: ("Tiraanve", "ترانوے"),
    94: ("Chauraanve", "چورانوے"), 95: ("Pachaanve", "پچانوے"), 96: ("Chhiyaanve", "چھیانوے"),
    97: ("Sattaanve", "ستانوے"), 98: ("Athaanve", "اٹھانوے"), 99: ("Ninyanve", "ننانوے"),
}


def _pct_words(pct: int) -> tuple[str, str]:
    if pct not in HINDI_URDU_NUMS:
        raise ValueError(f"pct must be an integer in [1, 99] (got {pct!r}).")
    return HINDI_URDU_NUMS[pct]


def _render_templates(obj: object, tokens: dict[str, str]) -> object:
    if isinstance(obj, str):
        out = obj
        for k, v in tokens.items():
            out = out.replace(f"{{{k}}}", v)
        return out
    if isinstance(obj, list):
        return [_render_templates(item, tokens) for item in obj]
    if isinstance(obj, dict):
        return {k: _render_templates(v, tokens) for k, v in obj.items()}
    return obj


def apply_poll_branch(manifest: dict, winner: str, pct: int | None = None) -> dict:
    win = str(winner).strip().upper()
    if win not in {"A", "B", "C"}:
        raise ValueError(f"winner must be A, B, or C (got {winner!r}).")
    if pct is None:
        raw_prev = ((manifest.get("hook") or {}).get("previousVoteResult") or {}).get("percentage")
        if isinstance(raw_prev, (int, float)) and not isinstance(raw_prev, bool):
            pct = int(raw_prev)
        else:
            raise ValueError(
                "--pct (1..99) is required when hook.previousVoteResult.percentage is not already set."
            )
    if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 99):
        raise ValueError(f"pct must be an integer in [1, 99] (got {pct!r}).")
    branches = manifest.get("pollBranches")
    if not isinstance(branches, dict) or win not in branches or not isinstance(branches[win], dict):
        raise KeyError(f"Manifest '{manifest.get('id')}' has no pollBranches[{win!r}] definition.")

    pct_word, pct_urdu = _pct_words(pct)
    tokens = {"pct": str(pct), "pct_word": pct_word, "pct_urdu": pct_urdu}
    branch = _render_templates(copy.deepcopy(branches[win]), tokens)
    assert isinstance(branch, dict)

    out = copy.deepcopy(manifest)
    if "episodeTitle" in branch:
        out["episodeTitle"] = branch["episodeTitle"]
    if "coldOpenTag" in branch:
        out["coldOpenTag"] = branch["coldOpenTag"]

    hook = out.setdefault("hook", {})
    if "openingLine" in branch:
        hook["openingLine"] = branch["openingLine"]
    prev_vote = hook.setdefault("previousVoteResult", {})
    prev_vote["winningOption"] = win
    prev_vote["percentage"] = pct
    if "outcomeVerdict" in branch:
        prev_vote["outcomeVerdict"] = branch["outcomeVerdict"]

    segments = out.get("scriptSegments")
    if isinstance(segments, list) and segments and isinstance(branch.get("seg01"), dict):
        seg0 = segments[0]
        b_seg = branch["seg01"]
        for field in ("narration", "ttsClauses", "highlightKeywords"):
            if field in b_seg:
                seg0[field] = b_seg[field]

    scenes = out.get("scenes")
    if isinstance(scenes, list) and scenes and isinstance(branch.get("scene01Props"), dict):
        sc0_props = scenes[0].setdefault("props", {})
        for field in ("phoneStatus", "scrollStopper", "shotTitles"):
            if field in branch["scene01Props"]:
                sc0_props[field] = branch["scene01Props"][field]

    if isinstance(branch.get("postCopy"), dict):
        out["postCopy"] = {**out.get("postCopy", {}), **branch["postCopy"]}

    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply live Part-1 poll winner (A/B/C) & pct to Part-2 manifest.")
    parser.add_argument("--episode", required=True, help="Path to Part-2 episode JSON manifest.")
    parser.add_argument("--winner", required=True, choices=("A", "B", "C", "a", "b", "c"), help="Winning poll option.")
    parser.add_argument("--pct", type=int, default=None, help="Winning option vote percentage (1..99; required unless hook.previousVoteResult.percentage is already set).")
    parser.add_argument("--output", help="Optional output path (defaults to updating --episode in place).")
    args = parser.parse_args(argv)

    ep_path = Path(args.episode)
    if not ep_path.is_file():
        print(f"Episode manifest not found: {ep_path}", file=sys.stderr)
        return 1
    try:
        manifest = json.loads(ep_path.read_text(encoding="utf-8"))
        updated = apply_poll_branch(manifest, args.winner.upper(), args.pct)
        applied_pct = updated["hook"]["previousVoteResult"]["percentage"]
        dst = Path(args.output) if args.output else ep_path
        dst.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"Failed to apply poll result: {exc}", file=sys.stderr)
        return 1
    print(f"Applied poll winner {args.winner.upper()} ({applied_pct}%) -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
