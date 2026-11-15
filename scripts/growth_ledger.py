#!/usr/bin/env python3
"""SQLite growth telemetry ledger & Adam Mosseri Reels ranking auto-learner for Cyber Jasoos."""

import argparse, datetime as dt, json, math, sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "growth_ledger.sqlite3"
DEFAULT_DEFAULTS_PATH = REPO_ROOT / "data" / "learned_defaults.json"
COLD_START_PRIORS: dict[str, object] = {
    "mode": "cold_start_prior", "sampleSize": 0, "targetDurationSec": 52.0,
    "targetWpm": 168, "preferredHookStyle": "mid_crime_shock", "preferredIstHour": 19, "topEpisodes": [],
}
TABLE_DDL = """
CREATE TABLE IF NOT EXISTS episode_metrics (
    episode_id TEXT PRIMARY KEY, media_id TEXT, season INTEGER, part INTEGER,
    duration_sec REAL, actual_wpm REAL, hook_style TEXT, payoff_type TEXT,
    suspect_count INTEGER, posted_hour_ist INTEGER, views INTEGER, reach INTEGER,
    saved INTEGER, shares INTEGER, comments_count INTEGER, poll_votes INTEGER,
    save_rate_pct REAL, share_rate_pct REAL, vote_rate_pct REAL, mosseri_score REAL, recorded_at TEXT
);
"""


def compute_mosseri_score(save_rate_pct: float, share_rate_pct: float, vote_rate_pct: float) -> float:
    """Weighted Reels composite per Adam Mosseri ranking signals (Sends/Shares > Saves > Poll Votes)."""
    return round(0.45 * float(share_rate_pct) + 0.35 * float(save_rate_pct) + 0.20 * float(vote_rate_pct), 3)


def _infer_part(manifest: dict) -> int:
    if isinstance(manifest.get("part"), int) and not isinstance(manifest.get("part"), bool):
        return 1 if manifest["part"] == 1 else 2
    badge = str(manifest.get("hudPartBadge") or "").upper()
    if "PART 2" in badge or "2/2" in badge:
        return 2
    if "PART 1" in badge or "1/2" in badge:
        return 1
    hook = manifest.get("hook") if isinstance(manifest.get("hook"), dict) else {}
    if manifest.get("pollBranches") or hook.get("previousVoteResult") or hook.get("hookPattern") == "comment_callout":
        return 2
    cliff = manifest.get("cliffhanger")
    if isinstance(cliff, dict):
        return 1 if (cliff.get("options") or cliff.get("poll") or cliff.get("suspects")) else 2
    scenes = manifest.get("scenes") if isinstance(manifest.get("scenes"), list) else []
    if scenes and isinstance(scenes[-1], dict):
        last = scenes[-1]
        props = last.get("props") if isinstance(last.get("props"), dict) else {}
        if props.get("boardMode") == "next_case_vote":
            return 2
        if props.get("options") or props.get("poll") or props.get("suspects") or last.get("options"):
            return 1
    return 2


def _infer_payoff_and_suspects(manifest: dict) -> tuple[str, int]:
    scenes = [s for s in (manifest.get("scenes") or []) if isinstance(s, dict)]
    payoff_type = str(manifest.get("payoffType") or "").strip()
    if not payoff_type:
        for sc in reversed(scenes):
            kind = sc.get("kind")
            props = sc.get("props") if isinstance(sc.get("props"), dict) else {}
            if kind == "detective_evidence_twist":
                payoff_type = str(props.get("variant") or "detective_evidence_twist")
                break
            if kind == "payoff_proof_card":
                payoff_type = "payoff_proof_card"
                break
    suspect_count = 0
    if scenes:
        last_props = scenes[-1].get("props") if isinstance(scenes[-1].get("props"), dict) else {}
        choices = last_props.get("suspects") or last_props.get("options") or []
        if isinstance(choices, list):
            suspect_count = len(choices)
    if suspect_count == 0 and isinstance(manifest.get("cliffhanger"), dict):
        opts = manifest["cliffhanger"].get("options") or manifest["cliffhanger"].get("suspects") or []
        if isinstance(opts, list):
            suspect_count = len(opts)
    return (payoff_type or "actionable_shield"), suspect_count


