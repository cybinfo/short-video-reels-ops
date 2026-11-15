#!/usr/bin/env python3
"""End-to-end ratchet tests for the 4-pillar Cyber Jasoos self-healing pipeline."""

from __future__ import annotations

import copy, io, json, re, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import compile_story_brief  # noqa: E402
import instagram_ops  # noqa: E402
import self_heal_rules  # noqa: E402
import standardize_cast  # noqa: E402
import sync_episode_registry  # noqa: E402
import validate_episode  # noqa: E402

CASE02_BRIEF = REPO_ROOT / "episodes" / "briefs" / "case02-part1-shaadi-qr.yaml"
KABIR_RAW = REPO_ROOT / "assets" / "characters" / "case01" / "raw" / "kabir-investigating.png"


def _pct_val(rate_str: str) -> int:
    return int(re.sub(r"[^0-9+-]", "", rate_str))


class SelfHealingPipelineRatchetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.brief_p1 = compile_story_brief.load_brief(CASE02_BRIEF)
        cls.manifest_p1 = compile_story_brief.compile_brief(cls.brief_p1)

    def test_pillar1_registry_seasons_1_to_6_and_auto_cast_framing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ep_dir, aud_dir, reg_out = root / "episodes", root / "audio", root / "generated" / "episodeRegistry.ts"
            (ep_dir / "briefs").mkdir(parents=True)
            aud_dir.mkdir(parents=True)

            (ep_dir / "schema.json").write_text('{"$schema": "https://json-schema.org/draft/2020-12/schema"}', encoding="utf-8")
            (ep_dir / "briefs" / "ignored.json").write_text('{"id": "s99e99-skip", "scenes": []}', encoding="utf-8")
            (ep_dir / "s01-init").mkdir()
            (ep_dir / "s01-init" / "draft.brief.json").write_text('{"id": "s01e99-brief", "scenes": []}', encoding="utf-8")

            specs = [
                ("s06-deepfake-finale", "s06e04-voice-clone", 6, 4),
                ("s01-init", "s01e01-call-divert", 1, 1),
                ("s03-upi-traps", "s03e02-qr-overlay", 3, 2),
            ]
            for folder, ep_id, season, ep_num in specs:
                d = ep_dir / folder
                d.mkdir(parents=True, exist_ok=True)
                m = {**copy.deepcopy(self.manifest_p1), "id": ep_id, "season": season, "episode": ep_num}
                (d / f"{ep_id}.json").write_text(json.dumps(m), encoding="utf-8")

            (aud_dir / "s01e01-call-divert.captions.json").write_text('[{"word": "Raat", "startSec": 0.0, "endSec": 0.3}]', encoding="utf-8")
            found = sync_episode_registry.discover_episode_manifests(ep_dir)
            self.assertEqual([p.stem for p in found], ["s01e01-call-divert", "s03e02-qr-overlay", "s06e04-voice-clone"])

            synced = sync_episode_registry.sync_registry(episodes_dir=ep_dir, output_path=reg_out, audio_dir=aud_dir)
            self.assertEqual(len(synced), 3)
            ts_src = reg_out.read_text(encoding="utf-8")
            self.assertIn("s01e01-call-divert.captions.json", ts_src)
            self.assertIn('"s03e02-qr-overlay": [] as WordTimestamp[],', ts_src)
            self.assertIn('"s06e04-voice-clone": [] as WordTimestamp[],', ts_src)
            self.assertNotIn("schema.json", ts_src)
            self.assertNotIn("draft.brief.json", ts_src)

        scale, cx, eye_y = standardize_cast.estimate_auto_cast_spec(KABIR_RAW)
        self.assertTrue(0.90 <= scale <= 1.32, f"scale out of bounds: {scale}")
        self.assertTrue(0.35 <= cx <= 0.65, f"cx out of bounds: {cx}")
        self.assertTrue(0.24 <= eye_y <= 0.50, f"eye_y out of bounds: {eye_y}")

    def test_pillar2_compile_part1_yaml_and_part2_poll_branches(self) -> None:
        self.assertEqual(validate_episode.validate_manifest(self.manifest_p1), [])
        self.assertLessEqual(len(self.manifest_p1["securityDomain"]), 32)
        self.assertIn("@CYBERJASOOS", self.manifest_p1["scenes"][-1]["props"]["followHandleLine"])

        with tempfile.TemporaryDirectory() as td:
            p2_brief_path = Path(td) / "case02-part2-reveal.json"
            p2_brief = {
                **copy.deepcopy(self.brief_p1),
                "id": "s02e02-shaadi-qr-reveal", "episodeNumber": 2, "part": 2,
                "previousVoteResult": {"winningOption": "C", "percentage": 72},
                "pollBranches": {
                    "A": {"openingLine": "{pct_word} percent logon ne Hotel Reception Wi-Fi chuna, par asli gaddar stage ke paas chhupa tha!"},
                    "B": {"openingLine": "{pct_word} percent logon ne Lobby Smart Printer par shak kiya, magar asli khel Shagun gate par hua!"},
                    "C": {"openingLine": "{pct_word} percent Jasoos bilkul sahi the! Shagun QR Standee ke upar nakli sticker chipkaya gaya tha!"},
                },
            }
            p2_brief_path.write_text(json.dumps(p2_brief), encoding="utf-8")
            m_p2 = compile_story_brief.compile_brief(compile_story_brief.load_brief(p2_brief_path))
            self.assertEqual(validate_episode.validate_manifest(m_p2), [])
            self.assertEqual(set(m_p2["pollBranches"].keys()), {"A", "B", "C"})
            self.assertEqual(m_p2["hook"]["previousVoteResult"]["winningOption"], "C")
            self.assertIn("@CYBERJASOOS", m_p2["scenes"][-1]["props"]["followHandleLine"])

    def test_pillar3_self_heal_rate_text_dom_and_launch_copy_pack(self) -> None:
        base_rate = _pct_val(self.manifest_p1["voiceConfig"]["edgeRates"]["narrator"])
        m_fast, r_fast = self_heal_rules.compute_rate_heal_adjustment(self.manifest_p1, 62.0, 128.0)
        self.assertIsNotNone(r_fast)
        self.assertGreater(_pct_val(m_fast["voiceConfig"]["edgeRates"]["narrator"]), base_rate)
        self.assertGreater(m_fast["voiceConfig"]["kokoroSpeed"], 1.08)

        m_slow, r_slow = self_heal_rules.compute_rate_heal_adjustment(self.manifest_p1, 38.0, 205.0)
        self.assertIsNotNone(r_slow)
        self.assertLess(_pct_val(m_slow["voiceConfig"]["edgeRates"]["narrator"]), base_rate)
        self.assertLess(m_slow["voiceConfig"]["kokoroSpeed"], 1.08)

        m_noop, r_noop = self_heal_rules.compute_rate_heal_adjustment(self.manifest_p1, 51.0, 165.0)
        self.assertIsNone(r_noop)
        self.assertEqual(m_noop["voiceConfig"]["edgeRates"], self.manifest_p1["voiceConfig"]["edgeRates"])

        broken = copy.deepcopy(self.manifest_p1)
        broken["hook"]["openingLine"] = "Outdated mismatched cold open hook line!"
        broken["scriptSegments"][-1]["narration"] = re.sub(r"\.+$", ".", broken["scriptSegments"][-1]["narration"])
        for fld in ("hi", "roman"):
            broken["scriptSegments"][-1]["ttsClauses"][-1][fld] = re.sub(r"\.+$", ".", broken["scriptSegments"][-1]["ttsClauses"][-1][fld])
        pre_errs = validate_episode.validate_manifest(broken)
        self.assertTrue(any("openingLine" in e for e in pre_errs))
        self.assertTrue(any("Loop Suspension" in e for e in pre_errs))
        healed_txt, txt_acts = self_heal_rules.heal_manifest_text_guards(broken, pre_errs)
        self.assertGreaterEqual(len(txt_acts), 3)
        self.assertTrue(healed_txt["scriptSegments"][-1]["narration"].endswith("..."))
        self.assertEqual(validate_episode.validate_manifest(healed_txt), [])

        overflow = copy.deepcopy(self.manifest_p1)
        overflow["securityDomain"] = "Quishing Malicious QR Sticker Overlay Rogue Hotel Wi-Fi And Scanner Traps"
        overflow["scenes"][1]["props"]["headline"] = "YEH HEADLINE BAHUT LAMBI HAI AUR SAFE ZONE SE BAHAR NIKAL JAYEGI BILKUL!"
        overflow["scenes"][2]["props"]["badge"] = "KABIR ULTRA LONG FORENSIC INVESTIGATION BADGE OVERFLOW"
        overflow["scenes"][4]["props"]["suspects"][0]["clue"] = "Fake Captive Portal With Evil Twin Router Packet Sniffer!"
        rep = {"defects": [{"episode": overflow["id"], "sceneIndex": i, "code": "HORIZONTAL_CLIP"} for i in (1, 2, 4)]}
        dom_fixed, dom_acts = self_heal_rules.heal_dom_defects(overflow, rep)
        self.assertGreaterEqual(len(dom_acts), 4)
        self.assertLessEqual(len(dom_fixed["securityDomain"]), 32)
        self.assertLessEqual(len(dom_fixed["scenes"][1]["props"]["headline"]), 38)
        self.assertLessEqual(len(dom_fixed["scenes"][2]["props"]["badge"]), 26)
        self.assertLessEqual(len(dom_fixed["scenes"][4]["props"]["suspects"][0]["clue"]), 20)

        with tempfile.TemporaryDirectory() as td:
            pack_txt = self_heal_rules.generate_launch_copy_pack(self.manifest_p1, Path(td) / "POST_COPY.txt").read_text(encoding="utf-8")
            m_cap = re.search(r"\[2\] REEL CAPTION \+ HASHTAGS \((\d+)/2200 CHARS\)\n(.+?)\n\n\[3\]", pack_txt, re.S)
            self.assertIsNotNone(m_cap)
            assert m_cap is not None
            self.assertLess(int(m_cap.group(1)), 2200)
            self.assertLess(len(m_cap.group(2).strip()), 2200)
            opts = re.findall(r"Option \d -> (.+?) \((\d+) chars\)", pack_txt)
            self.assertEqual(len(opts), 3)
            for opt_label, opt_len in opts:
                self.assertLessEqual(len(opt_label), 22)
                self.assertEqual(len(opt_label), int(opt_len))
            for s_name in ("Hotel Reception Wi-Fi", "Lobby Smart Printer", "Shagun QR Standee"):
                self.assertIn(s_name, pack_txt)
            for stale_case01 in ("Sharma Ji", "Pappu Chachu", "Ramu Kaka", "Golu"):
                self.assertNotIn(stale_case01, pack_txt)

    def test_pillar4_growth_ledger_learning_and_brief_inheritance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db_p, learned_p = root / "growth.sqlite3", root / "learned_defaults.json"
            runs = [
                ("s01e01-low-a", 55.5, {"reach": 10000, "views": 11000, "saved": 90, "shares": 60}, 40, 13, "mid_crime_shock"),
                ("s01e02-low-b", 56.0, {"reach": 10000, "views": 11500, "saved": 110, "shares": 80}, 50, 14, "mid_crime_shock"),
                ("s02e01-top-a", 49.0, {"reach": 10000, "views": 28000, "saved": 680, "shares": 920}, 540, 20, "contradiction_shock"),
                ("s02e02-top-b", 49.5, {"reach": 10000, "views": 31000, "saved": 740, "shares": 980}, 610, 20, "contradiction_shock"),
            ]
            for idx, (ep_id, dur, met, votes, hr, hk) in enumerate(runs, 1):
                ep_file = root / f"{ep_id}.json"
                ep_obj = {**copy.deepcopy(self.manifest_p1), "id": ep_id, "durationSeconds": dur}
                ep_file.write_text(json.dumps(ep_obj), encoding="utf-8")
                with redirect_stdout(io.StringIO()):
                    rc = instagram_ops.main([
                        "record-metrics", "--episode", str(ep_file), "--metrics-json", json.dumps(met),
                        "--poll-votes", str(votes), "--posted-hour-ist", str(hr), "--hook-style", hk, "--db", str(db_p),
                    ])
                self.assertEqual(rc, 0)
                if idx == 2:
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(instagram_ops.main(["learn", "--db", str(db_p), "--out", str(learned_p)]), 0)
                    cold = json.loads(learned_p.read_text(encoding="utf-8"))
                    self.assertEqual(cold["mode"], "cold_start_prior")
                    self.assertEqual(cold["sampleSize"], 2)

            with redirect_stdout(io.StringIO()):
                self.assertEqual(instagram_ops.main(["learn", "--db", str(db_p), "--out", str(learned_p)]), 0)
            emp = json.loads(learned_p.read_text(encoding="utf-8"))
            self.assertEqual(emp["mode"], "empirical_top_performers")
            self.assertEqual(emp["sampleSize"], 4)
            self.assertTrue(49.0 <= emp["targetDurationSec"] <= 49.5)
            self.assertGreater(emp["targetWpm"], 180)
            self.assertEqual(emp["preferredHookStyle"], "contradiction_shock")
            self.assertEqual(emp["preferredIstHour"], 20)

            inherited = compile_story_brief.compile_brief(self.brief_p1, defaults_path=learned_p)
            self.assertEqual(inherited["durationSeconds"], emp["targetDurationSec"])
            self.assertEqual(inherited["voiceConfig"]["targetWpm"], emp["targetWpm"])
            self.assertEqual(inherited["hook"]["hookPattern"], "contradiction_shock")
            self.assertEqual(validate_episode.validate_manifest(inherited), [])


if __name__ == "__main__":
    unittest.main()
