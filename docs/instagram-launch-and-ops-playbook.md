# Cyber Jasoos (`@cyberjasoos`) — Unified Production, Self-Healing Engine & Instagram Operations Handbook

Canonical single-source Markdown handbook for **Cyber Jasoos (`@cyberjasoos`)**, structured in exact lockstep with the **5-Tab Centralized Web Hub** ([`docs/index.html`](index.html), exported to static GitHub Pages via `scripts/export_sanitized_pages.py`):
1. **End-to-End Reel Factory Workflow** (`3m 07s Hinglish Master Video Guide, 4-Pillar Self-Healing Pipeline + Part 1 & Part 2 YAML Briefs`)
2. **Master Script & CLI Directory** (`All 23 Python Scripts + Remotion 4 Engine Commands`)
3. **Show Spec, Safe Zones, Voice Provenance & 6-Season Curriculum** (`42–58s Clock, NOIR_GRID, Season 2 NovaPay Arc`)
4. **Hybrid Instagram Launch, Active Case Ops & Part 1 -> Part 2 Poll Loop** (`85% Mac Web + 15% Android SOP`)
5. **One-Time Account Privacy & $0 Meta Graph API Setup** (`Android Trust Anchor, Handle Matrix & Graph v22.0`)

## 1. End-to-End Reel Factory Workflow

### End-to-End Hinglish Video Guide (`3m 07s` · 4 Chapters)

- **Master Stitched Video (`1080x1920 @ 30fps`, `FFMETADATA1` Chapter Markers)**: `renders/guide/cyber-jasoos-automation-master-guide.mp4` (`open renders/guide/cyber-jasoos-automation-master-guide.mp4`)
- **Non-Crime Tutorial / Explainer YAML Preset**: Set `preset: guide_walkthrough` in any YAML Story Brief (`compile_story_brief.py` + `story_brief_templates.py`), generate deterministic `1080x1920` UI/YAML/CLI/Safe-Zone plates via `scripts/render_guide_plates.py`, build chapter MP4s via `scripts/build_episode.py --mp4-output`, and stitch chapters via `scripts/stitch_video_guide.py`.

| Chapter & Timestamp | Walkthrough Coverage | Standalone Chapter Reel MP4 |
| :--- | :--- | :--- |
| **`00:00 — Ch 1 (51.9s)`** | 5-Tab Web Hub, `.png/.jpg` Auto-Cast & 35-Line Story Brief (`preset: guide_walkthrough`) | `renders/guide/ch01-story-brief-autocast.mp4` |
| **`00:52 — Ch 2 (47.2s)`** | Single-Command `build_episode.py`, Voice Modes & Safe-Zone Self-Heal | `renders/guide/ch02-self-healing-build.mp4` |
| **`01:39 — Ch 3 (44.1s)`** | `7:40 PM IST` Upload SOP, Comment Tally & `95%` Zero-AI Part 2 Branch | `renders/guide/ch03-upload-and-poll-branch.mp4` |
| **`02:23 — Ch 4 (43.8s)`** | SQLite Mosseri Growth Ledger & Auto-Inherited Defaults | `renders/guide/ch04-growth-ledger-learning.mp4` |

### 4-Pillar Deterministic Self-Healing & Auto-Improvement Engine

Every stage from 35-line YAML brief to rendered launch pack and post-publish parameter tuning runs 100% deterministically in local Python + TypeScript with zero external model runtime dependencies:

1. **Pillar 1 — Zero-Touch Episode Registry (`scripts/sync_episode_registry.py`)**: Scans `episodes/**/*.json` (excluding `schema.json` and `briefs/`) and generates `engine/src/generated/episodeRegistry.ts` so every episode registers in Remotion automatically.
2. **Pillar 2 — Auto-Calibrated `1080x1920` Cast Framing & 2.5D Mattes (`scripts/standardize_cast.py --auto-frame` + `scripts/generate_depth_mattes.py` + `scripts/render_guide_plates.py`)**: Locks raw `.png/.jpg/.webp` plates in `<case_dir>/raw/` to eye-line-calibrated `1080x1920` PNGs, deterministically inpaints third-party stencils, renders walkthrough plates (`assets/characters/guide01/raw/`), and generates Apache-2.0 `fg/*.png` + `bg/*.jpg` parallax depth layers.
3. **Pillar 3 — Story Brief Compiler, Self-Healing Builder & Guide Stitcher (`scripts/compile_story_brief.py` + `scripts/build_episode.py` + `scripts/self_heal_rules.py` + `scripts/stitch_video_guide.py`)**: Compiles `.yaml`/`.json` briefs (`crime_case` or `preset: guide_walkthrough`, seeded by `data/learned_defaults.json`) into validated `EpisodeManifest` JSONs, conforms `44.1kHz` narration + word captions, iteratively heals speech-rate/WPM/text/DOM drift (`--max-heal-iters 3`), runs Headless Chrome `npm run uat:dom`, emits the MP4 (`--mp4-output`) + `POST_COPY_AND_PINNED_COMMENT.txt` + grid-safe Reel cover, and stitches multi-chapter MP4 guides with `FFMETADATA1` chapters.
4. **Pillar 4 — SQLite Growth Telemetry Ledger (`scripts/growth_ledger.py` + `scripts/instagram_ops.py record-metrics` & `learn`)**: Logs per-Reel reach, saves, shares, skip rate, poll votes, hook style, and IST upload hour into `data/growth_ledger.sqlite3`, then writes top-performing duration, WPM, hook archetype, and IST slot priors to `data/learned_defaults.json`.

### Step-by-Step Reel Factory CLI Pipeline

