# Cyber Jasoos (`@cyberjasoos`) — Unified Production, Self-Healing Engine & Instagram Operations Handbook

Canonical single-source Markdown reference for **Cyber Jasoos (`@cyberjasoos`)**: show identity, `42–58s` Hindi cyber-noir retention architecture, `NOIR_GRID` `124px` right-rail safe zones, the 4-pillar deterministic self-healing engine, voice & asset provenance, the `85% Mac Web + 15% Android` Instagram launch SOP, and the 6-season case curriculum. For the interactive visual command center, open [`docs/index.html`](index.html).

## 1. Show Identity, `42–58s` Noir Retention Clock & `NOIR_GRID` Safe Zones

### Universe, Cast & Two-Part Whodunit Format

- **Format & Specs**: Serialized `9:16` (`1080x1920` @ `30fps`) Hindi/Hinglish Crime-Cyber Noir Reels (`visualTheme: "noir_cinema"`), validated strictly inside a **`42–58s` (`1,260–1,740` frames)** envelope with legacy enterprise SOC/GRC modes (`dark_cyber` / `bright_detective`) supported in the same Remotion 4 engine.
- **Core Loop (`Part 1 -> Community Poll -> Part 2`)**: Lead investigator **Detective Kabir** drops viewers directly into a high-stakes Indian household or retail cyber-fraud scene (`Rs 12,00,000` wedding account drained while the phone sat untouched in the Puja Ghar), exposes the live technical exploit on stage (`*21*` unconditional IVR OTP call forwarding, `UPI Collect` QR inversion, courier `.apk` SMS mirroring, or predatory 7-day loan-app blackmail), delivers a 5-second **Suraksha Kavach** (`*#21#`, `##002#`, MHA I4C `1930`), and closes Part 1 on three plausible **A / B / C** suspects (`Pados Ka Golu`, `Ramu Kaka`, `Pappu Chachu`). At `T+24h..48h`, the live audience vote percentage is injected into Part 2's cold open.

### The `42–58s` Noir Thriller Retention Clock (`30fps`)

Every manifest in `episodes/**/*.json` progresses through all five contiguous `scriptSegments` phases in strict chronological order at **`130–195 WPM`** (`voiceConfig.targetWpm: 145..185`, sweet spot **`160–180 WPM`**, `< 250ms` inter-clause dead air):

| Phase (`ScriptPhase`) | Target Beat | Noir Production Rule & Scene Kinds | Target Retention Signal |
| :--- | :--- | :--- | :--- |
| `hook` | Cold Open (`0:00–0:04`) | Open mid-crime (`mid_breach_timestamp`), false-safety shock (`contradiction_shock`), or Part 1 voter callout (`comment_callout`). `hook.openingLine` matches `scriptSegments[0].narration` verbatim. | **3-Second Hold (`> 78%`)** |
| `escalation` | Crime Reconstruction | Compound suspect motives, timestamps, and physical vs. digital clues (`detective_crime_hook`, `detective_wifi_clue`; legacy `breach_terminal`). | **15-Second Swipe Defense** |
| `framework` | Forensic Mechanism | Expose the live exploit (`*21*` IVR voice-OTP divert, rogue SIM ping, QR collect trap, malicious `.apk`) via `detective_wifi_clue` / `detective_evidence_twist`. | **Avg % Viewed (`> 85%`)** |
| `micro_payoff` | Actionable 5s Shield | Deliver the concrete 5–10s family defense (`*#21#`, `##002#`, `1930` golden-hour freeze) + verified DoT/RBI/CERT-In/I4C advisory (`realBreachParallel`). | **Bookmark Saves & Family Shares** |
| `cliffhanger_vote` | `A / B / C` Poll or Teaser | Present 3 suspect/defense cards (`detective_suspect_board`; legacy `vote_cliffhanger`) in Part 1, or resolve every clue and tease the next case in Part 2. | **Comment Depth & `> 105%` Rewatch** |

### Cold-Open Hook Archetypes, Banned Fillers & Zeigarnik Loop Suspension

