# Cyber Jasoos (`@cyberjasoos`) — V11 Cyber-Noir & Self-Healing Reels Engine

Data-driven `9:16` (`1080x1920` @ `30fps`) Hindi/Hinglish Crime-Cyber Reels production, validation, and closed-loop growth engine built on **Remotion 4**, **TypeScript**, and **Python**. Every episode dramatizes a real-world cyber fraud vector as an investigative noir whodunit led by **Detective Kabir** (`visualTheme: "noir_cinema"`, with legacy enterprise SOC/GRC modes supported), delivers a 5-second **Suraksha Kavach** (`*#21#`, `##002#`, MHA I4C `1930`), and connects **Part 1 -> Live Community `A / B / C` Poll -> Part 2** voter callout reveals.

## Canonical 5-Tab Documentation Hub (2 Entry Points, Zero Stray Docs)

- **[5-Tab Centralized Web Command Center (`docs/index.html`)](docs/index.html)** — Interactive 5-Tab visual portal (`1. Reel Factory Workflow`, `2. 21-Script CLI Directory`, `3. Show Spec & Safe Zones`, `4. Hybrid Launch & Poll Ops`, `5. Account Privacy & $0 Graph API`), `NOIR_GRID` visual previews (`docs/assets/*`), and sanitized static GitHub Pages export via `scripts/export_sanitized_pages.py`.
- **[Unified Production & Instagram Operations Handbook (`docs/instagram-launch-and-ops-playbook.md`)](docs/instagram-launch-and-ops-playbook.md)** — Single canonical Markdown reference mirroring all 5 Hub tabs across the 21 Python scripts, Part 1 & Part 2 (`pollBranches`) YAML briefs, `42–58s` retention clock, voice/asset provenance, `85% Mac Web + 15% Android` SOP, and 6-season curriculum.

## Core Architecture Highlights

1. **`42–58s` Noir Thriller Retention Clock**: Enforces contiguous 5-phase pacing (`hook` -> `escalation` -> `framework` -> `micro_payoff` -> `cliffhanger_vote`) at `130–195 WPM` (target `160–180 WPM`), blocks generic swipe-away openers, and holds vocal pitch on suspended `...` loop bridges (`Loop Suspension Guard`).
2. **`NOIR_GRID` `124px` Right-Rail Safe Zones (`1080x1920`)**: Locks lower cards and word-synced kinetic captions inside `x: 132..948` (`x >= 956` 100% clear of Instagram Reels right-rail icons), enforces `fontSize >= 20px` across noir overlays, and verifies every composition in Headless Chrome (`npm run uat:dom`).
3. **4-Pillar Deterministic Self-Healing & Auto-Improvement**:
   - **Zero-Touch Episode Registry (`scripts/sync_episode_registry.py`)**: Auto-discovers `episodes/**/*.json` into `engine/src/generated/episodeRegistry.ts`.
   - **Auto-Framed `1080x1920` Cast & 2.5D Mattes (`scripts/standardize_cast.py --auto-frame` + `scripts/generate_depth_mattes.py`)**: Eye-line-locked plates + Apache-2.0 Depth-Anything-V2 `fg`/`bg` parallax mattes + 18 procedural first-principles WAVs.
   - **Brief Compiler & Self-Healing Builder (`scripts/compile_story_brief.py` + `scripts/build_episode.py`)**: Compiles `.yaml`/`.json` briefs, conforms audio + captions, heals WPM/clock/schema drift, runs DOM UAT, and packages launch packs.
   - **SQLite Growth Ledger (`scripts/growth_ledger.py` + `scripts/instagram_ops.py record-metrics` & `learn`)**: Turns live Reel reach, save/share rates, skip rate, and poll votes into `data/learned_defaults.json`.
4. **Commercial-Clean Voice & Asset Gate (`--publish-ready`)**: Supports `OWN_VOICE` human recordings (`--mode recorded`), `$0` free-tier Azure Speech `F0` commercial neural voices (`ur-IN-SalmanNeural + hi-IN-MadhurNeural`, `COMMERCIAL_API`), and offline Apache-2.0 Kokoro ONNX (`APACHE_2_0`), while blocking non-commercial `CC-BY-NC` checkpoints.

## Prerequisites & Setup

- **Node.js** `20+` & `npm`, **Python** `3.10+`, and **FFmpeg** on `PATH` (`brew install ffmpeg`)

```bash
cd engine && npm install && cd ..
```

## Quickstart CLI Workflow

```bash
# 1. Conform 1080x1920 cast plates, generate 2.5D depth mattes & sync Remotion episode registry
.venv_audio/bin/python scripts/standardize_cast.py --case-dir assets/characters/case01 --auto-frame
.venv_audio/bin/python scripts/generate_depth_mattes.py
python3 scripts/sync_episode_registry.py

# 2. Build an episode end-to-end (conforms voice + captions, self-heals timings, runs DOM UAT & renders MP4)
.venv_audio/bin/python scripts/build_episode.py \
  --episode episodes/s01-asset-classification/s01e01-forgotten-bucket.json \
  --voice-mode recorded --voice-input episodes/audio/s01e01-forgotten-bucket.m4a \
  --launch-pack-dir renders/launch-pack-case01-part1 --render-mp4

# 3. Tally live Part 1 A/B/C votes at T+24h..48h & inject winning percentage into Part 2
python3 scripts/instagram_ops.py poll-tally \
  --media-id <PART1_MEDIA_ID> \
  --part1 episodes/s01-asset-classification/s01e01-forgotten-bucket.json \
  --apply-to episodes/s01-asset-classification/s01e02-crown-jewels.json

# 4. Export Voice Memos teleprompter & sanitized static GitHub Pages bundle from the 5-Tab Web Hub
python3 scripts/export_teleprompter.py --output renders/teleprompter-export.md
python3 scripts/export_sanitized_pages.py --src-dir docs --out-dir renders/gh-pages-bundle

# 5. Run full schema/publish-ready gate, 31-test Python suite & Headless Chrome safe-zone audit
python3 scripts/validate_episode.py episodes/ --publish-ready
python3 -m unittest discover -s tests -v
cd engine && npm run typecheck && npm run uat:dom
```

## Repository Layout

```text
SocialMediaShortVideo/
├── assets/                  # Brand kit PNGs (DP, 4 Story Highlights) & 1080x1920 cast/B-roll plates
├── data/                    # Learned retention defaults (learned_defaults.json) & SQLite growth ledger
├── docs/
│   ├── index.html           # 5-Tab Centralized Web Hub (exported via scripts/export_sanitized_pages.py)
│   ├── assets/              # Web Hub safe-zone mockups, brand previews & QA stills
│   └── instagram-launch-and-ops-playbook.md  # Single 5-Section Markdown Production & Ops Handbook
├── episodes/                # Canonical schema.json, briefs/*.yaml & Season 01–02 JSON manifests (0 .md files)
├── engine/                  # Remotion 4 TypeScript compositions, NOIR_GRID tokens & uat-dom-audit.mjs
├── scripts/                 # All 21 deterministic Python scripts (builder, briefs, voice, mattes, IG ops, Pages)
├── tests/                   # 31-test automated unit & self-healing ratchet suite
└── renders/                 # Reel covers, QA frames & gitignored H.264 MP4 / teleprompter / Pages exports
```