```bash
# 1. Score cold-open hook (0-100), conform 1080x1920 cast plates, build 2.5D mattes & sync registry
python3 scripts/competitor_hooks.py --score "Subah beti ki doli uthne wali thi, magar aadhi raat baarah lakh gayab!"
.venv_audio/bin/python scripts/standardize_cast.py --case-dir assets/characters/case01 --auto-frame
.venv_audio/bin/python scripts/generate_depth_mattes.py --skip-existing
python3 scripts/sync_episode_registry.py

# 2. Compile a YAML brief (inheriting learned_defaults.json) & run single-command self-healing build
.venv_audio/bin/python scripts/compile_story_brief.py \
  --brief episodes/briefs/case02-part1-shaadi-qr.yaml \
  --defaults data/learned_defaults.json \
  --output episodes/s02-risk-assessment/s02e01-shaadi-qr-trap.json
.venv_audio/bin/python scripts/build_episode.py \
  --episode episodes/s01-asset-classification/s01e01-forgotten-bucket.json \
  --voice-mode recorded --voice-input episodes/audio/s01e01-forgotten-bucket.m4a \
  --launch-pack-dir renders/launch-pack-case01-part1 --render-mp4

# 3. Export Voice Memos teleprompter & composite 124px right-rail Instagram UI safe-zone QA mockup
python3 scripts/export_teleprompter.py --output renders/teleprompter-export.md
.venv_audio/bin/python scripts/render_instagram_ui_mockup.py \
  --input renders/s01e01-preview-frame.png \
  --episode episodes/s01-asset-classification/s01e01-forgotten-bucket.json \
  --output renders/s01e01-ig-ui-qa.png

# 4. Run --publish-ready gate, 31-test suite, DOM audit & sanitized GitHub Pages export
python3 scripts/validate_episode.py episodes/ --publish-ready
python3 -m unittest discover -s tests -v
cd engine && npm run typecheck && npm run uat:dom && cd ..
python3 scripts/export_sanitized_pages.py --src-dir docs --out-dir renders/gh-pages-bundle
```

### Starter YAML Brief — Part 1 Whodunit (`episodes/briefs/case02-part1-shaadi-qr.yaml`)

```yaml
id: s02e01-shaadi-qr-trap
season: 2
episodeNumber: 1
part: 1
title: "Shagun QR Ya Hotel Wi-Fi? Reception Par 8 Lakh Saaf!"
cyberConcept: "Quishing (Malicious QR Sticker Overlay), Rogue Hotel Wi-Fi & Scanner Traps"
caseTag: "HOTEL RECEPTION · 8 LAKH SAAF"
realIncident:
  incident: "RBI & MHA I4C 1930 Advisory (2024) Wedding Shagun QR Overlay & Rogue Wi-Fi UPI Fraud"
  year: 2024
  impact: "Tampered UPI collect/APK QR stickers over venue Shagun standees drain wedding guests"
  lesson: "Receiving Shagun never needs a UPI PIN, verify merchant name, avoid open Wi-Fi for banking, and dial 1930."
scrollStopper: { badge: "RECEPTION ALERT · 10:15 PM", text: "3 Mehmaano Ke A/c Se Rs 8,40,000 Saaf!", tone: "danger" }
plates:
  hookHero: "characters/case02-shaadi-qr.png"
  clueHero: "characters/case02-hotel-wifi.png"
  clueSecondary: "characters/case02-smart-printer.png"
  twistHero: "characters/handoff-shadow.png"
  payoffHero: "characters/kabir-closeup.png"
beats:
  hook: "Grand Hotel reception par dulha-dulhan muskura rahe the, tabhi teen mehmaano ke phone ek saath baje: Aath lakh chalis hazaar gayab! Shagun dete hi khaate khali ho gaye!"
  escalation: "Hairaani ki baat thi ki kisi ne anjaan call nahi uthaya! Ek mehmaan ne Hotel Wi-Fi joda, doosre ne lobby printer par ID scan karwayi, aur teesre ne Shagun QR scan kiya!"
  framework: "Jab Cyber Jasoos Kabir ne jaanch shuru ki, toh raaz gehra gaya. Theek das bajkar barah minute par lobby ke ek chhupe jaal ne chupke se UPI payment divert kar diya!"
  micro_payoff: "Yaad rakhiye, paise lene ke liye UPI PIN kabhi nahi lagta, aur free Wi-Fi par bank app mat kholiye! Thagi hote hi 1930 milaiye, par hotel lobby ka jaal abhi zinda tha!"
  cliffhanger_vote: "Shak ke ghere mein teen suraag hain: Hotel Reception Wi-Fi, Lobby Smart Printer, ya Shagun QR Standee! Asli jaal kaunsa hai? Neeche A, B, C comment kijiye, kyunki agle hi pal..."
suspects:
  - { key: A, name: "Hotel Reception Wi-Fi", role: "10:05 PM · Free Lounge", timestampBadge: "10:05 PM", clue: "Fake Captive Portal!", image: "characters/case02-hotel-wifi.png" }
  - { key: B, name: "Lobby Smart Printer", role: "10:08 PM · ID Check-In", timestampBadge: "10:08 PM", clue: "Cached Guest IDs!", image: "characters/case02-smart-printer.png" }
  - { key: C, name: "Shagun QR Standee", role: "10:12 PM · Stage Gate", timestampBadge: "10:12 PM", clue: "Sticker Par Fake QR!", image: "characters/case02-shaadi-qr.png" }
```

### Companion YAML Brief — Part 2 Live Poll-Branch Reveal (`pollBranches` `A / B / C`)

`compile_story_brief.py` expands `pollBranches` (`A`, `B`, `C`) with `{pct}` and `{pct_word}` Hindi number tokens and injects `previousVoteResult` automatically (later updated with live Instagram votes via `instagram_ops.py poll-tally` or `apply_poll_result.py`):

