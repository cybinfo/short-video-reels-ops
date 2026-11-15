#!/usr/bin/env python3
"""Unit tests for episode validation, hook scoring, and voice/caption tooling."""

import json, os, shutil, struct, subprocess, sys, tempfile, unittest, wave
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import apply_poll_result, competitor_hooks, export_teleprompter, prepare_voice, render_instagram_ui_mockup, validate_episode  # noqa: E402


def make_valid_manifest() -> dict:
    return {
        "id": "s01e01-shadow-jenkins", "season": 1, "episode": 1, "totalEpisodesInSeason": 6,
        "seasonTitle": "BreachZero: First 72 Hours", "episodeTitle": "The Untracked Build Server",
        "companyName": "vaultgrid.io", "securityDomain": "Asset Inventory & Tiering",
        "realBreachParallel": {
            "incident": "Equifax Unpatched Build Portal", "year": 2017,
            "impact": "147M records exposed via untracked web server",
            "lesson": "You cannot patch or monitor an asset missing from your inventory.",
        },
        "voiceConfig": {"mode": "recorded", "engineLicense": "OWN_VOICE", "targetWpm": 165},
        "durationSeconds": 48, "fps": 30,
        "hook": {
            "openingLine": "At 02:14 AM, an untracked Jenkins build server leaked forty thousand live production keys while every perimeter firewall dashboard stayed completely green.",
            "hookPattern": "mid_breach_timestamp",
        },
        "scriptSegments": [
            {"id": "seg-hook", "startSec": 0, "endSec": 7.5, "phase": "hook",
             "narration": "At 02:14 AM, an untracked Jenkins build server leaked forty thousand live production keys while every perimeter firewall dashboard stayed completely green.",
             "highlightKeywords": ["02:14", "Jenkins", "forty thousand"]},
            {"id": "seg-escalation", "startSec": 7.5, "endSec": 19.0, "phase": "escalation",
             "narration": "A temporary contractor spun up that cloud instance six months ago for weekend load tests and left root admin tokens sitting inside world-readable environment files.",
             "highlightKeywords": ["contractor", "admin tokens"]},
            {"id": "seg-framework", "startSec": 19.0, "endSec": 31.5, "phase": "framework",
             "narration": "High-reliability security teams classify every workload into Tier Zero crown jewel vaults, Tier One customer APIs, and isolated build runners with short-lived ephemeral credentials.",
             "highlightKeywords": ["crown jewel", "Tier Zero"]},
            {"id": "seg-payoff", "startSec": 31.5, "endSec": 40.0, "phase": "micro_payoff",
             "narration": "Equifax learned that lesson the brutal way when one forgotten unpatched portal exposed 147 million consumer records across critical databases overnight.",
             "highlightKeywords": ["Equifax", "147 million"]},
            {"id": "seg-vote", "startSec": 40.0, "endSec": 48.0, "phase": "cliffhanger_vote",
             "narration": "Right now active ransom beacons are sweeping our primary database subnet every ten seconds. Do you execute option A, B, or C? Drop your vote below before episode two.",
             "highlightKeywords": ["ransom beacons", "database subnet"]},
        ],
        "scenes": [
            {"id": "sc-1", "startSec": 0, "endSec": 12, "kind": "breach_terminal", "props": {}},
            {"id": "sc-2", "startSec": 12, "endSec": 26, "kind": "asset_tier_matrix", "props": {}},
            {"id": "sc-3", "startSec": 26, "endSec": 39, "kind": "payoff_proof_card", "props": {}},
            {"id": "sc-4", "startSec": 39, "endSec": 48, "kind": "vote_cliffhanger", "props": {
                "crisisPrompt": "Ransomware beacon live on DB subnet. Your move?", "countdownLabel": "00:10",
                "options": [
                    {"key": "A", "label": "Kill Jenkins IAM", "detail": "Revoke role tokens now"},
                    {"key": "B", "label": "Isolate DB Subnet", "detail": "Sever prod traffic"},
                    {"key": "C", "label": "Sinkhole C2 IP", "detail": "Watch attacker pivot"},
                ],
                "ctaLine": "Comment A, B, or C", "loopBridgeText": "Because at",
            }},
        ],
        "postCopy": {
            "instagramCaption": "Shadow IT caused the breach before sunrise.",
            "youtubeShortsTitle": "02:14 AM Breach: The Untracked Jenkins Box #Shorts",
            "linkedinPost": "Asset inventory beats shiny tools when Tier 0 creds sit on staging.",
            "pinnedCommentVote": "You have 60 seconds as CISO: Pick A (Revoke IAM), B (Isolate DB), or C (Sinkhole C2)!",
            "hashtags": ["#cybersecurity", "#infosec", "#ciso", "#cloudsecurity", "#incidentresponse"],
        },
    }