def _extract_actual_wpm(manifest: dict, duration_sec: float) -> float:
    segs = [s for s in (manifest.get("scriptSegments") or []) if isinstance(s, dict)]
    words = sum(len(str(s.get("narration") or "").split()) for s in segs)
    return round(words / (duration_sec / 60.0), 2) if duration_sec > 0 else 0.0


def _ensure_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(TABLE_DDL)
    return conn


def record_episode_outcome(
    manifest: dict,
    metrics: dict,
    db_path: Path | None = None,
    posted_hour_ist: int = 19,
    hook_style: str = "mid_crime_shock",
) -> dict:
    """Extract manifest telemetry + IG reach rates, upsert into SQLite, and return stored record."""
    if not isinstance(manifest, dict) or not str(manifest.get("id") or "").strip():
        raise ValueError("manifest must be a dict with a non-empty 'id'.")
    metrics = metrics if isinstance(metrics, dict) else {}
    target_db = Path(db_path) if db_path is not None else DEFAULT_DB_PATH

    ep_id = str(manifest["id"]).strip()
    media_id = str(metrics.get("media_id") or "").strip()
    season = int(manifest.get("season") or 1)
    part = _infer_part(manifest)
    duration_sec = round(float(manifest.get("durationSeconds") or 0.0), 3)
    actual_wpm = _extract_actual_wpm(manifest, duration_sec)
    payoff_type, suspect_count = _infer_payoff_and_suspects(manifest)
    if metrics.get("payoff_type"):
        payoff_type = str(metrics["payoff_type"]).strip()
    resolved_hook = str(hook_style or (manifest.get("hook") or {}).get("hookPattern") or "mid_crime_shock").strip()
    hour_ist = int(posted_hour_ist) % 24

    views = int(metrics.get("views") or 0)
    reach = int(metrics.get("reach") or 0)
    saved = int(metrics.get("saved") or 0)
    shares = int(metrics.get("shares") or 0)
    raw_comments = metrics.get("comments_count") if metrics.get("comments_count") is not None else metrics.get("comments")
    comments_count = int(raw_comments or 0)
    poll_votes = int(metrics.get("poll_votes") or 0)

    if reach > 0:
        save_rate_pct = round((saved / reach) * 100.0, 3)
        share_rate_pct = round((shares / reach) * 100.0, 3)
        vote_rate_pct = round((poll_votes / reach) * 100.0, 3)
    else:
        save_rate_pct = round(float(metrics.get("save_rate_pct") or 0.0), 3)
        share_rate_pct = round(float(metrics.get("share_rate_pct") or 0.0), 3)
        vote_rate_pct = round(float(metrics.get("vote_rate_pct") or 0.0), 3)

    mosseri_score = compute_mosseri_score(save_rate_pct, share_rate_pct, vote_rate_pct)
    recorded_at = dt.datetime.now(dt.timezone.utc).isoformat()

    row_tuple = (
        ep_id, media_id, season, part, duration_sec, actual_wpm, resolved_hook, payoff_type,
        suspect_count, hour_ist, views, reach, saved, shares, comments_count, poll_votes,
        save_rate_pct, share_rate_pct, vote_rate_pct, mosseri_score, recorded_at,
    )
    with _ensure_db(target_db) as conn:
        conn.execute(
            """
            INSERT INTO episode_metrics (
                episode_id, media_id, season, part, duration_sec, actual_wpm, hook_style, payoff_type,
                suspect_count, posted_hour_ist, views, reach, saved, shares, comments_count, poll_votes,
                save_rate_pct, share_rate_pct, vote_rate_pct, mosseri_score, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(episode_id) DO UPDATE SET
                media_id=excluded.media_id, season=excluded.season, part=excluded.part,
                duration_sec=excluded.duration_sec, actual_wpm=excluded.actual_wpm,
                hook_style=excluded.hook_style, payoff_type=excluded.payoff_type,
                suspect_count=excluded.suspect_count, posted_hour_ist=excluded.posted_hour_ist,
                views=excluded.views, reach=excluded.reach, saved=excluded.saved,
                shares=excluded.shares, comments_count=excluded.comments_count,
                poll_votes=excluded.poll_votes, save_rate_pct=excluded.save_rate_pct,
                share_rate_pct=excluded.share_rate_pct, vote_rate_pct=excluded.vote_rate_pct,
                mosseri_score=excluded.mosseri_score, recorded_at=excluded.recorded_at
            """,
            row_tuple,
        )
        stored = conn.execute("SELECT * FROM episode_metrics WHERE episode_id = ?", (ep_id,)).fetchone()
    return dict(stored)


