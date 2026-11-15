#!/usr/bin/env python3
"""Unit tests for Phase 2 (@cyberjasoos) Instagram Graph API, Poll Tally, Replies & Brand Kit."""

import datetime as dt
import io
import json
import struct
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ig_graph_client  # noqa: E402
import instagram_ops  # noqa: E402
import validate_episode  # noqa: E402


def _png_dims(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", f"Not a valid PNG: {path}"
    w, h = struct.unpack(">II", raw[16:24])
    return int(w), int(h)


class _FakeResp:
    def __init__(self, payload: dict) -> None:
        self._bytes = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._bytes

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class InstagramOpsPhase2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.e01 = json.loads((REPO_ROOT / "episodes/s01-asset-classification/s01e01-forgotten-bucket.json").read_text())
        self.e02 = json.loads((REPO_ROOT / "episodes/s01-asset-classification/s01e02-crown-jewels.json").read_text())

    def test_brand_kit_png_dimensions_and_playbook_presence(self) -> None:
        self.assertEqual(_png_dims(REPO_ROOT / "assets/brand/thecyberjasoos-dp-1080.png"), (1080, 1080))
        self.assertEqual(_png_dims(REPO_ROOT / "engine/public/brand/kabir-avatar.png"), (512, 512))
        for hl in ("cases", "polls", "kavach", "1930"):
            self.assertEqual(_png_dims(REPO_ROOT / f"assets/brand/highlight-{hl}.png"), (1080, 1920))
        self.assertEqual(_png_dims(REPO_ROOT / "renders/s01e01-reel-cover.png"), (1080, 1920))
        self.assertEqual(_png_dims(REPO_ROOT / "renders/s01e02-reel-cover.png"), (1080, 1920))
        playbook = (REPO_ROOT / "docs/instagram-launch-and-ops-playbook.md").read_text(encoding="utf-8")
        self.assertIn("realcyberjasoos@gmail.com", playbook)
        self.assertTrue("@cyberjasoos" in playbook or "@thecyberjasoos" in playbook)
        self.assertIn("@realcyberjasoos", playbook)

    def test_poll_vote_classification_deduplication_and_part2_injection(self) -> None:
        aliases = instagram_ops.extract_option_aliases(self.e01)
        self.assertEqual(instagram_ops.classify_poll_vote("C", aliases), "C")
        self.assertEqual(instagram_ops.classify_poll_vote("Pappu Chachu hi chor hai!", aliases), "C")
        self.assertEqual(instagram_ops.classify_poll_vote("Ramu Kaka pakka", aliases), "B")
        self.assertEqual(instagram_ops.classify_poll_vote("Meri taraf se Golu", aliases), "A")
        self.assertIsNone(instagram_ops.classify_poll_vote("A ya C mein confusion hai", aliases))
        self.assertIsNone(instagram_ops.classify_poll_vote("A great mystery episode bhai!", aliases))

        comments = [
            {"id": "0", "username": "cyberjasoos", "text": "C"},
            {"id": "1", "username": "thecyberjasoos", "text": "A, B, ya C comment kijiye!"},
            {"id": "2", "username": "realcyberjasoos", "text": "C"},
            {"id": "3", "username": "spammer_99", "text": "C", "timestamp": "2026-11-15T14:10:00Z"},
            {"id": "4", "username": "spammer_99", "text": "C pakka!", "timestamp": "2026-11-15T14:11:00Z"},
            {"id": "5", "username": "spammer_99", "text": "A", "timestamp": "2026-11-15T14:12:00Z"},
            {"id": "6", "username": "viewer_2", "text": "Pappu Chachu"},
            {"id": "7", "username": "viewer_3", "text": "Option B Ramu Kaka"},
            {"id": "8", "username": "viewer_4", "text": "Golu (A)"},
            {"id": "9", "username": "viewer_5", "text": "Bahut shaandaar story!"},
        ]
        tally = instagram_ops.tally_poll_comments(comments, self.e01)
        self.assertEqual(tally["counts"], {"A": 1, "B": 1, "C": 2})
        self.assertEqual(tally["totalVotes"], 4)
        self.assertEqual(tally["winner"], "C")
        self.assertEqual(tally["winnerPct"], 50)
        self.assertEqual(tally["unclassifiedCount"], 1)

        with tempfile.TemporaryDirectory() as td:
            td_p = Path(td)
            c_file = td_p / "comments.json"
            p2_tmp = td_p / "s01e02.json"
            c_file.write_text(json.dumps(comments), encoding="utf-8")
            p2_tmp.write_text(json.dumps(self.e02), encoding="utf-8")
            rc = instagram_ops.main([
                "poll-tally", "--comments-file", str(c_file),
                "--part1", str(REPO_ROOT / "episodes/s01-asset-classification/s01e01-forgotten-bucket.json"),
                "--apply-to", str(p2_tmp),
            ])
            self.assertEqual(rc, 0)
            updated_p2 = json.loads(p2_tmp.read_text(encoding="utf-8"))
            self.assertEqual(updated_p2["hook"]["previousVoteResult"]["winningOption"], "C")
            self.assertEqual(updated_p2["hook"]["previousVoteResult"]["percentage"], 50)
            self.assertIn("Pachaas percent", updated_p2["hook"]["openingLine"])
            self.assertEqual(validate_episode.validate_manifest(updated_p2), [])

    def test_publish_reel_blocks_preview_tts_and_passes_dry_run_on_own_voice(self) -> None:
        mp4 = REPO_ROOT / "renders/s01e01-forgotten-bucket.mp4"
        with tempfile.TemporaryDirectory() as td:
            prev_ep = Path(td) / "prev_e01.json"
            m_prev = json.loads(json.dumps(self.e01))
            m_prev["voiceConfig"]["mode"] = "edge_neural"
            m_prev["voiceConfig"]["engineLicense"] = "EDGE_READ_ALOUD_PREVIEW"
            prev_ep.write_text(json.dumps(m_prev), encoding="utf-8")
            rc_blocked = instagram_ops.main(["publish-reel", "--episode", str(prev_ep), "--video", str(mp4), "--dry-run"])
            self.assertEqual(rc_blocked, 2)

            pub_ep = Path(td) / "pub_e01.json"
            m = json.loads(json.dumps(self.e01))
            m["voiceConfig"]["mode"] = "recorded"
            m["voiceConfig"]["engineLicense"] = "OWN_VOICE"
            pub_ep.write_text(json.dumps(m), encoding="utf-8")
            rc_ok = instagram_ops.main(["publish-reel", "--episode", str(pub_ep), "--video", str(mp4), "--dry-run"])
            self.assertEqual(rc_ok, 0)

    def test_graph_client_rate_guard_insights_fallback_resumable_upload_and_token_redaction(self) -> None:
        calls: list[tuple[str, str]] = []
        clock = [1000.0]
        sleeps: list[float] = []

        def fake_urlopen(req, timeout=30.0):
            url = req.full_url
            calls.append((req.get_method(), url))
            if "reels_skip_rate" in url:
                raise urllib.error.HTTPError(url, 400, "Bad Request", {}, io.BytesIO(b'{"error":"metric_unavailable_secret_tok"}'))
            if "/insights" in url:
                return _FakeResp({"data": [{"name": "views", "values": [{"value": 12000}]}, {"name": "reach", "values": [{"value": 10000}]}, {"name": "saved", "values": [{"value": 450}]}, {"name": "shares", "values": [{"value": 620}]}]})
            if url.endswith("/1789/media"):
                return _FakeResp({"id": "cnt_1", "uri": "https://rupload.facebook.com/ig-api-upload/v22.0/cnt_1"})
            if "rupload.facebook.com" in url:
                return _FakeResp({"success": True})
            if "/cnt_1?" in url:
                return _FakeResp({"status_code": "FINISHED"})
            if "/media_publish" in url:
                return _FakeResp({"id": "media_999"})
            return _FakeResp({"id": "reply_1"})

        client = ig_graph_client.InstagramGraphClient(
            access_token="secret_tok", ig_user_id="1789", urlopen_fn=fake_urlopen,
            sleep_fn=lambda s: (sleeps.append(round(s, 2)), clock.__setitem__(0, clock[0] + s)),
            time_fn=lambda: clock[0], max_calls_per_hour=10, min_reply_interval_sec=2.2,
        )
        ins = client.get_media_insights("m_1")
        self.assertEqual(ins["save_rate_pct"], 4.5)
        self.assertEqual(ins["share_rate_pct"], 6.2)

        with tempfile.NamedTemporaryFile(suffix=".mp4") as vf:
            vf.write(b"\x00\x00\x00\x18ftypmp42")
            vf.flush()
            pub = client.publish_reel_resumable(Path(vf.name), caption="Case #01")
            self.assertEqual(pub["media_id"], "media_999")

        client.reply_to_comment("c_1", "Saboot dekhiye!")
        clock[0] += 0.5
        client.reply_to_comment("c_2", "Kya lagta hai?")
        self.assertIn(1.7, sleeps)

        with self.assertRaises(RuntimeError):
            for _ in range(10):
                client.reply_to_comment("c_3", "Extra")

    def test_socratic_replies_and_ist_best_time_window(self) -> None:
        r1 = instagram_ops.draft_socratic_reply({"username": "rahul_k"}, "C", self.e01, idx=0)
        self.assertTrue(r1.startswith("@rahul_k, "))
        self.assertLessEqual(len(r1.split()), 22)
        slots = instagram_ops.recommend_ist_upload_slots(dt.datetime(2026, 11, 15, 5, 0, tzinfo=dt.timezone.utc))
        self.assertEqual(slots["primarySlot"]["targetIst"], "19:45 IST")
        self.assertEqual(slots["secondarySlot"]["targetIst"], "12:30 IST")


if __name__ == "__main__":
    unittest.main()