```yaml
id: s02e02-shaadi-qr-reveal
season: 2
episodeNumber: 2
part: 2
title: "Shagun QR Sticker Pardafaash — 8 Lakh Ka Asli Khel!"
cyberConcept: "Quishing Sticker Overlay & Merchant Name Verification Shield"
caseTag: "POLL REVEAL · PARDAFAASH"
previousVoteResult: { winningOption: C, percentage: 72 }
pollBranches:
  A:
    openingLine: "{pct_word} percent logon ne Hotel Reception Wi-Fi chuna, par asli gaddar stage gate ke Shagun standee par chhupa tha!"
  B:
    openingLine: "{pct_word} percent logon ne Lobby Smart Printer par shak kiya, magar aath lakh ka asli khel Shagun gate par hua!"
  C:
    openingLine: "{pct_word} percent Jasoos bilkul sahi the! Shagun QR Standee ke upar chupke se nakli collect sticker chipkaya gaya tha!"
beats:
  hook: "Bahattar percent Jasoos bilkul sahi the! Shagun QR Standee ke upar chupke se nakli collect sticker chipkaya gaya tha!"
  escalation: "CCTV mein dikha ki raat das baje ek nakli waiter ne dulhe ke QR ke upar mule account ka sticker chipka diya, jabki Wi-Fi aur printer sirf dhyaan bhatkane ke bahane the!"
  framework: "Jaise hi mehmaano ne bina naam padhe jaldi mein UPI PIN daala, paisa dulhe ke bajaye seedha fraudster ke current account mein chala gaya!"
  micro_payoff: "5-second Suraksha Kavach: QR chhu kar dekhiye kahin upar alag sticker toh nahi, PIN daalne se pehle screen par asli naam padhiye, aur thagi par turant 1930 milaiye!"
  cliffhanger_vote: "Yeh case toh sulajh gaya, par agla rahasya kaunsa kholein: Courier APK Scam, 7-Day Loan App Trap, ya SIM Swap? Neeche A, B, C comment kijiye, kyunki agle hi pal..."
suspects:
  - { key: A, name: "Courier APK Trap", role: "Case #03A · SMS Mirror", timestampBadge: "DELIVERY SMS", clue: "5MB APK Hijack!", image: "characters/golu-phone-dial.png" }
  - { key: B, name: "7-Day Loan App", role: "Case #03B · Gallery Leak", timestampBadge: "INSTANT LOAN", clue: "Contacts Access!", image: "characters/sharma-shock.png" }
  - { key: C, name: "Midnight SIM Swap", role: "Case #03C · No Network", timestampBadge: "02:10 AM", clue: "Dead Signal Bars!", image: "characters/kabir-investigating.png" }
```

## 2. Master Script & CLI Directory (All 23 Python Scripts + Engine Commands)

### Episode Authoring, Self-Healing Builder, Guide Stitcher, Voice & Validation (`10` Scripts)

| Script (`scripts/`) | Mode | Key CLI Flags / Entrypoints & Primary Output |
| :--- | :--- | :--- |
| `build_episode.py` | CLI | `--brief \| --episode`, `--output-manifest`, `--case-dir`, `--voice-mode {edge,kokoro,recorded,draft_say}`, `--voice-input`, `--launch-pack-dir`, `--max-heal-iters 3`, `--skip-dom-audit`, `--render-mp4`, `--mp4-output` -> end-to-end healed MP4 + launch copy pack + Reel cover. |
| `compile_story_brief.py` | CLI + Lib | `--brief/-b`, `--output/-o`, `--defaults data/learned_defaults.json` -> compiles 30–40 line `.yaml`/`.json` briefs (`crime_case` or `preset: guide_walkthrough`, + `pollBranches`) into validated `EpisodeManifest` JSONs. |
| `story_brief_templates.py` | Library | `build_noir_scenes`, `build_clauses`, `expand_poll_branches`, `build_post_copy`, `ensure_loop_suspension` -> pure deterministic template builders (including `preset: guide_walkthrough`) imported by `compile_story_brief.py`. |
| `self_heal_rules.py` | Library | `compute_rate_heal_adjustment`, `heal_manifest_text_guards`, `heal_dom_defects`, `generate_launch_copy_pack` -> pure deterministic speech-rate, text-guard & DOM overflow healers imported by `build_episode.py`. |
| `stitch_video_guide.py` | CLI + Lib | `--inputs <ch.mp4...>`, `--titles <title...>`, `--output <master.mp4>` -> FFmpeg `1080x1920 @ 30fps` multi-chapter MP4 stitcher with embedded `FFMETADATA1` chapter markers (`renders/guide/cyber-jasoos-automation-master-guide.mp4`). |
| `sync_episode_registry.py` | CLI + Lib | `--episodes-dir`, `--output`, `--quiet` -> auto-discovers `episodes/**/*.json` and writes `engine/src/generated/episodeRegistry.ts`. |
| `validate_episode.py` | CLI + Lib | `targets`, `--publish-ready` -> validates Draft 2020-12 JSON Schema, `42–58s` retention clock, `130–195 WPM`, hook fillers, `...` loop suspension, and commercial voice licensing. |
| `competitor_hooks.py` | CLI + Lib | `--score "<hook>"`, `--analyze-url <url>`, `--json` -> scores cold-open hooks (`0–100` across numbers, breach verbs, curiosity gap, `< 22` words & zero filler) or inspects reference URLs via `yt-dlp`. |
| `prepare_voice.py` | CLI + Lib | `--episode`, `--mode {recorded,edge,kokoro,draft}`, `--input`, `--voice`, `--rate`, `--output-dir`, `--whisper`, `--sync-manifest` -> conforms `44.1kHz` WAV (`-14 LUFS`) + word-timestamp `*.captions.json`. |
| `export_teleprompter.py` | CLI + Lib | `--output`, `--episodes-dir` -> exports Voice Memos teleprompter script (`**BOLD CAPS**` stress cues, `//` `< 250ms` breath markers & mic checklist) to untracked `renders/teleprompter-export.md`. |

### Cast Standardization, Guide Plates, 2.5D Mattes, Procedural Foley & UI Mockups (`8` Scripts)