class FrameworkTestSuite(unittest.TestCase):
    def setUp(self) -> None:
        self._prev_whisper_env = os.environ.get("BREACHZERO_DISABLE_WHISPER")
        os.environ["BREACHZERO_DISABLE_WHISPER"] = "1"
        self.tmp_dir = Path(os.environ.get("TMPDIR", "/tmp")) / f"breachzero_ut_{os.getpid()}_{self._testMethodName}"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        os.environ.pop("BREACHZERO_DISABLE_WHISPER", None) if self._prev_whisper_env is None else os.environ.__setitem__("BREACHZERO_DISABLE_WHISPER", self._prev_whisper_env)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_valid_manifest_passes_with_zero_errors(self) -> None:
        self.assertEqual(validate_episode.validate_manifest(make_valid_manifest()), [])

    def test_adversarial_cc_by_nc_voice_license_blocked(self) -> None:
        manifest = make_valid_manifest()
        manifest["voiceConfig"]["engineLicense"] = "CC-BY-NC"
        errors = validate_episode.validate_manifest(manifest)
        self.assertTrue(any("Commercial Voice License Guard" in e for e in errors), errors)

    def test_generic_filler_hook_blocked(self) -> None:
        manifest = make_valid_manifest()
        manifest["hook"]["openingLine"] = "In this video we will learn asset classification"
        errors = validate_episode.validate_manifest(manifest)
        self.assertTrue(any("Anti-Swipe Hook Guard" in e for e in errors), errors)

    def test_missing_vote_cliffhanger_and_scene_gap_caught(self) -> None:
        m_no_vote = make_valid_manifest()
        m_no_vote["scenes"][-1]["kind"] = "breach_terminal"
        self.assertTrue(any("vote_cliffhanger" in e for e in validate_episode.validate_manifest(m_no_vote)))

        m_gap = make_valid_manifest()
        m_gap["scenes"][1]["startSec"] = 14.0
        self.assertTrue(any("gap" in e.lower() for e in validate_episode.validate_manifest(m_gap)))

    def test_out_of_bounds_speaking_wpm_caught(self) -> None:
        m_slow = make_valid_manifest()
        for seg in m_slow["scriptSegments"]:
            seg["narration"] = "Too few words spoken slowly here."
        self.assertTrue(any("WPM" in e for e in validate_episode.validate_manifest(m_slow)))

        m_fast = make_valid_manifest()
        burst = " ".join(["rapid"] * 45)
        for seg in m_fast["scriptSegments"]:
            seg["narration"] = f"Crisis alert {burst}"
        self.assertTrue(any("WPM" in e for e in validate_episode.validate_manifest(m_fast)))

    def test_competitor_hooks_scores_crisis_vs_textbook(self) -> None:
        crisis = "At 02:14 AM, an untracked Jenkins box leaked 40,000 keys while every SOC alert stayed green."
        textbook = "In this video we will learn asset classification and why it matters."
        self.assertGreaterEqual(competitor_hooks.score_hook(crisis)["score"], 80)
        self.assertLessEqual(competitor_hooks.score_hook(textbook)["score"], 40)

    def test_deterministic_word_timestamps_bounds_and_highlights(self) -> None:
        segments = make_valid_manifest()["scriptSegments"]
        words = prepare_voice.build_deterministic_word_timestamps(segments)
        self.assertGreater(len(words), 80)
        idx = 0
        for seg in segments:
            seg_tokens = seg["narration"].split()
            seg_slice = words[idx : idx + len(seg_tokens)]
            self.assertEqual(len(seg_slice), len(seg_tokens))
            for item in seg_slice:
                self.assertGreaterEqual(item["startSec"], seg["startSec"])
                self.assertLessEqual(item["endSec"], seg["endSec"])
                self.assertLess(item["startSec"], item["endSec"])
            idx += len(seg_tokens)
        emph_words = {w["word"].strip(".,!?") for w in words if w["emphasis"]}
        self.assertTrue({"Jenkins", "crown", "jewel"}.issubset(emph_words))

    def test_cli_validation_and_silent_wav_synthesis(self) -> None:
        ep_file = self.tmp_dir / "s01e01-shadow-jenkins.json"
        ep_file.write_text(json.dumps(make_valid_manifest()), encoding="utf-8")
        self.assertEqual(validate_episode.main([str(ep_file)]), 0)
        wav_path = self.tmp_dir / "test.wav"
        prepare_voice.synthesize_silent_wav(wav_path, 1.5)
        with wave.open(str(wav_path), "rb") as wf:
            self.assertEqual((wf.getnchannels(), wf.getsampwidth(), wf.getframerate()), (1, 2, 44100))

    @unittest.skipUnless(Path("/usr/bin/say").is_file() and Path("/usr/bin/afconvert").is_file(), "macOS audio tools required")
    def test_recorded_m4a_voice_ingest_end_to_end_and_duration_conform(self) -> None:
        ep_path = REPO_ROOT / "episodes" / "s01-asset-classification" / "s01e01-forgotten-bucket.json"
        ep_dur = float(json.loads(ep_path.read_text(encoding="utf-8"))["durationSeconds"])
        expected_frames = int(round(ep_dur * 44100))
        with tempfile.TemporaryDirectory() as tmp:
            tp = Path(tmp)
            aiff, m4a_short, out_short = tp / "voice.aiff", tp / "short.m4a", tp / "out_short"
            subprocess.run(["/usr/bin/say", "-o", str(aiff), "At two fourteen AM four million records leaked."], check=True)
            subprocess.run(["/usr/bin/afconvert", "-f", "m4af", "-d", "aac", str(aiff), str(m4a_short)], check=True)
            rc = prepare_voice.main(["--episode", str(ep_path), "--mode", "recorded", "--input", str(m4a_short), "--output-dir", str(out_short)])
            self.assertEqual(rc, 0)
            with wave.open(str(out_short / "s01e01-forgotten-bucket.wav"), "rb") as wf:
                self.assertEqual((wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()), (1, 2, 44100, expected_frames))
            caps = json.loads((out_short / "s01e01-forgotten-bucket.captions.json").read_text(encoding="utf-8"))
            self.assertGreater(len(caps), 100)
            self.assertTrue(all(isinstance(c["word"], str) and c["startSec"] < c["endSec"] <= ep_dur for c in caps))

            stereo_src, m4a_long, out_long = tp / "stereo58.wav", tp / "long_stereo.m4a", tp / "out_long"
            with wave.open(str(stereo_src), "wb") as swf:
                swf.setparams((2, 2, 44100, 0, "NONE", "not compressed"))
                swf.writeframes(b"\x20\x01\xe0\xfe" * (58 * 44100))
            subprocess.run(["/usr/bin/afconvert", "-f", "m4af", "-d", "aac", str(stereo_src), str(m4a_long)], check=True)
            self.assertEqual(prepare_voice.main(["--episode", str(ep_path), "--mode", "recorded", "--input", str(m4a_long), "--output-dir", str(out_long)]), 0)
            with wave.open(str(out_long / "s01e01-forgotten-bucket.wav"), "rb") as wf2:
                self.assertEqual((wf2.getnchannels(), wf2.getsampwidth(), wf2.getframerate(), wf2.getnframes()), (1, 2, 44100, expected_frames))

            corrupt = tp / "bad.m4a"
            corrupt.write_bytes(b"not-an-audio-file")
            self.assertEqual(prepare_voice.main(["--episode", str(ep_path), "--mode", "recorded", "--input", str(corrupt), "--output-dir", str(tp / "bad_out")]), 1)

    def test_comment_callout_missing_previous_vote_and_spotlight_guards(self) -> None:
        m = make_valid_manifest()
        m["hook"]["hookPattern"] = "comment_callout"
        errs = validate_episode.validate_manifest(m)
        self.assertTrue(any("previousVoteResult" in e for e in errs), errs)

        m["hook"]["previousVoteResult"] = {"winningOption": "D", "percentage": 100}
        m["scenes"][0] = {"id": "sc-1", "startSec": 0, "endSec": 12, "kind": "comment_spotlight",
                          "props": {"optionPicked": "Z", "verdictTone": "neutral"}}
        errs2 = validate_episode.validate_manifest(m)
        for field in ("winningOption", "percentage", "optionPicked", "verdictTone"):
            self.assertTrue(any(field in e for e in errs2), errs2)

    def test_season_continuity_across_all_live_episodes_and_negative_case(self) -> None:
        ep_files = validate_episode._collect_targets([str(REPO_ROOT / "episodes")])
        self.assertGreaterEqual(len(ep_files), 5)
        manifests = [json.loads(f.read_text(encoding="utf-8")) for f in ep_files]
        for m in manifests:
            self.assertEqual(validate_episode.validate_manifest(m), [], m["id"])
        self.assertEqual(validate_episode.validate_season_continuity(manifests), [])

        ep1, ep2 = make_valid_manifest(), make_valid_manifest()
        ep1["scenes"][-1]["props"]["options"] = [{"key": "A", "label": "A", "detail": "d"}, {"key": "B", "label": "B", "detail": "d"}]
        ep2["id"], ep2["episode"] = "s01e02-broken-followup", 2
        ep2["scenes"][0] = {"id": "sc-1", "startSec": 0, "endSec": 12, "kind": "comment_spotlight",
                            "props": {"optionPicked": "C", "verdictTone": "warning"}}
        cont_errs = validate_episode.validate_season_continuity([ep2, ep1])
        self.assertTrue(any("Continuity" in e and "'C'" in e for e in cont_errs), cont_errs)

    def test_export_teleprompter_formatting_and_live_pack(self) -> None:
        seg = {"startSec": 0, "endSec": 4, "phase": "hook", "highlightKeywords": ["2:14 AM", "4.2 million", "$200K firewall", "silent"],
               "narration": "2:14 AM. 4.2 million records leak while their $200K firewall stays silent."}
        line = export_teleprompter.format_segment_line(seg)
        for expected in ("[00.0s – 04.0s | HOOK]", "**2:14 AM**. // **4.2 MILLION**", "**$200K FIREWALL** stays **SILENT**."):
            self.assertIn(expected, line)
        out_md = self.tmp_dir / "teleprompter.md"
        self.assertEqual(export_teleprompter.main(["--output", str(out_md)]), 0)
        text = out_md.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 220)
        for token in ("S01E01", "S01E02", "S01E03", "S01E04", "S02E01", "6 inches off-axis", "160 WPM", "<250ms", "--mode recorded"):
            self.assertIn(token, text)

    def test_asset_tier_matrix_active_tier_mismatch_caught(self) -> None:
        m = make_valid_manifest()
        tiers = [
            {"rank": 0, "name": "Crown Jewels", "tag": "TIER 0", "examples": "KMS", "blastRadius": "Fatal", "colorTone": "crimson"},
            {"rank": 1, "name": "Customer Core", "tag": "TIER 1", "examples": "API", "blastRadius": "High", "colorTone": "amber"},
        ]
        for valid_active in ("Crown Jewels", "tier 0", "TIER 1"):
            m["scenes"][1]["props"] = {"title": "Asset Tiers", "activeTier": valid_active, "tiers": tiers}
            self.assertEqual(validate_episode.validate_manifest(m), [])
        m["scenes"][1]["props"]["activeTier"] = "Unclassified Bucket"
        self.assertEqual(
            validate_episode.validate_manifest(m),
            ["scenes[1] asset_tier_matrix.activeTier 'Unclassified Bucket' matches no tier name, tag, or 'Tier <rank>'."],
        )

    @unittest.skipUnless(Path("/usr/bin/say").is_file() and Path("/usr/bin/afconvert").is_file(), "macOS audio tools required")
    def test_draft_voice_bidirectional_pacing_calibration(self) -> None:
        ep_json, out_dir = self.tmp_dir / "s99e01-pacing.json", self.tmp_dir / "draft_out"
        manifest = {
            "id": "s99e01-pacing", "durationSeconds": 16.7,
            "voiceConfig": {"mode": "draft_say", "engineLicense": "MACOS_DRAFT", "targetWpm": 165},
            "scriptSegments": [
                {"id": "s1", "startSec": 0.0, "endSec": 5.5, "phase": "hook", "highlightKeywords": ["Jenkins"],
                 "narration": "At two fourteen AM, an untracked Jenkins build server leaked forty thousand live production keys."},
                {"id": "s2", "startSec": 5.5, "endSec": 16.7, "phase": "escalation", "highlightKeywords": ["root"],
                 "narration": "Six months ago, a temporary contractor launched that cloud instance for weekend load tests and left root admin tokens sitting inside world-readable environment files across staging."},
            ],
        }
        ep_json.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(prepare_voice.main(["--episode", str(ep_json), "--mode", "draft", "--output-dir", str(out_dir)]), 0)
        caps = json.loads((out_dir / "s99e01-pacing.captions.json").read_text(encoding="utf-8"))
        seg1_end = max(c["endSec"] for c in caps if c["startSec"] < 5.5)
        seg2_end = max(c["endSec"] for c in caps if c["startSec"] >= 5.5)
        self.assertLess(5.5 - seg1_end, 0.65)
        self.assertLess(16.7 - seg2_end, 0.65)
        with wave.open(str(out_dir / "s99e01-pacing.wav"), "rb") as wf:
            self.assertEqual((wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()), (1, 2, 44100, int(round(16.7 * 44100))))

    def test_mlx_whisper_venv_alignment_and_disable_env_guard(self) -> None:
        fake_mlx, wav_path = self.tmp_dir / "mlx_whisper", self.tmp_dir / "sample.wav"
        prepare_voice.synthesize_silent_wav(wav_path, 2.0)
        fake_mlx.write_text(
            f"#!{sys.executable}\nimport json, pathlib, sys\nassert '--model' in sys.argv and 'mlx-community/whisper-base-mlx' in sys.argv\n"
            "out = pathlib.Path(sys.argv[sys.argv.index('--output-dir') + 1]) / (pathlib.Path(sys.argv[1]).stem + '.json')\n"
            "out.write_text(json.dumps({'segments': [{'words': [{'word': ' Jenkins', 'start': 0.1, 'end': 0.6}, {'word': ' leaked', 'start': 0.6, 'end': 2.5}]}]}))\n",
            encoding="utf-8",
        )
        fake_mlx.chmod(0o755)
        orig_bin, orig_env = prepare_voice.MLX_WHISPER_BIN, os.environ.get("BREACHZERO_DISABLE_WHISPER")
        try:
            prepare_voice.MLX_WHISPER_BIN, os.environ["BREACHZERO_DISABLE_WHISPER"] = fake_mlx, "1"
            self.assertIsNone(prepare_voice._try_whisper_captions(wav_path, [{"highlightKeywords": ["Jenkins"]}], max_sec=2.0))
            os.environ.pop("BREACHZERO_DISABLE_WHISPER", None)
            caps = prepare_voice._try_whisper_captions(wav_path, [{"highlightKeywords": ["Jenkins"]}], max_sec=2.0)
            self.assertEqual(caps, [{"word": "Jenkins", "startSec": 0.1, "endSec": 0.6, "emphasis": True},
                                    {"word": "leaked", "startSec": 0.6, "endSec": 2.0, "emphasis": False}])
        finally:
            prepare_voice.MLX_WHISPER_BIN = orig_bin
            os.environ.pop("BREACHZERO_DISABLE_WHISPER", None) if orig_env is None else os.environ.__setitem__("BREACHZERO_DISABLE_WHISPER", orig_env)

    def test_kokoro_neural_mode_and_dual_speaker_clause_locked_timestamps(self) -> None:
        m = make_valid_manifest()
        m["voiceConfig"] = {
            "mode": "kokoro_neural",
            "engineLicense": "APACHE_2_0",
            "kokoroVoice": "hf_sweet",
            "kokoroVoices": {"jyoti": "hf_sweet", "rajat": "hm_omega"},
            "kokoroLang": "hi",
            "kokoroSpeed": 1.08,
            "targetWpm": 165,
        }
        self.assertEqual(validate_episode.validate_manifest(m), [])

        seg = {
            "id": "seg-duo",
            "startSec": 1.0,
            "endSec": 6.0,
            "phase": "framework",
            "speaker": "rajat",
            "narration": "Rule One clear hai: bhoola bucket sab le dooba!",
            "ttsClauses": [
                {"speaker": "rajat", "roman": "Rule One clear hai:", "hi": "रूल वन क्लियर है:"},
                {"speaker": "jyoti", "roman": "bhoola bucket sab le dooba!", "hi": "भूला बकिट सब ले डूबा!"},
            ],
            "highlightKeywords": ["Rule One", "sab le dooba!"],
        }
        clauses = prepare_voice.extract_segment_clauses(seg)
        self.assertEqual([c["speaker"] for c in clauses], ["rajat", "jyoti"])

        caps = prepare_voice.build_clause_locked_word_timestamps([seg], [[(1.05, 2.60), (2.78, 5.82)]])
        self.assertEqual(len(caps), 9)
        c1_caps, c2_caps = caps[:4], caps[4:]
        self.assertTrue(all(1.05 <= w["startSec"] < w["endSec"] <= 2.60 and w["speaker"] == "rajat" for w in c1_caps))
        self.assertTrue(all(2.78 <= w["startSec"] < w["endSec"] <= 5.82 and w["speaker"] == "jyoti" for w in c2_caps))
        emph_words = [w["word"] for w in caps if w["emphasis"]]
        self.assertEqual(emph_words, ["Rule", "One", "sab", "le", "dooba!"])

        bad_seg = dict(seg, ttsClauses=[{"roman": "Wrong words", "hi": "गलत"}])
        with self.assertRaises(ValueError):
            prepare_voice.extract_segment_clauses(bad_seg)

        s01e01_raw = (REPO_ROOT / "episodes" / "s01-asset-classification" / "s01e01-forgotten-bucket.json").read_text(encoding="utf-8")
        self.assertNotIn("riya", s01e01_raw.lower())
        self.assertNotIn("jyoti", s01e01_raw.lower())
        self.assertNotIn("rajat", s01e01_raw.lower())
        live_caps_path = REPO_ROOT / "engine" / "public" / "audio" / "s01e01-forgotten-bucket.captions.json"
        if live_caps_path.is_file():
            live_caps = json.loads(live_caps_path.read_text(encoding="utf-8"))
            self.assertEqual({w.get("speaker") for w in live_caps}, {"narrator", "sharma"})

    def test_bright_detective_edge_neural_and_one_to_one_scene_sync(self) -> None:
        m = make_valid_manifest()
        m["visualTheme"] = "bright_detective"
        m["voiceConfig"] = {
            "mode": "edge_neural",
            "engineLicense": "EDGE_READ_ALOUD_PREVIEW",
            "edgeVoices": {"jyoti": "hi-IN-SwaraNeural", "rajat": "hi-IN-MadhurNeural"},
            "edgeRates": {"jyoti": "+10%", "rajat": "+12%"},
            "edgePitches": {"jyoti": "+4Hz", "rajat": "-2Hz"},
            "targetWpm": 165,
        }
        m["scenes"] = [
            {"id": "d-1", "startSec": 0, "endSec": 7.5, "kind": "detective_crime_hook", "props": {}},
            {"id": "d-2", "startSec": 7.5, "endSec": 19.0, "kind": "detective_wifi_clue", "props": {}},
            {"id": "d-3", "startSec": 19.0, "endSec": 31.5, "kind": "detective_evidence_twist", "props": {"variant": "cctv_backdoor"}},
            {"id": "d-4", "startSec": 31.5, "endSec": 40.0, "kind": "detective_evidence_twist", "props": {"variant": "contact_match"}},
            {"id": "d-5", "startSec": 40.0, "endSec": 48.0, "kind": "detective_suspect_board", "props": {
                "prompt": "ASLI CHOR KAUN HAI?",
                "suspects": [
                    {"key": "A", "name": "CA Vikram", "role": "CA", "clue": "KYC"},
                    {"key": "B", "name": "Tech Ravi", "role": "CCTV", "clue": "1234"},
                    {"key": "C", "name": "Partner Kabir", "role": "Partner", "clue": "10 PM"},
                ],
            }},
        ]
        self.assertEqual(validate_episode.validate_manifest(m), [])

        prepare_voice.sync_manifest_timings(m, [8.12, 18.44, 31.90, 40.55, 50.20], 50.20)
        self.assertEqual(m["durationSeconds"], 50.2)
        for seg, sc in zip(m["scriptSegments"], m["scenes"]):
            self.assertEqual(sc["startSec"], seg["startSec"])
            self.assertEqual(sc["endSec"], seg["endSec"])

        m_bad_theme = dict(m, visualTheme="neon_invalid")
        self.assertTrue(any("visualTheme" in e for e in validate_episode.validate_manifest(m_bad_theme)))

        ep2 = make_valid_manifest()
        ep2["id"], ep2["episode"] = "s01e02-followup", 2
        ep2["scenes"][0] = {"id": "sc-1", "startSec": 0, "endSec": 12, "kind": "comment_spotlight",
                            "props": {"optionPicked": "B", "verdictTone": "warning"}}
        self.assertEqual(validate_episode.validate_season_continuity([m, ep2]), [])

        self.assertIn("\u027e", prepare_voice._KOKORO_WORKER_CODE)
        self.assertNotIn("\u027d", prepare_voice._KOKORO_WORKER_CODE)
        self.assertIn("\\u0600-\\u06FF", prepare_voice._KOKORO_WORKER_CODE)
        self.assertEqual(prepare_voice._bump_edge_rate("+10%", 8), "+18%")

    def test_v3_formant_shaping_loudness_peaks_and_shaadi_case_sync(self) -> None:
        m = make_valid_manifest()
        m["voiceConfig"] = {
            "mode": "edge_neural",
            "engineLicense": "COMMERCIAL_API",
            "azureSpeechRegion": "centralindia",
            "edgeFormants": {"jyoti": 1.065, "rajat": 1.12},
            "targetWpm": 165,
        }
        self.assertEqual(validate_episode.validate_manifest(m), [])

        for bad_formants in ("not-a-dict", {"jyoti": 0.70}, {"rajat": 1.35}, {"jyoti": True}):
            m["voiceConfig"]["edgeFormants"] = bad_formants
            errs = validate_episode.validate_manifest(m)
            self.assertTrue(any("edgeFormants" in e for e in errs), errs)

        self.assertEqual(
            prepare_voice.normalize_edge_clause_text("अरे रजत! क्या हुआ? बारह लाख साफ़ हो गए!"),
            "अरे रजत, क्या हुआ, बारह लाख साफ़ हो गए!",
        )
        self.assertEqual(
            prepare_voice.normalize_edge_clause_text("असली गद्दार कौन था? कमेंट करो, क्योंकि ये शुरू हुआ था..."),
            "असली गद्दार कौन था, कमेंट करो, क्योंकि ये शुरू हुआ था",
        )
        for token in ("1.065", "1.12", "asetrate=24000*", "0.095", "0.085", "0.11", "0.26"):
            self.assertIn(token, prepare_voice._EDGE_WORKER_CODE)

        wav_p = self.tmp_dir / "env_test.wav"
        sr = 44100
        loud_chunk = b"\x00\x40\x00\xc0" * (sr // 2)  # 1.0s loud square wave (~16384 amp)
        quiet_chunk = b"\x00\x08\x00\xf8" * (sr // 2)  # 1.0s quiet wave (~2048 amp)
        sil_chunk = b"\x00\x00" * sr  # 1.0s silence
        with wave.open(str(wav_p), "wb") as wf:
            wf.setparams((1, 2, sr, 0, "NONE", "not compressed"))
            wf.writeframes(loud_chunk + quiet_chunk + sil_chunk)
        test_caps = [
            {"word": "Loud", "startSec": 0.1, "endSec": 0.9},
            {"word": "Mixed", "startSec": 0.5, "endSec": 1.5},
            {"word": "Silent", "startSec": 2.1, "endSec": 2.8},
        ]
        prepare_voice.attach_wav_loudness_peaks(wav_p, test_caps)
        self.assertTrue(all(len(c["peak"]) == 4 and all(0.0 <= p <= 1.0 for p in c["peak"]) for c in test_caps))
        self.assertGreater(min(test_caps[0]["peak"]), 0.9)
        self.assertGreater(test_caps[1]["peak"][0], test_caps[1]["peak"][3])
        self.assertEqual(test_caps[2]["peak"], [0.0, 0.0, 0.0, 0.0])

        for ep_rel, expected_title in (
            ("episodes/s01-asset-classification/s01e01-forgotten-bucket.json", "Guddi Didi Ki Shaadi Ke 12 Lakh Gayab!"),
            ("episodes/s01-asset-classification/s01e02-crown-jewels.json", "74% Logon Ne Pappu Chachu Ko Chor Maana — Par Asli Gaddar Nikla..."),
        ):
            ep_data = json.loads((REPO_ROOT / ep_rel).read_text(encoding="utf-8"))
            self.assertEqual(ep_data["episodeTitle"], expected_title)
            dur = float(ep_data["durationSeconds"])
            wpm = sum(len(s["narration"].split()) for s in ep_data["scriptSegments"]) / (dur / 60.0)
            self.assertTrue(145.0 <= wpm <= 185.0, f"{ep_data['id']} WPM={wpm:.1f}")
            cap_file = REPO_ROOT / "engine" / "public" / "audio" / f"{ep_data['id']}.captions.json"
            caps_live = json.loads(cap_file.read_text(encoding="utf-8"))
            self.assertTrue(all(isinstance(w.get("peak"), list) and len(w["peak"]) == 4 for w in caps_live))

        e01 = json.loads((REPO_ROOT / "episodes/s01-asset-classification/s01e01-forgotten-bucket.json").read_text(encoding="utf-8"))
        e01_dur = float(e01["durationSeconds"])
        e01_wpm = sum(len(s["narration"].split()) for s in e01["scriptSegments"]) / (e01_dur / 60.0)
        self.assertLessEqual(e01_wpm, 185.0, f"s01e01 WPM={e01_wpm:.2f} exceeds 185.0 human prosody cap")
        self.assertIn("Cyber Jasoos", e01["scriptSegments"][2]["narration"])
        self.assertNotIn("Kabir", json.dumps(e01["scriptSegments"]))
        sc3_props = e01["scenes"][2]["props"]
        sc4_props = e01["scenes"][3]["props"]
        self.assertEqual(sc4_props["secondaryImage"], "characters/shaadi-chhat-wide.png")
        self.assertEqual(sc4_props["heroImage"], "characters/shaadi-chhat-signal.png")
        self.assertNotEqual(sc4_props["heroImage"], sc3_props["secondaryImage"])
        self.assertTrue(
            all("PM · " in s["role"] for s in e01["scenes"][4]["props"]["suspects"]),
            [s["role"] for s in e01["scenes"][4]["props"]["suspects"]],
        )
        e01_caps = json.loads((REPO_ROOT / "engine/public/audio/s01e01-forgotten-bucket.captions.json").read_text(encoding="utf-8"))
        sc5_start = float(e01["scenes"][4]["startSec"])
        opt_times = e01["scenes"][4]["props"]["optionTimingsSec"]
        sc5_words = {w["word"]: round(float(w["startSec"]) - sc5_start, 3) for w in e01_caps if float(w["startSec"]) >= sc5_start - 0.05}
        self.assertEqual(opt_times, [sc5_words["do"], sc5_words["jeb"], sc5_words["aur"]])
        self.assertIn("CHHAT PAR CHALU", e01["scenes"][4]["props"]["forensicClueBar"])
        sfx_wav = REPO_ROOT / "engine" / "public" / "sfx" / "heartbeat-radar-ping.wav"
        self.assertTrue(sfx_wav.is_file(), f"Missing SFX WAV: {sfx_wav}")
        with wave.open(str(sfx_wav), "rb") as sfx_wf:
            self.assertEqual((sfx_wf.getnchannels(), sfx_wf.getsampwidth(), sfx_wf.getframerate()), (1, 2, 44100))
            sfx_dur = sfx_wf.getnframes() / float(sfx_wf.getframerate())
            self.assertAlmostEqual(sfx_dur, 1.45, places=2)
            sfx_pcm = struct.unpack(f"<{sfx_wf.getnframes()}h", sfx_wf.readframes(sfx_wf.getnframes()))
            self.assertTrue(16000 <= max(abs(x) for x in sfx_pcm) <= 26000)
        for char_png in ("kabir-investigating.png", "sharma-shock.png", "golu.png", "ramu-kaka.png", "pappu-chachu.png"):
            png_data = (REPO_ROOT / "engine" / "public" / "characters" / char_png).read_bytes()
            self.assertEqual(png_data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", png_data[16:24]), (1080, 1920), char_png)
        suspect_board_src = (REPO_ROOT / "engine/src/components/DetectiveSuspectBoardScene.tsx").read_text(encoding="utf-8")
        self.assertNotIn("<img", suspect_board_src)
        self.assertIn("<Img", suspect_board_src)

    def test_v9_pixel_locked_chhat_plates_and_vibrate_sfx(self) -> None:
        vibrate_wav = REPO_ROOT / "engine" / "public" / "sfx" / "puja-phone-vibrate.wav"
        self.assertTrue(vibrate_wav.is_file(), f"Missing vibrate SFX WAV: {vibrate_wav}")
        with wave.open(str(vibrate_wav), "rb") as vwf:
            self.assertEqual((vwf.getnchannels(), vwf.getsampwidth(), vwf.getframerate()), (1, 2, 44100))
            vdur = vwf.getnframes() / float(vwf.getframerate())
            self.assertTrue(0.8 <= vdur <= 1.1, f"Unexpected puja-phone-vibrate.wav duration: {vdur:.3f}s")
            vpcm = struct.unpack(f"<{vwf.getnframes()}h", vwf.readframes(vwf.getnframes()))
            self.assertTrue(15000 <= max(abs(x) for x in vpcm) <= 23000)

        for plate_name in ("shaadi-chhat-wide.png", "shaadi-chhat-signal.png", "sharma-eyes-closeup.png"):
            plate_path = REPO_ROOT / "engine" / "public" / "characters" / plate_name
            png_hdr = plate_path.read_bytes()[:24]
            self.assertEqual(png_hdr[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", png_hdr[16:24]), (1080, 1920), plate_name)

        venv_py = REPO_ROOT / ".venv_audio" / "bin" / "python"
        py_bin = str(venv_py) if venv_py.is_file() else sys.executable
        probe_code = (
            "import json, pathlib, subprocess, sys\n"
            "import numpy as np\n"
            "out = {}\n"
            "for p_str in sys.argv[1:]:\n"
            "    p = pathlib.Path(p_str)\n"
            "    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(p), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])\n"
            "    arr = np.frombuffer(raw, dtype=np.uint8).reshape(1920, 1080, 3).astype(np.int32)\n"
            "    r, g = arr[:, :, 0], arr[:, :, 1]\n"
            "    yy, xx = np.mgrid[0:1920, 0:1080]\n"
            "    m_top = (r >= 150) & ((r - g) >= 90) & (yy >= 450) & (yy <= 880)\n"
            "    m_bot = (r >= 150) & ((r - g) >= 90) & (yy > 950)\n"
            "    out[p.name] = {\n"
            "        'count': int(m_top.sum()),\n"
            "        'cx': float(xx[m_top].mean()) if m_top.any() else -1.0,\n"
            "        'cy': float(yy[m_top].mean()) if m_top.any() else -1.0,\n"
            "        'below_950': int(m_bot.sum()),\n"
            "    }\n"
            "print(json.dumps(out))\n"
        )
        plates = [
            str(REPO_ROOT / "engine" / "public" / "characters" / "shaadi-chhat-wide.png"),
            str(REPO_ROOT / "engine" / "public" / "characters" / "shaadi-chhat-signal.png"),
        ]
        metrics = json.loads(subprocess.check_output([py_bin, "-c", probe_code, *plates], text=True))
        for fname, stats in metrics.items():
            self.assertGreater(stats["count"], 500, fname)
            self.assertTrue(520.0 <= stats["cx"] <= 560.0, f"{fname} cx={stats['cx']:.2f} outside 520..560")
            self.assertTrue(645.0 <= stats["cy"] <= 685.0, f"{fname} cy={stats['cy']:.2f} outside 645..685")
            self.assertEqual(stats["below_950"], 0, f"{fname} has {stats['below_950']} bright red pixels below y=950")

        ig_src = (REPO_ROOT / "scripts" / "render_instagram_ui_mockup.py").read_text(encoding="utf-8")
        self.assertIn("IG REELS SAFE-ZONE SIMULATOR · 124PX RAIL · {measured_overlap_pct}% OVERLAP", ig_src)
        self.assertNotIn("REAL IPHONE", ig_src)
        self.assertIn("956.0", ig_src)
        self.assertIn("1018.0", ig_src)

        clean_frame = render_instagram_ui_mockup.decode_rgb(REPO_ROOT / "renders" / "s01e01-preview-frame.png", 1080, 1920)
        self.assertEqual(render_instagram_ui_mockup.measure_right_rail_overlap_pct(clean_frame, caption_right_x=922), 0)
        intruding_frame = clean_frame.copy()
        render_instagram_ui_mockup.rrect(intruding_frame, 132, 1080, 888, 140, 18, (240, 245, 252), 0.96)
        self.assertGreater(render_instagram_ui_mockup.measure_right_rail_overlap_pct(intruding_frame, caption_right_x=922), 0)
        bad_png = self.tmp_dir / "intruding_frame.png"
        render_instagram_ui_mockup.encode_png(intruding_frame, bad_png)
        with self.assertRaises(ValueError):
            render_instagram_ui_mockup.build_mockup_array(bad_png, REPO_ROOT / "engine" / "public" / "brand" / "kabir-avatar.png")

    def test_v9_part2_finale_cast_voice_and_continuity(self) -> None:
        e02 = json.loads((REPO_ROOT / "episodes/s01-asset-classification/s01e02-crown-jewels.json").read_text(encoding="utf-8"))
        e02_dur = float(e02["durationSeconds"])
        e02_wpm = sum(len(s["narration"].split()) for s in e02["scriptSegments"]) / (e02_dur / 60.0)
        self.assertLessEqual(e02_wpm, 185.0, f"s01e02 WPM={e02_wpm:.2f} exceeds 185.0 human prosody cap")
        narration_blob = " ".join(s["narration"] for s in e02["scriptSegments"])
        self.assertIn("Cyber Jasoos", narration_blob)
        for banned in ("Kabir", "divert", "freeze"):
            self.assertNotIn(banned.lower(), narration_blob.lower())

        sc2_devs = e02["scenes"][1]["props"]["devices"]
        self.assertIn("11:25 PM", sc2_devs[0]["name"])
        self.assertIn("7:42 PM", sc2_devs[1]["name"])
        self.assertIn("7:40 PM", sc2_devs[2]["name"])
        self.assertTrue(
            all(s["timestampBadge"] == f"CASE {s['key']}" and len(s["role"]) >= 5 for s in e02["scenes"][4]["props"]["suspects"]),
            [(s.get("timestampBadge"), s["role"]) for s in e02["scenes"][4]["props"]["suspects"]],
        )

        e02_caps = json.loads((REPO_ROOT / "engine/public/audio/s01e02-crown-jewels.captions.json").read_text(encoding="utf-8"))
        self.assertLessEqual(max(len(w["word"]) for w in e02_caps), 18)
        twist_src = (REPO_ROOT / "engine/src/components/DetectiveEvidenceTwistScene.tsx").read_text(encoding="utf-8")
        self.assertTrue("['#', '#', '0', '0', '2', '#']" in twist_src or "eraseCode" in twist_src or "##002#" in twist_src)
        sc5_start = float(e02["scenes"][4]["startSec"])
        sc5_words = [w for w in e02_caps if float(w["startSec"]) >= sc5_start - 0.05]
        t_a = next(round(float(w["startSec"]) - sc5_start, 3) for w in sc5_words if w["word"].startswith("Hotel"))
        t_b = next(round(float(w["startSec"]) - sc5_start, 3) for w in sc5_words if w["word"].startswith("Daftaron"))
        t_c = next(
            round(float(w["startSec"]) - sc5_start, 3)
            for i, w in enumerate(sc5_words[:-1])
            if w["word"] in ("ya", "aur") and sc5_words[i + 1]["word"].startswith("Shaadi")
        )
        self.assertEqual(e02["scenes"][4]["props"]["optionTimingsSec"], [t_a, t_b, t_c])

        part2_pngs = (
            "golu-caught-tanki.png",
            "sharma-relief-dawn.png",
            "tanki-burner-phone.png",
            "case02-hotel-wifi.png",
            "case02-smart-printer.png",
            "case02-shaadi-qr.png",
        )
        for fname in part2_pngs:
            hdr = (REPO_ROOT / "engine" / "public" / "characters" / fname).read_bytes()[:24]
            self.assertEqual(hdr[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", hdr[16:24]), (1080, 1920), fname)

    def test_v10_cinema_stack_depth_cameos_and_foley(self) -> None:
        e01 = json.loads((REPO_ROOT / "episodes/s01-asset-classification/s01e01-forgotten-bucket.json").read_text(encoding="utf-8"))
        e02 = json.loads((REPO_ROOT / "episodes/s01-asset-classification/s01e02-crown-jewels.json").read_text(encoding="utf-8"))
        c01 = json.loads((REPO_ROOT / "engine/public/audio/s01e01-forgotten-bucket.captions.json").read_text(encoding="utf-8"))
        c02 = json.loads((REPO_ROOT / "engine/public/audio/s01e02-crown-jewels.captions.json").read_text(encoding="utf-8"))

        # 1. Diegetic character voice cameos + max word length guard across BOTH episodes
        self.assertEqual({w.get("speaker") for w in c01}, {"narrator", "sharma"})
        self.assertEqual({w.get("speaker") for w in c02}, {"narrator", "chachu"})
        self.assertLessEqual(max(len(w["word"]) for w in c01), 18)
        self.assertLessEqual(max(len(w["word"]) for w in c02), 18)

        # 2. Golu bomber-jacket phone-dial wardrobe fix in Part 2 Scene 2
        self.assertEqual(e02["scenes"][1]["props"]["secondaryImage"], "characters/golu-phone-dial.png")
        golu_dial_hdr = (REPO_ROOT / "engine/public/characters/golu-phone-dial.png").read_bytes()[:24]
        self.assertEqual(struct.unpack(">II", golu_dial_hdr[16:24]), (1080, 1920))

        # 3. All 20 neural depth foreground RGBA mattes exist at 1080x1920 RGBA (color_type=6)
        char_dir = REPO_ROOT / "engine" / "public" / "characters"
        fg_dir = char_dir / "fg"
        base_plates = sorted(p.name for p in char_dir.glob("*.png") if p.is_file())
        self.assertGreaterEqual(len(base_plates), 20)
        for plate_name in base_plates:
            fg_path = fg_dir / plate_name
            self.assertTrue(fg_path.is_file(), f"Missing neural depth foreground matte: {fg_path}")
            ihdr = fg_path.read_bytes()[:26]
            self.assertEqual(ihdr[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", ihdr[16:24]), (1080, 1920), plate_name)
            self.assertEqual(ihdr[25], 6, f"{plate_name} fg matte must be RGBA (color_type=6)")

        # 4. All 4 procedural cinema foley WAVs exist at 44.1kHz 16-bit mono PCM
        for sfx_name, min_dur in (
            ("bank-sms-chime.wav", 0.55),
            ("rooftop-wind-drip.wav", 4.5),
            ("keypad-tap-seq.wav", 1.8),
            ("dawn-temple-bell.wav", 2.8),
        ):
            sfx_p = REPO_ROOT / "engine" / "public" / "sfx" / sfx_name
            self.assertTrue(sfx_p.is_file(), f"Missing V10 foley WAV: {sfx_p}")
            with wave.open(str(sfx_p), "rb") as wf:
                self.assertEqual((wf.getnchannels(), wf.getsampwidth(), wf.getframerate()), (1, 2, 44100), sfx_name)
                self.assertGreaterEqual(wf.getnframes() / 44100.0, min_dur, sfx_name)

        # 5. NoirParallaxStage wired across all 3 Noir cinema scene renderers
        for comp_name in ("DetectiveCrimeHookScene.tsx", "DetectiveWifiClueScene.tsx", "DetectiveEvidenceTwistScene.tsx"):
            comp_src = (REPO_ROOT / "engine" / "src" / "components" / comp_name).read_text(encoding="utf-8")
            self.assertIn("NoirParallaxStage", comp_src, comp_name)

    def test_v11_honest_license_word_boundary_peaks_and_poll_branching(self) -> None:
        # 1. P0-1 Honest Mode-to-License Gate & --publish-ready enforcement
        m_edge = make_valid_manifest()
        m_edge["voiceConfig"] = {"mode": "edge_neural", "engineLicense": "COMMERCIAL_API", "targetWpm": 165}
        self.assertTrue(any("azureSpeechRegion" in e for e in validate_episode.validate_manifest(m_edge)))

        m_edge["voiceConfig"]["engineLicense"] = "EDGE_READ_ALOUD_PREVIEW"
        self.assertEqual(validate_episode.validate_manifest(m_edge, publish_ready=False), [])
        pub_errs = validate_episode.validate_manifest(m_edge, publish_ready=True)
        self.assertTrue(any("Publish-Ready License Guard" in e for e in pub_errs), pub_errs)

        m_edge["voiceConfig"] = {
            "mode": "edge_neural",
            "engineLicense": "COMMERCIAL_API",
            "azureSpeechRegion": "centralindia",
            "targetWpm": 165,
        }
        self.assertEqual(validate_episode.validate_manifest(m_edge, publish_ready=True), [])

        m_draft = make_valid_manifest()
        m_draft["voiceConfig"] = {"mode": "draft_say", "engineLicense": "OWN_VOICE", "targetWpm": 165}
        self.assertTrue(any("MACOS_DRAFT" in e for e in validate_episode.validate_manifest(m_draft)))
        m_draft["voiceConfig"]["engineLicense"] = "MACOS_DRAFT"
        self.assertEqual(validate_episode.validate_manifest(m_draft, publish_ready=False), [])
        self.assertTrue(any("Publish-Ready License Guard" in e for e in validate_episode.validate_manifest(m_draft, publish_ready=True)))

        ep_preview = self.tmp_dir / "preview_ep.json"
        ep_preview.write_text(json.dumps(m_draft), encoding="utf-8")
        self.assertEqual(validate_episode.main([str(ep_preview)]), 0)
        self.assertEqual(validate_episode.main(["--publish-ready", str(ep_preview)]), 1)

        # 2. P0-3 Exact Neural WordBoundary Span Mapping, RMS Silence Snapping & Live Zero-Silence Gate
        seg_wb = {
            "id": "seg-wb",
            "startSec": 0.0,
            "endSec": 3.0,
            "phase": "hook",
            "speaker": "narrator",
            "narration": "Asli gaddar kaun hai? Neeche likhiye — abhi",
            "ttsClauses": [
                {
                    "speaker": "narrator",
                    "roman": "Asli gaddar kaun hai? Neeche likhiye — abhi",
                    "hi": "اصلی غدار کون ہے؟ نیچے لکھیے ابھی",
                }
            ],
            "highlightKeywords": ["Asli gaddar", "likhiye"],
        }
        wb_spans = [[[(0.05, 0.30), (0.31, 0.62), (0.63, 0.85), (0.86, 1.08), (1.52, 1.85), (1.86, 2.25), (2.28, 2.65)]]]
        wb_caps = prepare_voice.build_clause_locked_word_timestamps([seg_wb], [[(0.0, 2.80)]], wb_spans)
        self.assertEqual(len(wb_caps), 7)
        self.assertEqual(wb_caps[5]["word"], "likhiye —")
        # Pause [1.08..1.52] between sentence 1 ('hai?') and sentence 2 ('Neeche') must NOT be assigned to either word
        self.assertLessEqual(wb_caps[3]["endSec"], 1.10)
        self.assertGreaterEqual(wb_caps[4]["startSec"], 1.50)

        snap_wav = self.tmp_dir / "snap_test.wav"
        sr = 44100
        # 0.0..0.5s loud speech, 0.5..1.0s dead silence
        with wave.open(str(snap_wav), "wb") as wf:
            wf.setparams((1, 2, sr, 0, "NONE", "not compressed"))
            wf.writeframes((b"\x00\x38\x00\xc8" * (sr // 4)) + (b"\x00\x00" * (sr // 2)))
        drifted_caps = [
            {"word": "ghanton", "startSec": 0.05, "endSec": 0.52},
            {"word": "baad...", "startSec": 0.52, "endSec": 0.64},
        ]
        prepare_voice.attach_wav_loudness_peaks(snap_wav, drifted_caps)
        self.assertEqual(max(drifted_caps[1]["peak"]), 0.0)
        prepare_voice.snap_words_off_silence(snap_wav, drifted_caps)
        prepare_voice.attach_wav_loudness_peaks(snap_wav, drifted_caps)
        self.assertGreaterEqual(max(drifted_caps[0]["peak"]), 0.05)
        self.assertGreaterEqual(max(drifted_caps[1]["peak"]), 0.05)

        for ep_id in ("s01e01-forgotten-bucket", "s01e02-crown-jewels"):
            live_caps = json.loads((REPO_ROOT / "engine" / "public" / "audio" / f"{ep_id}.captions.json").read_text(encoding="utf-8"))
            min_word_peak = min(max(w["peak"]) for w in live_caps)
            self.assertGreaterEqual(min_word_peak, 0.05, f"{ep_id} has silent caption word (min_peak={min_word_peak})")

        # Negative test: Caption Silence Guard catches max(peak) < 0.04
        e01 = json.loads((REPO_ROOT / "episodes/s01-asset-classification/s01e01-forgotten-bucket.json").read_text(encoding="utf-8"))
        bad_cap_rel = f"audio/.tmp_silent_{os.getpid()}.captions.json"
        bad_cap_abs = REPO_ROOT / "engine" / "public" / bad_cap_rel
        try:
            bad_cap_abs.write_text(json.dumps([{"word": "khamosh", "startSec": 0.1, "endSec": 0.4, "peak": [0.0, 0.01, 0.0, 0.0]}]), encoding="utf-8")
            e01_bad_cap = dict(e01, voiceConfig={**e01["voiceConfig"], "captionsFile": bad_cap_rel})
            cap_errs = validate_episode.validate_manifest(e01_bad_cap)
            self.assertTrue(any("Caption Silence Guard" in e for e in cap_errs), cap_errs)
        finally:
            bad_cap_abs.unlink(missing_ok=True)

        # 3. P1-4 / P1-5 noir_cinema Opening-Line Parity, Loop Suspension & Poll Branching CLI
        e01_bad_loop = json.loads(json.dumps(e01))
        e01_bad_loop["scriptSegments"][-1]["ttsClauses"][-1]["hi"] += "۔"
        self.assertTrue(any("Loop Suspension Guard" in e for e in validate_episode.validate_manifest(e01_bad_loop)))

        e02_src = REPO_ROOT / "episodes/s01-asset-classification/s01e02-crown-jewels.json"
        e02_orig = json.loads(e02_src.read_text(encoding="utf-8"))
        e02_tmp = self.tmp_dir / "s01e02-branch-test.json"
        shutil.copy2(e02_src, e02_tmp)

        # Full 1..99 Hindi/Urdu number table coverage with zero digit fallback
        self.assertEqual(set(apply_poll_result.HINDI_URDU_NUMS.keys()), set(range(1, 100)))
        for pct_k, (rom_w, urd_w) in apply_poll_result.HINDI_URDU_NUMS.items():
            self.assertTrue(rom_w and urd_w, f"Empty numeral entry for {pct_k}")
            self.assertFalse(any(ch.isdigit() for ch in rom_w + urd_w), f"Digit fallback in {pct_k}: {(rom_w, urd_w)}")
        self.assertEqual(apply_poll_result.HINDI_URDU_NUMS[38][0], "Artis")
        self.assertEqual(apply_poll_result.HINDI_URDU_NUMS[45][0], "Paintaalis")
        self.assertEqual(apply_poll_result.HINDI_URDU_NUMS[74][0], "Chauhattar")
        self.assertEqual(apply_poll_result.HINDI_URDU_NUMS[99][0], "Ninyanve")

        for winner, pct in (("A", 38), ("B", 45), ("C", 99), ("A", 68), ("B", 61), ("C", 74)):
            self.assertEqual(apply_poll_result.main(["--episode", str(e02_tmp), "--winner", winner, "--pct", str(pct)]), 0)
            branched = json.loads(e02_tmp.read_text(encoding="utf-8"))
            self.assertEqual(branched["hook"]["previousVoteResult"]["winningOption"], winner)
            self.assertEqual(branched["hook"]["previousVoteResult"]["percentage"], pct)
            self.assertIn(apply_poll_result.HINDI_URDU_NUMS[pct][0], branched["hook"]["openingLine"])
            self.assertEqual(validate_episode.validate_manifest(branched), [], f"Branch {winner}@{pct}% failed validation")
            self.assertEqual(validate_episode.validate_season_continuity([e01, branched]), [])
        e02_roundtrip = json.loads(e02_tmp.read_text(encoding="utf-8"))
        self.assertEqual(e02_roundtrip["episodeTitle"], e02_orig["episodeTitle"])
        self.assertEqual(e02_roundtrip["hook"]["openingLine"], e02_orig["hook"]["openingLine"])

        # Optional --pct reuses existing hook.previousVoteResult.percentage, and raises ValueError when absent (zero silent 60% fallback)
        self.assertEqual(apply_poll_result.main(["--episode", str(e02_tmp), "--winner", "B"]), 0)
        branched_no_pct = json.loads(e02_tmp.read_text(encoding="utf-8"))
        self.assertEqual(branched_no_pct["hook"]["previousVoteResult"]["winningOption"], "B")
        self.assertEqual(branched_no_pct["hook"]["previousVoteResult"]["percentage"], 74)
        e02_no_prev = json.loads(json.dumps(e02_orig))
        e02_no_prev["hook"].pop("previousVoteResult", None)
        with self.assertRaises(ValueError):
            apply_poll_result.apply_poll_branch(e02_no_prev, "A")

        # Validator pollBranches guard catches missing branch keys and unresolved {pct placeholders
        e02_missing_b = json.loads(json.dumps(e02_orig))
        e02_missing_b["pollBranches"].pop("B")
        self.assertTrue(any("pollBranches missing" in e for e in validate_episode.validate_manifest(e02_missing_b)))
        e02_bad_tok = json.loads(json.dumps(e02_orig))
        e02_bad_tok["pollBranches"]["A"]["openingLine"] += " {pct_typo}"
        self.assertTrue(any("unresolved placeholder" in e for e in validate_episode.validate_manifest(e02_bad_tok)))

        # V11.2 verified PIB Release ID 1995304 (11 Jan 2024) citation in BOTH episodes, honest 1930 lien/hold payoff, Indian Chachu voice & badge parity
        self.assertEqual(e01["realBreachParallel"]["year"], 2024)
        self.assertEqual(e02_orig["realBreachParallel"]["year"], 2024)
        self.assertIn("PIB Release ID 1995304, 11 Jan 2024", e01["realBreachParallel"]["incident"])
        self.assertIn("PIB Release ID 1995304, 11 Jan 2024", e02_orig["realBreachParallel"]["incident"])
        self.assertEqual(e01["scenes"][0]["props"]["secondaryParallaxMode"], "macro")
        self.assertEqual(e01["scenes"][4]["props"]["partBadge"], "PART 2 JALD")
        self.assertEqual(e02_orig["voiceConfig"]["edgeVoices"]["chachu"], "hi-IN-MadhurNeural")
        self.assertEqual(e02_orig["voiceConfig"]["edgeFormants"]["chachu"], 0.91)
        self.assertIn("rok li", e02_orig["scriptSegments"][3]["narration"])
        self.assertEqual(e02_orig["scenes"][3]["props"]["verdictPillLeft"], "✓ 1930 GOLDEN-HOUR LIEN HOLD")

        # Continuity check catches invalid winningOption on detective_crime_hook (even without comment_spotlight)
        e01_two_opts = json.loads(json.dumps(e01))
        e01_two_opts["scenes"][-1]["props"]["suspects"] = e01_two_opts["scenes"][-1]["props"]["suspects"][:2]
        cont_errs = validate_episode.validate_season_continuity([e01_two_opts, e02_orig])
        self.assertTrue(any("previousVoteResult.winningOption" in e and "'C'" in e for e in cont_errs), cont_errs)


if __name__ == "__main__":
    unittest.main()