- **3 Proven Hinglish Hook Archetypes (`0:00–0:04`)**:
  1. **`mid_breach_timestamp` (Mid-Crime Shock)**: `"Subah beti ki doli uthne wali thi, magar aadhi raat Sharma Ji ki cheekh goonj uthi: Arre, shaadi ke poore baarah lakh kahan gaye?!"`
  2. **`comment_callout` (Part 2 Live Voter Reveal)**: `"Chauhattar percent logon ne Pappu Chachu par shak kiya, par chhat ki asli baat suniye: Bhaiya mera scooter girvi rakh lo, subah bhatiji ki doli hai!"`
  3. **`contradiction_shock` (False-Safety Shatter)**: `"Phone shaam se Puja Ghar mein band rakha tha, na koi anjaan link chhua na OTP bataya — phir bhi baarah lakh nikal gaye!"`
- **Validator Hook Guard (`scripts/validate_episode.py`)**: Hard-rejects generic swipe-away openers (`"Hey guys"`, `"Namaskar dosto"`, `"In this video"`, `"Today we will"`, `"Welcome back"`, `"Let's explore"`).
- **Zeigarnik Loop Suspension Guard (`cliffhanger_vote -> 0:00`)**: Because viewers replay the final suspect board for `4–6s` while comparing `A`, `B`, and `C`, the final `ttsClauses[-1]` and `loopBridgeText` in `noir_cinema` must terminate on suspended `...` (for example, `"Neeche A, B, ya C comment kijiye — kyunki bas kuch hi ghanton baad..."`) and **never** on a pitch-dropping full stop (`'.'`, `'।'`, or `'۔'`).

### `NOIR_GRID` & Instagram Reels `124px` Right-Rail Safe Zones (`1080x1920`)

All foreground elements conform to `NOIR_GRID` (`engine/src/theme/tokens.ts`) and pass Headless Chrome DOM geometry/contrast checks (`engine/scripts/uat-dom-audit.mjs`):

| Region | Pixel Coordinates (`1080x1920`) | Hard Layout & Exclusion Rule |
| :--- | :--- | :--- |
| **Top & Bottom Exclusions** | `y: 0..185` & `y: 1480..1920` | Clear for OS status bar / Reels header (`y < 185`; ambient HUD pill permitted at `y: 108..176`) and `@cyberjasoos` handle, caption drawer & audio ticker (`y >= 1480`). |
| **Upper Stage (`y < 1000`)** | `x: 84..996`, `y: 190..999` | `912px` width (`hudTop: 198`, `stageTop: 298`) above the right-rail icon stack for full-bleed 2.5D character portraits, HUD case badges, and top banners. |
| **Lower Overlay Band (`y >= 1000`)** | `x: 132..948`, `y: 1000..1460` | Symmetric `816px` container keeping **`x >= 956` 100% clear** of Instagram Reels' `124px` right-rail Like / Comment / Share / Audio chrome even during camera shake. |
| **Kinetic Captions** | `x: 132..948`, `y: 1296..1468` | High-contrast Hinglish word-synchronized subtitle pill (`y: 1310..1460` text) centered at `x = 540` above the platform caption drawer (`Caption Silence Guard` active). |
| **Mobile Typography Floor** | `fontSize >= 20px` (`noir_cinema`) | Hard `20px` minimum across all noir badges, ambient stamps, clue metadata, captions, and poll pills (`>= 18px` on legacy scenes) on `#060A12` noir canvas. |

## 2. 4-Pillar Deterministic Self-Healing & Auto-Improvement Engine

Every stage from raw story brief to rendered launch pack and post-publish parameter tuning runs deterministically in local Python + TypeScript with zero LLM runtime dependencies:

1. **Pillar 1 — Zero-Touch Episode Registry (`scripts/sync_episode_registry.py`)**: Scans `episodes/**/*.json` and auto-generates `engine/src/generated/episodeRegistry.ts` so new episodes register in Remotion with zero manual `index.ts` edits.
2. **Pillar 2 — Auto-Calibrated `1080x1920` Cast Framing & 2.5D Mattes (`scripts/standardize_cast.py --auto-frame` + `scripts/generate_depth_mattes.py`)**: Auto-frames uncalibrated raw plates in `<case_dir>/raw/` to eye-line-locked `1080x1920` PNGs, deterministically inpaints stray third-party stencils, and generates Apache-2.0 `fg/*.png` + `bg/*.jpg` parallax depth layers.
3. **Pillar 3 — Story Brief Compiler & Closed-Loop Self-Healing Builder (`scripts/compile_story_brief.py` + `scripts/build_episode.py`)**: Compiles concise `.yaml`/`.json` briefs (seeded by `data/learned_defaults.json`) into full `EpisodeManifest` JSONs, conforms narration + word captions, iteratively self-heals timeline/WPM/schema drift (`--max-heal-iters 3`), runs `npm run uat:dom`, and packages the publish-ready MP4 + brand launch pack.
4. **Pillar 4 — SQLite Growth Telemetry Ledger & Empirical Learning (`scripts/growth_ledger.py` + `scripts/instagram_ops.py record-metrics` & `learn`)**: Persists per-Reel reach, saves, shares, skip rate, poll votes, hook pattern, and IST upload hour in local `data/*.sqlite3`, then distills top-performing duration, WPM, hook archetype, and IST slot defaults into `data/learned_defaults.json`.

### End-to-End CLI Cheat-Sheet

```bash
# 1. Conform raw cast/B-roll plates (with auto-framing), generate 2.5D depth mattes & sync Remotion registry
.venv_audio/bin/python scripts/standardize_cast.py --case-dir assets/characters/case01 --auto-frame
.venv_audio/bin/python scripts/generate_depth_mattes.py
python3 scripts/sync_episode_registry.py

# 2. Compile a story brief (applying learned defaults) OR run the single-command self-healing builder
python3 scripts/compile_story_brief.py --brief episodes/briefs/case01.yaml --defaults data/learned_defaults.json --output episodes/s01-asset-classification/s01e01-forgotten-bucket.json
.venv_audio/bin/python scripts/build_episode.py \
  --episode episodes/s01-asset-classification/s01e01-forgotten-bucket.json \
  --voice-mode recorded --voice-input episodes/audio/s01e01-forgotten-bucket.m4a \
  --launch-pack-dir renders/launch-pack-case01-part1 --render-mp4

# 3. Validate schema + --publish-ready license gate, run 31-test Python suite & Headless Chrome DOM audit
python3 scripts/validate_episode.py episodes/ --publish-ready
python3 -m unittest discover -s tests -v
cd engine && npm run typecheck && npm run uat:dom

# 4. Log post-publish Reel metrics into SQLite ledger & update data/learned_defaults.json
python3 scripts/instagram_ops.py record-metrics --episode episodes/s01-asset-classification/s01e01-forgotten-bucket.json --media-id <MEDIA_ID> --poll-votes 42 --posted-hour-ist 19
python3 scripts/instagram_ops.py learn --out data/learned_defaults.json
```

## 3. Voice, Cast, 2.5D Matte & Procedural Foley Provenance Matrix

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

## 4. Hybrid Instagram Launch & Viral Operations SOP (`85% Mac Web + 15% Android`)

### Account Hardening, Handle Matrix & `< 30`-Char SEO Name