def _summarize_top_row(row: dict) -> dict:
    keys = ("episode_id", "mosseri_score", "duration_sec", "actual_wpm", "hook_style", "posted_hour_ist")
    return {k: row[k] for k in keys}


def learn_optimal_defaults(db_path: Path | None = None, out_json: Path | None = None) -> dict:
    """Derive empirical pacing, hook, and IST posting defaults once >= 3 episodes are recorded."""
    target_db = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    rows: list[dict] = []
    if target_db.is_file():
        sql = "SELECT * FROM episode_metrics ORDER BY mosseri_score DESC, share_rate_pct DESC, save_rate_pct DESC, episode_id ASC"
        with _ensure_db(target_db) as conn:
            rows = [dict(r) for r in conn.execute(sql).fetchall()]
    n = len(rows)
    if n < 3:
        result: dict[str, object] = {**COLD_START_PRIORS, "sampleSize": n, "topEpisodes": [_summarize_top_row(r) for r in rows]}
    else:
        top_half = rows[: math.ceil(n / 2)]
        weights = [max(float(r["mosseri_score"] or 0.0), 0.01) for r in top_half]
        w_sum = sum(weights)
        avg_dur = sum(w * float(r["duration_sec"]) for w, r in zip(weights, top_half)) / w_sum
        avg_wpm = sum(w * float(r["actual_wpm"]) for w, r in zip(weights, top_half)) / w_sum
        hook_scores: dict[str, float] = {}
        hour_scores: dict[int, float] = {}
        for w, r in zip(weights, top_half):
            hk = str(r.get("hook_style") or "mid_crime_shock")
            hr = int(r.get("posted_hour_ist") if r.get("posted_hour_ist") is not None else 19)
            hook_scores[hk] = hook_scores.get(hk, 0.0) + w
            hour_scores[hr] = hour_scores.get(hr, 0.0) + w
        result = {
            "mode": "empirical_top_performers", "sampleSize": n,
            "targetDurationSec": round(min(56.5, max(44.0, avg_dur)), 2),
            "targetWpm": int(round(min(185.0, max(145.0, avg_wpm)))),
            "preferredHookStyle": max(hook_scores, key=lambda k: hook_scores[k]),
            "preferredIstHour": int(max(hour_scores, key=lambda k: hour_scores[k])),
            "topEpisodes": [_summarize_top_row(r) for r in top_half],
        }

    if out_json is not None:
        out_p = Path(out_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def load_learned_defaults(defaults_path: Path | None = None) -> dict:
    """Load data/learned_defaults.json if present, else return cold-start priors cleanly."""
    target = Path(defaults_path) if defaults_path is not None else DEFAULT_DEFAULTS_PATH
    if not target.is_file():
        return {**COLD_START_PRIORS, "topEpisodes": []}
    raw = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {**COLD_START_PRIORS, "topEpisodes": []}
    merged = {**COLD_START_PRIORS, **raw}
    merged["targetDurationSec"] = round(min(56.5, max(44.0, float(merged["targetDurationSec"]))), 2)
    merged["targetWpm"] = int(round(min(185.0, max(145.0, float(merged["targetWpm"])))))
    return merged


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Cyber Jasoos SQLite Growth Telemetry Ledger")
    ap.add_argument("--db", help="Optional path to SQLite ledger DB.")
    ap.add_argument("--out", default=str(DEFAULT_DEFAULTS_PATH), help="Output JSON for learned defaults.")
    args = ap.parse_args(argv)
    summary = learn_optimal_defaults(Path(args.db) if args.db else None, Path(args.out) if args.out else None)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