| Script (`scripts/`) | Mode | Key CLI Flags / Entrypoints & Primary Output |
| :--- | :--- | :--- |
| `standardize_cast.py` | CLI + Lib | `--case-dir`, `--only`, `--broll`, `--auto-frame` -> locks raw `.png/.jpg/.webp` plates to `1080x1920` eye-line portraits, inpaints stray water-tank stencils & syncs `engine/public/characters/*.png`. |
| `render_guide_plates.py` | CLI | `--out-dir assets/characters/guide01/raw` -> deterministic `1080x1920` UI, YAML, CLI & Safe-Zone visual plate generator for walkthrough/explainer Reels. |
| `generate_depth_mattes.py` | CLI | `--only`, `--skip-existing`, `--qa-out` -> runs Apache-2.0 Depth-Anything-V2 (`onnx/model_fp16.onnx`) to emit `1080x1920` RGBA `fg/*.png` & blurred `540x960` `bg/*.jpg` parallax plates. |
| `generate_cinema_foley.py` | CLI | Procedural NumPy/FFmpeg synthesis of `44.1kHz` 16-bit mono noir thriller beds, USSD dial tones, bank chimes, phone vibrations & impacts in `engine/public/sfx/*.wav` (`0` sample packs). |
| `generate_sfx.py` | CLI | Deterministic Python stdlib WAV synthesizer for enterprise/SOC stingers, radar pings, blueprint whooshes & alert cues in `engine/public/sfx/*.wav`. |
| `generate_ig_brand_kit.py` | CLI | `--all`, `--episode`, `--frame`, `--output` -> renders `1080x1080` DP, `512x512` Kabir avatar, 4 `1080x1920` Story Highlight covers & `1:1` profile-grid-safe `1080x1920` Reel covers. |
| `render_instagram_ui_mockup.py` | CLI + Lib | `--input/-i`, `--inputs`, `--episode/-e`, `--output/-o`, `--avatar`, `--caption1`, `--caption2`, `--multi-shot-grid`, `--grid-cols`, `--grid-scale` -> overlays Instagram `9:16` chrome & `124px` right rail for visual QA. |
| `render_ig_mockup.py` | CLI + Lib | Concise CLI & Python import alias re-exporting `render_instagram_ui_mockup.py` (`render_mockup`, `render_multi_shot_grid`, `RIGHT_RAIL_X`). |

### Instagram Launch, Graph API, Poll Branching, Telemetry & Pages Export (`5` Scripts)

| Script (`scripts/`) | Mode | Key CLI Flags / Entrypoints & Primary Output |
| :--- | :--- | :--- |
| `instagram_ops.py` | CLI + Lib | Subcommands: `best-time`, `publish-reel` (`--episode`, `--video`, `--dry-run`), `insights` (`--media-id`), `poll-tally` (`--media-id \| --comments-file`, `--part1`, `--apply-to`), `reply-comments` (`--approve`, `--yes`), `record-metrics` (`--db`), `learn` (`--out`). |
| `ig_graph_client.py` | Library | `InstagramGraphClient` (`v22.0`) -> stdlib-only Meta Graph API client with sliding-window rate guard, resumable Reel upload, insights fallback, comment replies & token redaction. |
| `apply_poll_result.py` | CLI + Lib | `--episode`, `--winner {A,B,C}`, `--pct 1..99`, `--output` -> standalone Part 1 -> Part 2 `pollBranches` + Hindi percentage-word (`Chauhattar percent`) injector. |
| `growth_ledger.py` | CLI + Lib | `--db data/growth_ledger.sqlite3`, `--out data/learned_defaults.json` -> SQLite Reel telemetry store & empirical top-performer parameter learner (`cold_start_prior` -> `empirical_top_performers`). |
| `export_sanitized_pages.py` | CLI + Lib | `--src-dir docs`, `--out-dir <path>` -> exports static GitHub Pages bundle (`index.html`, `assets/*`, `.nojekyll`) with emails, local `/Users/...` paths & explicit Part 2 spoilers scrubbed. |

### Remotion 4 Engine Commands (`cd engine && npm run <script>`)

| Command | Underlying Execution & Gate |
| :--- | :--- |
| `npm run studio` | Launches interactive Remotion 4 timeline preview (`remotion studio src/index.ts`). |
| `npm run sync:episodes` | Runs `python3 ../scripts/sync_episode_registry.py` to refresh `src/generated/episodeRegistry.ts`. |
| `npm run typecheck` | Syncs episode registry and runs strict TypeScript check (`tsc --noEmit`). |
| `npm run uat:dom` | Runs `node scripts/uat-dom-audit.mjs` (zero-token Headless Chrome `NOIR_GRID`, `>= 20px` font floor & contrast audit). |
| `npm run render:s01e01` .. `render:s02e01` | Renders deterministic `1080x1920` @ `30fps` H.264 MP4s into `../renders/<episodeId>.mp4` (or `npx remotion render src/index.ts <id> ../renders/<id>.mp4`). |
| `npm run still:s01e01` / `still:s01e02` | Exports `1080x1920` PNG preview stills (`--frame=1575` / `--frame=1620`) for Reel cover & UI safe-zone mockups. |

## 3. Show Spec, Safe Zones, Voice Provenance & 6-Season Curriculum

### Universe, Cast & `42–58s` Noir Thriller Retention Clock (`30fps`)

- **Format & Core Loop (`Part 1 -> Community Poll -> Part 2`)**: Serialized `9:16` (`1080x1920` @ `30fps`) Hindi/Hinglish Crime-Cyber Noir Reels (`visualTheme: "noir_cinema"`, with legacy `dark_cyber` / `bright_detective` enterprise scenes supported) inside a strict **`42–58s` (`1,260–1,740` frames)** envelope at **`130–195 WPM`** (target **`160–180 WPM`**, `< 250ms` dead air). **Detective Kabir** opens mid-crime (`Rs 12,00,000` wedding account drained while the phone sat untouched in the Puja Ghar), exposes the live technical exploit (`*21*` IVR OTP call forwarding, `UPI Collect` QR sticker overlay, courier `.apk` SMS mirroring, or 7-day loan-app blackmail), delivers a 5-second **Suraksha Kavach** (`*#21#`, `##002#`, MHA I4C `1930`), and closes Part 1 on an **A / B / C** suspect poll injected into Part 2 at `T+24h..48h`.

| Phase (`ScriptPhase`) | Target Beat | Noir Production Rule & Scene Kinds | Target Retention Signal |
| :--- | :--- | :--- | :--- |
| `hook` | Cold Open (`0:00–0:04`) | Open mid-crime (`mid_breach_timestamp`), false-safety shock (`contradiction_shock`), or Part 1 voter callout (`comment_callout`). `hook.openingLine` matches `scriptSegments[0].narration` verbatim. | **3-Second Hold (`> 78%`)** |
| `escalation` | Crime Reconstruction | Compound suspect motives, timestamps & physical vs. digital clues (`detective_crime_hook`, `detective_wifi_clue`; legacy `breach_terminal`). | **15-Second Swipe Defense** |
| `framework` | Forensic Mechanism | Expose the live exploit (`*21*` IVR divert, rogue SIM ping, QR collect sticker, malicious `.apk`) via `detective_wifi_clue` / `detective_evidence_twist`. | **Avg % Viewed (`> 85%`)** |
| `micro_payoff` | Actionable 5s Shield | Deliver the 5–10s family defense (`*#21#`, `##002#`, `1930` golden-hour freeze) + verified DoT/RBI/CERT-In/I4C parallel (`realBreachParallel`). | **Bookmark Saves & Family Shares** |
| `cliffhanger_vote` | `A / B / C` Poll or Teaser | Present 3 suspect/defense cards (`detective_suspect_board`; legacy `vote_cliffhanger`) in Part 1, or resolve every clue and tease the next case in Part 2. | **Comment Depth & `> 105%` Rewatch** |