1. **Android App Signup (`15%` Mobile Trust Anchor — `realcyberjasoos@gmail.com`)**:
   - Register inside the official Android Instagram app over clean residential Wi-Fi or Indian mobile carrier data using **`realcyberjasoos@gmail.com`** (keep credentials strictly in a password manager; never commit passwords or tokens).
   - Decline Android Contacts permission (`Don't allow`), skip Instagram Contact Sync, and keep the account **separate** from any personal Meta Accounts Center.
   - Enable **Authenticator-App 2FA** (`Settings and activity -> Accounts Center -> Password and security -> Two-factor authentication`) directly on **Android** (brand-new desktop sessions trigger Meta's `"You can't make this change at the moment"` security block).
   - Toggle `Data Saver: OFF` and **`Upload at highest quality: ON`** (`Settings and activity -> Data usage and media quality`).
   - Switch to **Professional -> Creator** (`Category: Reel creator` or `Digital creator`, **`Show category on profile`: UNCHECKED**), and add the public-service external link `https://cybercrime.gov.in` titled `Report Fraud: 1930 / cybercrime.gov.in`.
2. **Dedicated Mac Chrome Profile (`85%` Fast Upload & Copy Desk)**:
   - Create a dedicated Chrome Profile (never Incognito, so trusted session cookies persist across uploads) and log into `https://www.instagram.com`.
   - Upload `assets/brand/thecyberjasoos-dp-1080.png` (`1080x1080`), paste the `< 30`-char Name and `<= 150`-char Bio below, and toggle **`AI-generated profile: ON`**.

| Field | Primary Selection | Vetted Backups (Priority Order) | Search & UI Cap Rule |
| :--- | :--- | :--- | :--- |
| **Handle (`@username`)** | `@cyberjasoos` *(Registered)* | 1. `@thecyberjasoos`<br>2. `@realcyberjasoos` *(1:1 match with `realcyberjasoos@gmail.com`)*<br>3. `@thecyberjasoos.in`<br>4. `@askcyberjasoos` | Locked for 14 days after 2 changes; matches end-card & `postCopy`. |
| **SEO Name (`< 30` chars)** | `Cyber Jasoos \| Cyber Crime` | `Cyber Jasoos \| Scam Cases` | Strictly `< 30` chars (`26` & `25` chars); indexed in Instagram keyword search. |

### 3 Ready-to-Paste Hinglish Bios (`<= 150` Chars) & Anti-Spoiler Story Highlights

- **Bio Option A (Recommended Whodunit — `119 / 150` chars)**:
  ```text
  Asli Cyber Fraud Cases · 60s Rahasya
  Saboot Dekho — A, B ya C Gaddar Pehchano!
  5-Sec Suraksha Kavach · Cyber Help: 1930
  ```
- **Bio Option B (Cyber Rakshak Authority — `121 / 150` chars)**: `Kabir Ke Saath Asli Cyber Scam Investigation` / `Har Case Mein Chhupa Suraag + 10s Bachav Shield` / `Fraud Report: 1930 · Follow!`
- **Bio Option C (Minimalist Noir — `106 / 150` chars)**: `60s Hindi Cyber-Noir Whodunit` / `3 Shaq Ke Ghere · 1 Asli Gaddar — Comment A/B/C` / `5s Mobile Shield · Dial 1930`
- **4 Story Highlights (`1080x1920` covers in `assets/brand/highlight-*.png`)**: Publish `Cases` (`highlight-cases.png`) and `Polls` (`highlight-polls.png`) alongside Part 1; hold `5s Kavach` (`highlight-kavach.png`) and `1930 Help` (`highlight-1930.png`) until **Part 2** drops so `*#21#` does not spoil the Part 1 mystery early.

### IST Prime-Time Cadence, Hybrid Upload & Socratic Voter Replies

- **IST Upload Windows**: Primary Prime-Time **`7:30 PM – 8:45 PM IST`** (target **`7:45 PM IST`**, Tue/Thu & Sat/Sun); Secondary Part 2 Poll-Reveal **`12:30 PM IST`** or **`7:45 PM IST`** at `T+24h..48h` (if a brand-new account has `< 8–10` votes at `T+24h`, wait until `T+48h` and combine Reel comments + Story Poll taps).
- **`T-5m..T+45m` Hybrid Execution**:
  1. **`T-5m` (Mac Web Upload)**: Drag `1080x1920` MP4 onto `instagram.com` -> **set Crop strictly to `Original (9:16)`** -> upload `renders/s01e01-reel-cover.png` -> paste `postCopy.instagramCaption` + `postCopy.hashtags` -> enable `Add AI label` if shown on desktop -> Publish at `7:45 PM IST`.
  2. **`T+0m` (Mac Ballot -> Android Pin & AI Label)**: Immediately paste `postCopy.pinnedCommentVote` as the first comment on Mac Web (2 seconds, zero phone typing), then open Android -> long-press that comment -> **Pin**, and verify `⋮ -> Edit -> Add AI label: ON` if desktop hid the toggle.
  3. **`T+3m` (Android 3-Option Story Poll Sticker)**: On Android, tap `Share -> Add to story` and select the **3-Option Story `Poll` Sticker** (`Poll` -> `Add another option`, `<= 22` chars/choice: `A: Pados Ka Golu`, `B: Ramu Kaka`, `C: Pappu Chachu` — never use `Quiz`, which prematurely marks one answer green) and save to the `Polls` Highlight.
  4. **`T+5m..T+45m` (Socratic Hinglish Voter Replies)**: Never reply `"Thanks!"` or spoil Part 2; challenge every voter with a 1-sentence counter-clue (and reply empathetically by hand pointing to `1930` if a viewer shares a personal fraud loss):
     - **Votes `A` (Golu)**: `"Golu ne 7:40 PM phone zaroor liya, par *21* log theek 7:42 PM ka hai jab Puja Ghar ke paas Ramu Kaka khade the — phir A kaise?"`
     - **Votes `B` (Ramu Kaka)**: `"Kaka ki jeb mein SIM packet mila, magar 11:25 PM par chhat ke andhere mein fusfusa kaun raha tha? B par pakka lock karein?"`
     - **Votes `C` (Pappu Chachu)**: `"Chachu ne 5 lakh maange the, par shaam 7:40 PM par Sharma Ji ka unlocked phone 2 minute kisne liya tha? Ek baar phir sochiye!"`

### Official `$0` Meta Graph API & Live `Part 1 -> Part 2` Poll Branching

1. **5-Minute Setup (`developers.facebook.com`, No Facebook Page Needed)**: Create Business App (`CyberJasoosOps`) -> add **Instagram -> API setup with Instagram login** -> add `@cyberjasoos` as **Instagram Tester** and accept under Android `Settings and activity -> Website permissions -> Apps and websites -> Tester Invites` -> generate token with `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_comments`, and `instagram_business_manage_insights` -> export `IG_ACCESS_TOKEN` and `IG_USER_ID` in untracked shell env vars.
2. **Tally Part 1 Votes, Inject Winning `%` into Part 2 & Re-Render**:

```bash
# Check next IST upload slot & inspect Part 1 telemetry
python3 scripts/instagram_ops.py best-time
python3 scripts/instagram_ops.py insights --media-id <PART1_MEDIA_ID>

# Tally deduplicated A/B/C votes (Graph API --media-id OR zero-API --comments-file) & inject into Part 2 JSON
python3 scripts/instagram_ops.py poll-tally \
  --media-id <PART1_MEDIA_ID> \
  --part1 episodes/s01-asset-classification/s01e01-forgotten-bucket.json \
  --apply-to episodes/s01-asset-classification/s01e02-crown-jewels.json

# Draft/post human-approved Socratic Hinglish replies & rebuild Part 2 with matching voice
python3 scripts/instagram_ops.py reply-comments --media-id <PART1_MEDIA_ID> --part1 episodes/s01-asset-classification/s01e01-forgotten-bucket.json --approve
.venv_audio/bin/python scripts/prepare_voice.py --episode episodes/s01-asset-classification/s01e02-crown-jewels.json --mode recorded --input episodes/audio/s01e02-crown-jewels.m4a --sync-manifest
python3 scripts/validate_episode.py episodes/s01-asset-classification/s01e02-crown-jewels.json --publish-ready
```

## 5. 6-Season, 24-Episode Case Curriculum & Teleprompter Export

Flagship consumer `noir_cinema` cases (**Case #01 Wedding `Rs 12L` `*21*` Call-Forwarding Two-Parter** in `s01e01`–`s01e02`, followed by **Shagun QR Collect Inversion**, **Courier `.apk` SMS Mirroring**, **7-Day Loan-App Blackmail**, and **Evil-Twin Hotel Wi-Fi / Smart Printer Pivots**) run side-by-side with the 6-season, 24-episode cyber-defense & enterprise breach curriculum:

| Season | Theme | 4-Episode Arc (`Episode ID` -> Core Exploit / Real-World Parallel -> `A / B / C` Cliffhanger) |
| :--- | :--- | :--- |
| **Season 1** | **Consumer Cyber-Noir & Shadow Asset Exposure** | **S01E01** (`s01e01-forgotten-bucket`: Wedding `Rs 12L` `*21*` OTP Divert / Shadow Bucket · DoT USSD & Capital One) -> **S01E02** (`s01e02-crown-jewels`: Live Poll `%` Reveal & `*#21#` Kavach / 4-Tier Crown Jewels · Equifax) -> **S01E03** (`s01e03-lobby-printer-pivot`: Cached AD Printer Pivot · Casino IoT & Target HVAC) -> **S01E04** (`s01e04-automated-cmdb-shield`: Continuous Auto-Discovery & Micro-Segmentation · MGM Hybrid Sprawl). |
| **Season 2** | **Risk Trade-Offs & Third-Party Cascades** | **S02E01** (`s02e01-the-100k-gamble`: `CVSS != Business Risk` `ALE = SLE x ARO` · Target POS) -> **S02E02** (`s02e02-insurance-fine-print`: Cyber Insurance Warranty Exclusions · NotPetya) -> **S02E03** (`s02e03-four-risk-moves`: Mitigate / Transfer / Accept / Avoid · Unlogged Exception Governance) -> **S02E04** (`s02e04-vendor-trojan-cascade`: 3rd/4th-Party Webhook Cascade · MOVEit / Okta). |
| **Season 3** | **Identity, SIM/MFA & Zero-Trust Segmentation** | **S03E01** (`s03e01-mfa-fatigue-flood`: Push-Bombing vs FIDO2/Number-Matching · Contractor MFA Fatigue) -> **S03E02** (`s03e02-standing-admin-suicide`: Standing Admin Removal & 30m JIT · Helpdesk Tier-0 Breach) -> **S03E03** (`s03e03-immortal-service-keys`: 400-Day CI Token & Short-Lived OIDC · CircleCI) -> **S03E04** (`s03e04-zero-trust-segmentation`: VPN Fallacy vs East-West mTLS · Colonial Pipeline). |
| **Season 4** | **Payment Logic, Cloud SSRF & Supply Chain** | **S04E01** (`s04e01-stride-before-midnight`: Negative-Amount P2P Transfer & STRIDE · Unauthenticated API Leak) -> **S04E02** (`s04e02-metadata-ssrf-root`: `169.254.169.254` Webhook SSRF vs IMDSv2 · WAF SSRF) -> **S04E03** (`s04e03-poisoned-cicd-runner`: Malicious PR Runner & Cosign Signing · Codecov) -> **S04E04** (`s04e04-kms-snapshot-leak`: Public DB Snapshot + Co-Located KMS Key · Cloud Key Leak). |
| **Season 5** | **First 60 Minutes of Ransomware & Golden-Hour Freeze** | **S05E01** (`s05e01-ir-first-15-minutes`: Minute `00–15` Silent EDR Containment & RAM Forensics · Change Healthcare) -> **S05E02** (`s05e02-containment-freeze`: Minute `15–30` Domain Controller Isolation vs `$22M` Payroll · Travelex) -> **S05E03** (`s05e03-immutable-backups`: Minute `30–45` `3-2-1-1-0` WORM Object Lock · Rackspace) -> **S05E04** (`s05e04-extortion-clock`: Minute `45–60` Double Extortion & Materiality Clock · MGM vs Caesars). |
| **Season 6** | **Agentic & Synthetic Fraud Security** | **S06E01** (`s06e01-indirect-prompt-injection`: Hidden Invoice Prompt Injection & Deterministic Caps) -> **S06E02** (`s06e02-shadow-model-leak`: Source-Code Paste Leak & Zero-Retention DLP · Samsung) -> **S06E03** (`s06e03-excessive-agency`: OWASP LLM06 Tool Escalation & Cryptographic HITL) -> **S06E04** (`s06e04-rag-permission-bleed`: Vector-Store ACL Inheritance & Query-Time RBAC). |

### On-Demand Own-Voice Teleprompter Export (`renders/teleprompter-export.md`)

Generate an untracked Voice Memos teleprompter script (`**BOLD CAPS**` emphasis cues, `//` `< 250ms` micro-breath markers, `6 inches off-axis` mic checklist, and per-episode WPM targets) directly from live `episodes/` manifests:

```bash
python3 scripts/export_teleprompter.py
# Writes untracked renders/teleprompter-export.md (or pass --output <custom.md>)
```
