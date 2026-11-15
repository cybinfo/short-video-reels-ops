#!/usr/bin/env python3
"""Ratchet unit/integration tests for the 6 video-guide automation fixes & MP4 chapter stitcher."""

from __future__ import annotations

import copy, io, json, struct, subprocess, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import apply_poll_result  # noqa: E402
import compile_story_brief  # noqa: E402
import generate_ig_brand_kit  # noqa: E402
import self_heal_rules  # noqa: E402
import standardize_cast  # noqa: E402
import stitch_video_guide  # noqa: E402
import sync_episode_registry  # noqa: E402
import validate_episode  # noqa: E402

FFMPEG = stitch_video_guide.FFMPEG
FFPROBE = stitch_video_guide.FFPROBE
CASE02_BRIEF = REPO_ROOT / "episodes" / "briefs" / "case02-part1-shaadi-qr.yaml"
KABIR_FRAME = REPO_ROOT / "engine" / "public" / "characters" / "kabir-closeup.png"


def _png_size(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", f"Not a valid PNG: {path}"
    return struct.unpack(">II", raw[16:24])


def _guide_brief(part: int = 1, **extra: object) -> dict:
    return {
        "preset": "guide_walkthrough", "season": 9, "episodeNumber": part, "part": part,
        "id": f"s09e0{part}-guide-ratchet", "title": "Zero AI Reel Factory Walkthrough",
        "hudPartBadge": f"GUIDE {part}/4",
        "beats": {
            "hook": "Paintis line ka YAML story brief likhiye aur Cyber Jasoos engine khud poora 1080p vertical noir episode bina kisi manual timeline edit ke taiyaar karta hai!",
            "escalation": "Raw character ya UI screenshot folder mein daalte hi standardize cast script har plate ko 1080 by 1920 portrait aur safe zone vignette mein lock karti hai!",
            "framework": "Build episode orchestrator pehle neural aawaaz aur word timestamps banata hai, phir WPM ya duration bahar hone par khud speech rate adjust karke dobara sync karta hai!",
            "micro_payoff": "Headless Chrome DOM auditor har frame par 124 pixel right rail aur subtitle safe zone naapta hai aur lamba badge milte hi turant self heal kar deta hai!",
            "cliffhanger_vote": "Agle chapter mein dekhiye sham saat chalis par upload, live poll tally aur SQLite growth ledger kaise kaam karte hain, kaunsa gate best laga comment kijiye...",
        },
        **extra,
    }


class GuideAutomationRatchetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_manifest = compile_story_brief.compile_brief(compile_story_brief.load_brief(CASE02_BRIEF))

    def test_validate_and_registry_prune_briefs_and_guides(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ep_dir = Path(td) / "episodes"
            for sub in ("briefs", "guides", "s01-case"):
                (ep_dir / sub).mkdir(parents=True)
            (ep_dir / "schema.json").write_text("{}", encoding="utf-8")
            (ep_dir / "briefs" / "b01.json").write_text('{"id": "s91e01-brief", "scenes": []}', encoding="utf-8")
            (ep_dir / "s01-case" / "draft.brief.json").write_text('{"id": "s01e99-draft", "scenes": []}', encoding="utf-8")
            live_ep = {**copy.deepcopy(self.base_manifest), "id": "s01e01-live-case", "season": 1, "episode": 1}
            guide_ep = {**copy.deepcopy(self.base_manifest), "id": "s99e01-guide-ch01", "season": 99, "episode": 1}
            (ep_dir / "s01-case" / "s01e01-live-case.json").write_text(json.dumps(live_ep), encoding="utf-8")
            (ep_dir / "guides" / "s99e01-guide-ch01.json").write_text(json.dumps(guide_ep), encoding="utf-8")
            (ep_dir / "guides" / "skip.brief.json").write_text("{}", encoding="utf-8")

            root_targets = validate_episode._collect_targets([str(ep_dir)])
            self.assertEqual([p.name for p in root_targets], ["s01e01-live-case.json"])

            guide_targets = validate_episode._collect_targets([str(ep_dir / "guides")])
            self.assertEqual([p.name for p in guide_targets], ["s99e01-guide-ch01.json"])

            reg_found = sync_episode_registry.discover_episode_manifests(ep_dir)
            self.assertEqual([p.name for p in reg_found], ["s01e01-live-case.json"])

    def test_standardize_cast_jpg_and_ui_broll_auto_frame(self) -> None:
        plate_png = "guide-unit-test-ui.png"
        pub_out = REPO_ROOT / "engine" / "public" / "characters" / plate_png
        try:
            with tempfile.TemporaryDirectory() as td:
                case_dir = Path(td) / "guide_case"
                raw_dir = case_dir / "raw"
                raw_dir.mkdir(parents=True)
                raw_jpg = raw_dir / "guide-unit-test-ui.jpg"
                subprocess.run(
                    [FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=800x1200:d=0.04", "-frames:v", "1", str(raw_jpg)],
                    check=True,
                )
                with redirect_stdout(io.StringIO()):
                    rc = standardize_cast.main(["--case-dir", str(case_dir), "--auto-frame", "--only", plate_png])
                self.assertEqual(rc, 0)
                self.assertTrue((case_dir / plate_png).is_file())
                self.assertTrue(pub_out.is_file())
                self.assertEqual(_png_size(case_dir / plate_png), (1080, 1920))
                self.assertEqual(_png_size(pub_out), (1080, 1920))
        finally:
            pub_out.unlink(missing_ok=True)
        self.assertFalse(pub_out.exists())

    def test_guide_walkthrough_preset_and_poll_branch_caps(self) -> None:
        m_p1 = compile_story_brief.compile_brief(_guide_brief(part=1))
        blob_p1 = json.dumps(m_p1)
        self.assertEqual(m_p1["hudPartBadge"], "GUIDE 1/4")
        self.assertNotIn("VERIFY PAYEE & WIFI", blob_p1)
        self.assertNotIn("shaadi-distant-intro.wav", blob_p1)
        self.assertEqual(validate_episode.validate_manifest(m_p1), [])
        self.assertLessEqual(len(m_p1["scenes"][0]["props"]["scrollStopper"]["badge"]), 26)

        m_p2 = compile_story_brief.compile_brief(
            _guide_brief(
                part=2,
                previousVoteResult={"winningOption": "B", "percentage": 76},
                pollBranches={
                    "A": {"openingLine": "{pct_word} percent builders ne YAML Brief Compiler ko top automation pillar chuna aur dekhiye agla self healing gate kaise chalta hai!", "stopperBadge": "POLL · {pct}% VOTED YAML BRIEF COMPILER STAGE"},
                    "B": {"openingLine": "{pct_word} percent builders ne Audio WPM Sync loop ko sabse powerful bataya aur ab dekhiye live safe zone audit kaise kaam karta hai!", "stopperBadge": "POLL · {pct}% VOTED AUDIO WPM SYNC ENGINE"},
                    "C": {"openingLine": "{pct_word} percent builders ne Headless DOM Heal ko chuna aur ab dekhiye poora master video chapter stitcher kaise kaam karta hai!", "stopperBadge": "POLL · {pct}% VOTED HEADLESS CHROME DOM HEAL"},
                },
            )
        )
        blob_p2 = json.dumps(m_p2)
        self.assertNotIn("VERIFY PAYEE & WIFI", blob_p2)
        self.assertNotIn("shaadi-distant-intro.wav", blob_p2)
        self.assertEqual(validate_episode.validate_manifest(m_p2), [])
        self.assertLessEqual(len(m_p2["scenes"][0]["props"]["scrollStopper"]["badge"]), 26)
        for opt in ("A", "B", "C"):
            applied = apply_poll_result.apply_poll_branch(m_p2, opt, 84)
            self.assertEqual(validate_episode.validate_manifest(applied), [])
            self.assertLessEqual(len(applied["scenes"][0]["props"]["scrollStopper"]["badge"]), 26)

    def test_expanded_dom_self_heal_caps(self) -> None:
        over = copy.deepcopy(self.base_manifest)
        over["scenes"][0]["props"]["shotTitles"] = ["ULTRA LONG SHOT TITLE THAT EXCEEDS TWENTY EIGHT CHAR CAP EASILY"]
        over["scenes"][1]["props"]["devices"][0]["status"] = "GATE 01 · ULTRA VERBOSE DEVICE STATUS OVERFLOWING SAFE ZONE RAIL"
        over["scenes"][2]["props"]["stepOneTitle"] = "THIRTY FIVE LINE YAML COMPILER OVERFLOW TITLE"
        over["scenes"][2]["props"]["exposedItems"] = ["SUPER LONG EXPOSED FORENSIC ITEM BADGE OVERFLOW"]
        over["scenes"][3]["props"]["crossedOutLabel"] = "MANUAL TIMELINE HARDCODING COMPLETELY BANNED HERE"
        rep = {"defects": [{"episode": over["id"], "sceneIndex": idx, "code": "HORIZONTAL_CLIP"} for idx in (0, 1, 2, 3)]}

        healed, actions = self_heal_rules.heal_dom_defects(over, rep)
        self.assertGreaterEqual(len(actions), 5)
        self.assertLessEqual(len(healed["scenes"][0]["props"]["shotTitles"][0]), 28)
        self.assertLessEqual(len(healed["scenes"][1]["props"]["devices"][0]["status"]), 32)
        self.assertLessEqual(len(healed["scenes"][2]["props"]["stepOneTitle"]), 26)
        self.assertLessEqual(len(healed["scenes"][2]["props"]["exposedItems"][0]), 22)
        self.assertLessEqual(len(healed["scenes"][3]["props"]["crossedOutLabel"]), 26)

    def test_brand_kit_dynamic_part2_and_guide_cover(self) -> None:
        captured: list[list[dict]] = []
        real_overlay = generate_ig_brand_kit.overlay_typography

        def _spy_overlay(img, items: list[dict]) -> None:
            captured.append(copy.deepcopy(items))
            real_overlay(img, items)

        with tempfile.TemporaryDirectory() as td, patch.object(generate_ig_brand_kit, "overlay_typography", side_effect=_spy_overlay):
            root = Path(td)
            p2_ep = {
                **copy.deepcopy(self.base_manifest),
                "id": "s02e02-shaadi-qr-reveal", "season": 2, "episode": 2,
                "hudPartBadge": "PART 2/2", "coldOpenTag": "72% VOTE · QR STICKER TRAP",
                "hook": {**self.base_manifest["hook"], "previousVoteResult": {"winningOption": "C", "percentage": 72}},
            }
            p2_json, p2_png = root / "s02e02.json", root / "s02e02-cover.png"
            p2_json.write_text(json.dumps(p2_ep), encoding="utf-8")
            generate_ig_brand_kit.build_reel_cover(p2_json, KABIR_FRAME, p2_png)
            self.assertEqual(_png_size(p2_png), (1080, 1920))
            p2_texts = " | ".join(it["text"] for it in captured[-1])
            self.assertIn("72% VOTED OPTION C!", p2_texts)
            self.assertNotIn("CHHAT KA ASLI GADDAR", p2_texts)

            g_ep = compile_story_brief.compile_brief(_guide_brief(part=1))
            g_json, g_png = root / "guide01.json", root / "guide01-cover.png"
            g_json.write_text(json.dumps(g_ep), encoding="utf-8")
            generate_ig_brand_kit.build_reel_cover(g_json, KABIR_FRAME, g_png)
            self.assertEqual(_png_size(g_png), (1080, 1920))
            g_texts = " | ".join(it["text"] for it in captured[-1])
            self.assertIn("GUIDE 1/4", g_texts)
            self.assertNotIn("CHHAT KA ASLI GADDAR", g_texts)

    def test_stitch_video_guide_with_ffmetadata_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            clips = [root / "ch1.mp4", root / "ch2.mp4"]
            for clip in clips:
                subprocess.run(
                    [
                        FFMPEG, "-y", "-v", "error",
                        "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30:d=0.5",
                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(clip),
                    ],
                    check=True,
                )
            out_mp4 = root / "stitched.mp4"
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = stitch_video_guide.main(["--inputs", str(clips[0]), str(clips[1]), "--titles", "Ch 1", "Ch 2", "--output", str(out_mp4)])
            self.assertEqual(rc, 0)
            summary = json.loads(buf.getvalue())
            self.assertEqual(summary["chapterCount"], 2)

            probe = json.loads(
                subprocess.check_output(
                    [FFPROBE, "-v", "error", "-show_streams", "-show_chapters", "-of", "json", str(out_mp4)],
                    text=True,
                )
            )
            v_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
            self.assertEqual((v_stream["width"], v_stream["height"]), (1080, 1920))
            self.assertEqual([c["tags"]["title"] for c in probe["chapters"]], ["Ch 1", "Ch 2"])


if __name__ == "__main__":
    unittest.main()