### Cold-Open Hook Archetypes, Banned Fillers & Zeigarnik Loop Suspension

- **3 Hinglish Hook Archetypes (`0:00–0:04`)**: (1) **`mid_breach_timestamp`** (`"Subah beti ki doli uthne wali thi, magar aadhi raat Sharma Ji ki cheekh goonj uthi: Arre, shaadi ke poore baarah lakh kahan gaye?!"`), (2) **`comment_callout`** (`"Chauhattar percent logon ne Pappu Chachu par shak kiya, par chhat ki asli baat suniye..."`), and (3) **`contradiction_shock`** (`"Phone shaam se Puja Ghar mein band rakha tha, na koi anjaan link chhua na OTP bataya — phir bhi baarah lakh nikal gaye!"`).
- **Swipe-Away Hook Guard & Loop Suspension Guard (`validate_episode.py`)**: Hard-rejects generic intros (`"Hey guys"`, `"Namaskar dosto"`, `"In this video"`, `"Today we will"`, `"Welcome back"`, `"Let's explore"`) and requires final `ttsClauses[-1]` + `loopBridgeText` in `noir_cinema` to end on suspended `...` (never `'.'`, `'।'`, or `'۔'`) so vocal pitch holds across the `cliffhanger_vote -> 0:00` replay seam.

### `NOIR_GRID` & Instagram Reels `124px` Right-Rail Safe Zones (`1080x1920`)

| Region | Pixel Coordinates (`1080x1920`) | Hard Layout & Exclusion Rule (`engine/src/theme/tokens.ts` + `uat-dom-audit.mjs`) |
| :--- | :--- | :--- |
| **Top & Bottom Exclusions** | `y: 0..185` & `y: 1480..1920` | Clear for OS status bar / Reels header (`y < 185`; ambient HUD pill permitted at `y: 108..176`) and `@cyberjasoos` handle, caption drawer & audio ticker (`y >= 1480`). |
| **Upper Stage (`y < 1000`)** | `x: 84..996`, `y: 190..999` | `912px` width (`hudTop: 198`, `stageTop: 298`) above the right-rail icon stack for full-bleed 2.5D portraits, HUD case badges & top banners. |
| **Lower Overlay Band (`y >= 1000`)** | `x: 132..948`, `y: 1000..1460` | Symmetric `816px` container keeping **`x >= 956` 100% clear** of Instagram Reels' `124px` right-rail Like / Comment / Share / Audio icons even during camera shake. |
| **Kinetic Captions & Font Floor** | `x: 132..948`, `y: 1296..1468` | Word-synced Hinglish subtitle pill (`y: 1310..1460` text, `Caption Silence Guard` active) with hard **`fontSize >= 20px`** floor across all `noir_cinema` text (`>= 18px` legacy). |

### Voice Synthesis & `--publish-ready` Commercial Licensing Matrix

| `voiceConfig.mode` | Voices / Pipeline | `engineLicense` | `--publish-ready` | Operational & Monetization Policy |
| :--- | :--- | :--- | :--- | :--- |
| `recorded` | Human narrator (`160–180 WPM` `.m4a`/`.wav`) | `OWN_VOICE` | **PASS** | Primary maximum-trust human narration (`scripts/prepare_voice.py --mode recorded`). |
| `azure_commercial` | **`ur-IN-SalmanNeural` + `hi-IN-MadhurNeural`** via Azure Speech **`F0` Free Tier (`$0`, `500K chars/mo`)** | `COMMERCIAL_API` | **PASS** | Commercial drop-in upgrade keeping the exact locked Hindi-Urdu thriller voice pair for monetized Reels/sponsorships. |
| `kokoro_neural` | Local ONNX neural voice (`voices-v1.0.bin`) | `APACHE_2_0` | **PASS** | `$0` offline Apache-2.0 commercial fallback (`--mode kokoro`). |
| `edge_neural` | **`ur-IN-SalmanNeural` + `hi-IN-MadhurNeural`** (`edge-tts`) | `EDGE_READ_ALOUD_PREVIEW` | **BLOCKED** | Locked dramatic Hindi-Urdu preview master (`56.43s` Case #01); requires `Add AI label: ON` and `$0` Azure `F0` swap once monetizing. |
| `draft_say` | macOS `say` scratch timing track | `MACOS_DRAFT` | **BLOCKED** | Local animatic timing check only; never uploaded publicly. |
| *(Banned TTS)* | Any `CC-BY-NC` voice-cloning checkpoint | `CC-BY-NC` *(Rejected)* | **BANNED** | Hard-rejected by `episodes/schema.json` and `scripts/validate_episode.py`. |

### Visual Plates (`20` PNGs), Neural Depth Mattes (`APACHE_2_0`) & `18` Procedural Foley WAVs

- **20 Standardized `1080x1920` Fictional Cast & B-Roll Plates (`assets/characters/case01/*.png` -> `engine/public/characters/*.png`)**: 100% fictional characters and staged crime-noir environments (`7` eye-line-locked `y = 36.5%` cast portraits including deterministic water-tank stencil inpainting on `golu-caught-tanki.png`, `1` upward-framed smartphone plate `golu-phone-dial.png`, `9` Lanczos-conformed narrative/Case #02 plates, and `3` crimson-centroid-locked rooftop plates).
- **20 Neural 2.5D Parallax Mattes (`engine/public/characters/{fg,bg}`)**: Generated via `onnx-community/depth-anything-v2-small` (`onnx/model_fp16.onnx`, **Apache-2.0 License**) into `1080x1920` RGBA foregrounds and pre-blurred `540x960` backgrounds.
- **18 First-Principles Procedural Foley & Score WAVs (`engine/public/sfx/*.wav`)**: Synthesized 100% mathematically via Python/NumPy/FFmpeg (`scripts/generate_cinema_foley.py`, `scripts/generate_sfx.py`) with **zero (`0`) third-party sample packs**:
  - *Underscore & Ambience (`4`)*: `dark-thriller-bed.wav`, `noir-thriller-bed.wav`, `shaadi-distant-intro.wav`, `rooftop-wind-drip.wav`.
  - *Transitions & Impacts (`4`)*: `cold-open-impact.wav`, `noir-suspect-slam.wav`, `stamp-slam.wav`, `blueprint-whoosh.wav`.
  - *Narrative, Alert & Resolution Foley (`10`)*: `puja-phone-vibrate.wav`, `ussd-dial-tones.wav`, `keypad-tap-seq.wav`, `bank-sms-chime.wav`, `cash-drain-ticks.wav`, `soc-alert-ping.wav`, `heartbeat-radar-ping.wav`, `payoff-chime.wav`, `dawn-temple-bell.wav`, `cliffhanger-tick.wav`.
- **Mandatory Platform AI Disclosure SOP**:
  1. Toggle **`AI-generated profile: ON`** under Instagram `Edit profile` (zero reach penalty per Meta policy; protects Explore/Reels eligibility for Detective Kabir's fictional persona).
  2. Toggle **`Add AI label` ("Made with AI")** ON for every Reel containing AI-generated visual plates or synthetic neural audio (and enable **"Altered or synthetic content"** on YouTube Shorts).

### 6-Season, 24-Episode Case Curriculum & Teleprompter Export

Flagship consumer `noir_cinema` cases (**Case #01 Wedding `Rs 12L` `*21*` Call-Forwarding Two-Parter** in `s01e01`–`s01e02`, followed by **Shagun QR Collect Inversion**, **Courier `.apk` SMS Mirroring**, **7-Day Loan-App Blackmail**, and **Evil-Twin Hotel Wi-Fi / Smart Printer Pivots**) run side-by-side with the 6-season, 24-episode cyber-defense & enterprise breach curriculum:

| Season | Theme | 4-Episode Arc (`Episode ID` -> Core Exploit / Real-World Parallel -> `A / B / C` Cliffhanger) |
| :--- | :--- | :--- |
| **Season 1** | **Consumer Cyber-Noir & Shadow Asset Exposure** | **S01E01** (`s01e01-forgotten-bucket`: Wedding `Rs 12L` `*21*` OTP Divert / Shadow Bucket · DoT USSD & Capital One) -> **S01E02** (`s01e02-crown-jewels`: Live Poll `%` Reveal & `*#21#` Kavach / 4-Tier Crown Jewels · Equifax) -> **S01E03** (`s01e03-lobby-printer-pivot`: Cached AD Printer Pivot · Casino IoT & Target HVAC) -> **S01E04** (`s01e04-automated-cmdb-shield`: Continuous Auto-Discovery & Micro-Segmentation · MGM Hybrid Sprawl). |
| **Season 2** | **Risk Trade-Offs & Third-Party Cascades** | **S02E01** (`s02e01-the-100k-gamble`: `CVSS != Business Risk` `ALE = SLE x ARO` · Target POS) -> **S02E02** (`s02e02-insurance-fine-print`: Cyber Insurance Warranty Exclusions · NotPetya) -> **S02E03** (`s02e03-four-risk-moves`: Mitigate / Transfer / Accept / Avoid · Uber Governance) -> **S02E04** (`s02e04-vendor-trojan-cascade`: 3rd/4th-Party Webhook Cascade · MOVEit / Okta). |
| **Season 3** | **Identity, SIM/MFA & Zero-Trust Segmentation** | **S03E01** (`s03e01-mfa-fatigue-flood`: Push-Bombing vs FIDO2/Number-Matching · Contractor MFA Fatigue) -> **S03E02** (`s03e02-standing-admin-suicide`: Standing Admin Removal & 30m JIT · Helpdesk Tier-0 Breach) -> **S03E03** (`s03e03-immortal-service-keys`: 400-Day CI Token & Short-Lived OIDC · CircleCI) -> **S03E04** (`s03e04-zero-trust-segmentation`: VPN Fallacy vs East-West mTLS · Colonial Pipeline). |
| **Season 4** | **Payment Logic, Cloud SSRF & Supply Chain** | **S04E01** (`s04e01-stride-before-midnight`: Negative-Amount P2P Transfer & STRIDE · Unauthenticated API Leak) -> **S04E02** (`s04e02-metadata-ssrf-root`: `169.254.169.254` Webhook SSRF vs IMDSv2 · WAF SSRF) -> **S04E03** (`s04e03-poisoned-cicd-runner`: Malicious PR Runner & Cosign Signing · Codecov) -> **S04E04** (`s04e04-kms-snapshot-leak`: Public DB Snapshot + Co-Located KMS Key · Cloud Key Leak). |
| **Season 5** | **First 60 Minutes of Ransomware & Golden-Hour Freeze** | **S05E01** (`s05e01-ir-first-15-minutes`: Minute `00–15` Silent EDR Containment & RAM Forensics · Change Healthcare) -> **S05E02** (`s05e02-containment-freeze`: Minute `15–30` Domain Controller Isolation vs `$22M` Payroll · Travelex) -> **S05E03** (`s05e03-immutable-backups`: Minute `30–45` `3-2-1-1-0` WORM Object Lock · Rackspace) -> **S05E04** (`s05e04-extortion-clock`: Minute `45–60` Double Extortion & Materiality Clock · MGM vs Caesars). |
| **Season 6** | **Agentic & Synthetic Fraud Security** | **S06E01** (`s06e01-indirect-prompt-injection`: Hidden Invoice Prompt Injection & Deterministic Caps) -> **S06E02** (`s06e02-shadow-model-leak`: Source-Code Paste Leak & Zero-Retention DLP · Samsung) -> **S06E03** (`s06e03-excessive-agency`: OWASP LLM06 Tool Escalation & Cryptographic HITL) -> **S06E04** (`s06e04-rag-permission-bleed`: Vector-Store ACL Inheritance & Query-Time RBAC). |

### Season 2 (`NovaPay`) Quantitative Risk & Supply-Chain Blueprints (`48–54s` @ `165 WPM`)

Enterprise Season 2 episodes run a 6-scene Remotion sequence (`comment_spotlight -> breach_terminal -> risk_heatmap -> network_attack_graph -> payoff_proof_card -> vote_cliffhanger`):
- **S02E01 (`s02e01-the-100k-gamble` — *The $100K CISO Gamble*)**: Proves `CVSS != Risk` via `Likelihood x Impact` (`ALE`) anchored to **Target (2013, `$292M`)**; closes on `$40K` budget left for a `$900K` Fraud Engine (**A** Virtual Patch Mitigate, **B** `$35K` Insurance Transfer, **C** Shut Signups Avoid).
- **S02E02 (`s02e02-insurance-fine-print` — *The Cyber Insurance Trap*, `51s`)**: Opens on `38%` choosing Option B (`$35K` Insurance) as Clause 19.4 voids `$2M` payout over unpatched known CVEs (while Option C burns `$1.2M/wk`). Walks `AV $3M x EF 50% = $1.5M SLE`, `ARO 0.60 -> $900K ALE`, and `$40K` WAF/mTLS virtual patch cutting `ARO -> 0.09` (`ALE -> $135K`, `Control ROI = (ALE_before - ALE_after) - Cost = $725K` net reduction + **Mondelez / NotPetya `$100M+`** claim disputes). Votes on residual `$135K` 60-day gap (**A** Hide, **B** Formal CFO Risk Acceptance + 60d SLA, **C** Raid Prod Devs).
- **S02E03 (`s02e03-four-risk-moves` — *Mitigate, Transfer, Accept, or Kill It?*, `51s`)**: Opens on `82%` logging CFO + CISO Risk Register `#RR-204` (`Expires: 60d`, Jira escalation; `9%` silent hide = **Uber `$148M`** governance failure). Maps all 4 treatments (Checkout `MITIGATE`, Tail `TRANSFER`, Dead FTP `AVOID`, 60d Gap `ACCEPT`) until a SOC-2 KYC vendor pushes Friday `4:55 PM` `VeriFast-KYC-SDK v4.9.2` (**A** Auto-Deploy, **B** Pin Version + Egress Sandbox, **C** Rip Out Vendor).
- **S02E04 (`s02e04-vendor-trojan-cascade` — *Season Finale: The Trusted Vendor Trojan*, `52s`)**: Opens on `74%` pinning hashes + egress sandboxing—dropping DNS exfil to `cdn-metrics-verify[.]io` after a hijacked 4th-party CI runner (`19%` trusted a 9-month-old SOC-2 PDF; **MOVEit / Okta `2,700+` orgs, `$10B+`**). Bridges to **Season 3 IAM** when a contractor token shows `*:*` Admin rights (**A** Weekly Password Rotation, **B** Ephemeral JIT + Least Privilege, **C** Office IP Allowlist).

- **On-Demand Teleprompter Export**: Run `python3 scripts/export_teleprompter.py` to write untracked `renders/teleprompter-export.md` (`**BOLD CAPS**` emphasis cues, `//` `< 250ms` breath markers & `6 inches off-axis` Voice Memos mic checklist).

## 4. Hybrid Instagram Launch, Active Case Ops & Part 1 -> Part 2 Poll Loop

### Brand Assets, Anti-Spoiler Story Highlights & IST Prime-Time Windows

- **Brand Kit (`scripts/generate_ig_brand_kit.py --all`)**: `assets/brand/thecyberjasoos-dp-1080.png` (`1080x1080`), `engine/public/brand/kabir-avatar.png` (`512x512`), 4 Story Highlight covers (`assets/brand/highlight-{cases,polls,kavach,1930}.png`, `1080x1920`), and `1:1`-safe Reel covers (`renders/s01e01-reel-cover.png`, `renders/s01e02-reel-cover.png`, `1080x1920`). Publish **`Cases`** and **`Polls`** with Part 1; hold **`5s Kavach`** and **`1930 Help`** until **Part 2** so `*#21#` never spoils the Part 1 mystery early.
- **IST Upload Windows (`instagram_ops.py best-time`)**: Primary Prime-Time **`7:30 PM – 8:45 PM IST`** (target **`7:45 PM IST`**, Tue/Thu & Sat/Sun); Secondary Part 2 Poll-Reveal **`12:30 PM IST`** or **`7:45 PM IST`** at `T+24h..48h` (if `< 8–10` votes at `T+24h`, wait until `T+48h` and combine Reel comments + Story Poll taps).

### `T-5m..T+45m` Hybrid Launch (`85% Mac Web + 15% Android`) & Socratic Replies

1. **`T-5m` (Mac Web Upload)**: Drag `1080x1920` MP4 onto `instagram.com` -> **set Crop strictly to `Original (9:16)`** -> upload `renders/<id>-reel-cover.png` -> paste `postCopy.instagramCaption` + `postCopy.hashtags` (`POST_COPY_AND_PINNED_COMMENT.txt`) -> enable `Add AI label` -> Publish at `7:45 PM IST`.
2. **`T+0m` (Mac Ballot -> Android Pin & AI Label)**: Paste `postCopy.pinnedCommentVote` as first comment on Mac Web (2s, zero phone typing), then on Android long-press -> **Pin**, and confirm `⋮ -> Edit -> Add AI label: ON` if desktop hid the toggle.
3. **`T+3m` (Android 3-Option Story Poll Sticker)**: Tap `Share -> Add to story` -> select **3-Option `Poll` Sticker** (`Poll` -> `Add another option`, `<= 22` chars/choice: `A: Pados Ka Golu`, `B: Ramu Kaka`, `C: Pappu Chachu` — never `Quiz`, which marks one answer green) -> save to `Polls` Highlight.
4. **`T+5m..T+45m` (Socratic Hinglish Voter Replies)**: Never spoil Part 2; challenge each voter with a 1-sentence counter-clue (and reply empathetically pointing to `1930` on real fraud losses):
   - **Votes `A` (Golu)**: `"Golu ne 7:40 PM phone zaroor liya, par *21* log theek 7:42 PM ka hai jab Puja Ghar ke paas Ramu Kaka khade the — phir A kaise?"`
   - **Votes `B` (Ramu Kaka)**: `"Kaka ki jeb mein SIM packet mila, magar 11:25 PM par chhat ke andhere mein fusfusa kaun raha tha? B par pakka lock karein?"`
   - **Votes `C` (Pappu Chachu)**: `"Chachu ne 5 lakh maange the, par shaam 7:40 PM par Sharma Ji ka unlocked phone 2 minute kisne liya tha? Ek baar phir sochiye!"`

### Live `Part 1 -> Part 2` Poll Tally, Branch Injection & Growth Learning

```bash
# 1. Inspect Part 1 insights & tally deduplicated A/B/C votes (--media-id OR offline --comments-file)
python3 scripts/instagram_ops.py insights --media-id <PART1_MEDIA_ID>
python3 scripts/instagram_ops.py poll-tally \
  --media-id <PART1_MEDIA_ID> \
  --part1 episodes/s01-asset-classification/s01e01-forgotten-bucket.json \
  --apply-to episodes/s01-asset-classification/s01e02-crown-jewels.json
# Or inject manual combined Reel + Story Poll % directly:
python3 scripts/apply_poll_result.py --episode episodes/s01-asset-classification/s01e02-crown-jewels.json --winner C --pct 74

# 2. Post human-approved Socratic replies, rebuild Part 2 voice/MP4 & log telemetry into SQLite
python3 scripts/instagram_ops.py reply-comments --media-id <PART1_MEDIA_ID> --part1 episodes/s01-asset-classification/s01e01-forgotten-bucket.json --approve
.venv_audio/bin/python scripts/build_episode.py --episode episodes/s01-asset-classification/s01e02-crown-jewels.json --voice-mode recorded --voice-input episodes/audio/s01e02-crown-jewels.m4a --render-mp4
python3 scripts/instagram_ops.py record-metrics --episode episodes/s01-asset-classification/s01e01-forgotten-bucket.json --media-id <PART1_MEDIA_ID> --poll-votes 42 --posted-hour-ist 20
python3 scripts/instagram_ops.py learn --out data/learned_defaults.json
```

## 5. One-Time Account Privacy & $0 Meta Graph API Setup

### Android `15%` Mobile Trust Anchor, Dedicated Mac Chrome Profile & Handle Matrix

1. **Android App Signup (`realcyberjasoos@gmail.com`)**:
   - Register inside the official Android Instagram app over clean residential Wi-Fi or Indian mobile carrier data using **`realcyberjasoos@gmail.com`** (store credentials strictly in a password manager; never commit secrets or tokens).
   - Decline Android Contacts permission (`Don't allow`), skip Instagram Contact Sync, and keep the account **isolated** from any personal Meta Accounts Center.
   - Enable **Authenticator-App 2FA** (`Settings and activity -> Accounts Center -> Password and security -> Two-factor authentication`) directly on **Android** (brand-new desktop logins trigger Meta's `"You can't make this change at the moment"` security block).
   - Toggle `Data Saver: OFF` and **`Upload at highest quality: ON`** (`Settings and activity -> Data usage and media quality`), switch to **Professional -> Creator** (`Category: Reel creator` or `Digital creator`, **`Show category on profile`: UNCHECKED**), and add external link `https://cybercrime.gov.in` (`Report Fraud: 1930 / cybercrime.gov.in`).
2. **Dedicated Mac Chrome Profile (`85%` Upload & Copy Desk)**: Create a dedicated non-Incognito Chrome Profile so trusted session cookies persist across `https://www.instagram.com` uploads, set `assets/brand/thecyberjasoos-dp-1080.png`, paste the `< 30`-char SEO Name + `<= 150`-char Bio below, and toggle **`AI-generated profile: ON`**.

| Field | Primary Selection | Vetted Backups (Priority Order) | Search & UI Cap Rule |
| :--- | :--- | :--- | :--- |
| **Handle (`@username`)** | `@cyberjasoos` *(Registered)* | 1. `@thecyberjasoos`<br>2. `@realcyberjasoos` *(1:1 match with `realcyberjasoos@gmail.com`)*<br>3. `@thecyberjasoos.in`<br>4. `@askcyberjasoos` | Locked for 14 days after 2 changes; matches end-card & `postCopy`. |
| **SEO Name (`< 30` chars)** | `Cyber Jasoos \| Cyber Crime` | `Cyber Jasoos \| Scam Cases` | Strictly `< 30` chars (`26` & `25` chars); indexed in Instagram keyword search. |

- **3 Ready-to-Paste Hinglish Bios (`<= 150` Chars)**:
  - **Option A (Recommended Whodunit — `119 / 150` chars)**: `Asli Cyber Fraud Cases · 60s Rahasya` / `Saboot Dekho — A, B ya C Gaddar Pehchano!` / `5-Sec Suraksha Kavach · Cyber Help: 1930`
  - **Option B (Cyber Rakshak — `121 / 150` chars)**: `Kabir Ke Saath Asli Cyber Scam Investigation` / `Har Case Mein Chhupa Suraag + 10s Bachav Shield` / `Fraud Report: 1930 · Follow!`
  - **Option C (Minimalist Noir — `106 / 150` chars)**: `60s Hindi Cyber-Noir Whodunit` / `3 Shaq Ke Ghere · 1 Asli Gaddar — Comment A/B/C` / `5s Mobile Shield · Dial 1930`

### 5-Minute `$0` Official Meta Graph API `v22.0` Setup (No Facebook Page Needed)

1. Open `https://developers.facebook.com` -> Create **Business** App (`CyberJasoosOps`) -> add **Instagram -> API setup with Instagram login**.
2. Add `@cyberjasoos` under **App Roles -> Roles -> Instagram Testers**, then accept on Android under `Settings and activity -> Website permissions -> Apps and websites -> Tester Invites`.
3. Generate an Instagram User Token with `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_comments`, and `instagram_business_manage_insights`, and export `IG_ACCESS_TOKEN` + `IG_USER_ID` in untracked shell env vars (`scripts/ig_graph_client.py` enforces sliding-window rate limits, `>= 2.2s` reply spacing, and automatic token redaction on errors).
