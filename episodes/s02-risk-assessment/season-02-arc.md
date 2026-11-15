# Season 2 Blueprint — Risk Assessment & Prioritization (`NovaPay`)

## Season 2 Arc Summary (`4` Episodes · `48–54s` · `30 fps` · `9:16`)

| Episode | ID | Title | Core Framework | Real Breach Parallel | Cliffhanger Vote |
|---|---|---|---|---|---|
| **S02E01** | `s02e01-the-100k-gamble` | *The $100K CISO Gamble* | `CVSS != Risk` · `Likelihood × Impact` (`ALE`) | **Target (2013)** — `$292M` cost | `$40K` left for `$900K` Fraud Engine: **A** Mitigate, **B** Transfer, **C** Avoid |
| **S02E02** | `s02e02-insurance-fine-print` | *The Cyber Insurance Trap* | Quantitative **AV · EF · SLE · ARO · ALE** | **Mondelez / NotPetya & Fine-Print Denials** (`$100M+`) | Residual `$135K` ALE left: **A** Silent Ignore, **B** CFO Risk Acceptance + 60-Day SLA, **C** Raid Prod Budget |
| **S02E03** | `s02e03-four-risk-moves` | *Mitigate, Transfer, Accept, or Kill It?* | **4 Risk Treatments** + Formal Risk Register | **Uber (2016/2022)** Unlogged Risk & Cover-Up (`$148M+`) | SOC-2 Vendor ships midnight KYC SDK: **A** Auto-Trust SOC-2, **B** Sandbox + Scope Cap, **C** Rip Out Vendor |
| **S02E04** | `s02e04-vendor-trojan-cascade` | *Season Finale — The Trusted Vendor Trojan* | **3rd/4th-Party Supply-Chain Risk Cascade** | **MOVEit / Okta Cascade (2023)** (`2,700+` orgs, `$10B+`) | **Season 3 Bridge (IAM)**: Contractor token has `Admin *`: **A** Rotate Weekly, **B** JIT + Least Privilege, **C** IP Allowlist |

## S02E02 Blueprint — `"The Cyber Insurance Trap"` (`s02e02-insurance-fine-print`)

- **Metadata**: `durationSeconds: 51`, `fps: 30`, `voiceConfig: { mode: "draft_say", engineLicense: "OWN_VOICE", targetWpm: 165 }`
- **Real Breach Parallel**: **Cyber Underwriting Exclusion Disputes (Mondelez / Lloyd's & Unpatched Control Clauses, 2017–2023)** — `$100M+` disputed claims prove insurance never replaces baseline controls.
- **Hook (`comment_callout`)**: `51%` voted Option A (Virtual Patch) while `38%` voted Option B (`$35K` Cyber Insurance) — and NovaPay's insurer just voided coverage on Page 19 because unmitigated known exploits violate the policy warranty!

### 5-Phase Narration Script (`139` words · `163.5 WPM`)
1. **`0.0–4.5s` (`hook`)**: `"Thirty-eight percent of you bought cyber insurance last night—and Clause Nineteen just voided NovaPay's entire two-million-dollar payout."`
2. **`4.5–15.0s` (`escalation`)**: `"Underwriters refuse claims when known high-likelihood bugs sit unpatched without compensating controls. Meanwhile, shutting down signups in Option C would burn $1.2 million in weekly growth—costing more than the breach itself."`
3. **`15.0–35.0s` (`framework`)**: `"Boardroom risk runs on cold math. Asset Value of $3 million times a 50% Exposure Factor equals a $1.5 million Single Loss Expectancy. Multiply by a 0.60 Annual Rate of Occurrence to get $900K ALE. Our $40K virtual patch slashes ARO to 0.09—dropping ALE to $135K AND unlocking insurance eligibility."`
4. **`35.0–43.0s` (`micro_payoff`)**: `"From $100 million NotPetya policy battles to ransomware claim denials, insurers audit your controls before wiring a single cent."`
5. **`43.0–51.0s` (`cliffhanger_vote`)**: `"Even after virtual patching, $135K in residual risk remains until Q2's rewrite. How do you handle the gap? Vote A, B, or C."`

### 6-Scene Remotion Timeline (`0–51s`)
| Scene | Window | `kind` | Key Visual Props |
|---|---|---|---|
| `sc-01` | `0–6s` | `comment_spotlight` | `optionPicked: "B"`, `percentage: 38`, `verdictLabel: "CLAIM VOID WITHOUT CONTROLS"`, `verdictTone: "danger"` |
| `sc-02` | `6–15s` | `breach_terminal` | `POLICY_AUDIT // CLAUSE 19.4 EXCLUSION`: Known unmitigated CVE voids `$2M` rider; Option C costs `$1.2M/wk` |
| `sc-03` | `15–28s` | `risk_heatmap` | Before/After math: `AV $3M × EF 50% = $1.5M SLE`; `ARO 0.60 -> 0.09` via `$40K` WAF cuts `ALE $900K -> $135K` |
| `sc-04` | `28–35s` | `network_attack_graph` | Rate-limit + mTLS virtual patch blocks automated credential stuffing; `$135K` residual logic bug isolated |
| `sc-05` | `35–43s` | `payoff_proof_card` | Rule: `Control ROI = (ALE_before − ALE_after) − Cost` (`$725K` net risk reduction) + `$100M+` Insurance Disputes |
| `sc-06` | `43–51s` | `vote_cliffhanger` | Residual `$135K` ALE for 60 days: **A** Hide it from Board, **B** Formal CFO Risk Acceptance + 60-Day SLA, **C** Pull Prod Devs off Checkout |

## S02E03 Blueprint — `"Mitigate, Transfer, Accept, or Kill It?"` (`s02e03-four-risk-moves`)

- **Metadata**: `durationSeconds: 51`, `fps: 30`, `voiceConfig: { mode: "draft_say", engineLicense: "OWN_VOICE", targetWpm: 165 }`
- **Real Breach Parallel**: **Uber Concealed Breach & Unlogged Risk Governance Failure (2016 / 2022 Conviction)** — `$148M` settlement + executive liability when residual risk is hidden instead of formally governed.
- **Hook (`comment_callout`)**: `82%` chose Option B (Formal CFO Risk Acceptance with a 60-Day expiration timer), while `9%` who hid the residual bug committed a career-ending governance felony.

### 5-Phase Narration Script (`141` words · `165.9 WPM`)
1. **`0.0–4.5s` (`hook`)**: `"Eighty-two percent of you made the executive move—putting the CFO's signature and a sixty-day kill timer on residual risk."`
2. **`4.5–15.0s` (`escalation`)**: `"Security engineers get fired when they silently carry business risk on their own backs. When an unpatched system blows up without a logged Risk Register entry, leadership blames the CISO, never the budget."`
3. **`15.0–35.0s` (`framework`)**: `"Every cyber risk on Earth has exactly four valid treatments: Mitigate with controls when fix cost beats ALE; Transfer tail catastrophe via insurance AFTER baseline hardening; Avoid by unplugging toxic legacy features like NovaPay's dead FTP server; or formally Accept with executive sign-off and an automatic expiration date."`
4. **`35.0–43.0s` (`micro_payoff`)**: `"Uber's $148 million settlement and executive conviction proved that concealing unlogged security risk destroys companies faster than the hack itself."`
5. **`43.0–51.0s` (`cliffhanger_vote`)**: `"Friday, 4:55 PM: NovaPay's risk register is green—until our SOC-2 KYC vendor pushes an unreviewed SDK update. Vote A, B, or C."`

### 6-Scene Remotion Timeline (`0–51s`)
| Scene | Window | `kind` | Key Visual Props |
|---|---|---|---|
| `sc-01` | `0–6s` | `comment_spotlight` | `optionPicked: "B"`, `percentage: 82`, `verdictLabel: "82% LOGGED FORMAL RISK ACCEPTANCE"`, `verdictTone: "success"` |
| `sc-02` | `6–15s` | `breach_terminal` | `GRC_LEDGER // RISK REGISTER #RR-204`: Signed by CFO + CISO, `Expires: 60d`, Automated Jira Escalation armed |
| `sc-03` | `15–28s` | `risk_heatmap` | Full 4-Quadrant Treatment Map: Checkout (`MITIGATE`), Tail Catastrophe (`TRANSFER`), Dead FTP (`AVOID`), 60d Gap (`ACCEPT`) |
| `sc-04` | `28–35s` | `network_attack_graph` | Internal NovaPay nodes Green, while external `VeriFast-KYC-SDK v4.9.2` injects outbound telemetry hook at `16:55` |
| `sc-05` | `35–43s` | `payoff_proof_card` | Rule: *Never silently own business risk—Mitigate, Transfer, Avoid, or log time-boxed Executive Acceptance* + Uber `$148M` |
| `sc-06` | `43–51s` | `vote_cliffhanger` | Vendor has clean SOC-2 PDF, pushes Friday 4:55 PM update: **A** Auto-Deploy (SOC-2 Trusted), **B** Pin Version + Egress Sandbox, **C** Terminate Vendor Tonight |

## S02E04 Blueprint — `"Season Finale — The Trusted Vendor Trojan"` (`s02e04-vendor-trojan-cascade`)

- **Metadata**: `durationSeconds: 52`, `fps: 30`, `voiceConfig: { mode: "draft_say", engineLicense: "OWN_VOICE", targetWpm: 165 }`
- **Real Breach Parallel**: **MOVEit Transfer & Okta Third-Party Cascade (2023)** — `2,700+` organizations and `$10B+` in global Supply-Chain / Nth-Party fallout despite compliant audit checkboxes.
- **Hook (`comment_callout`)**: `74%` pinned the SDK version and sandboxed egress—catching a hijacked fourth-party build pipeline that `19%` auto-deployed because of a 9-month-old SOC-2 PDF!

### 5-Phase Narration Script (`142` words · `163.8 WPM`)
1. **`0.0–4.5s` (`hook`)**: `"Seventy-four percent of you froze that Friday update—stopping a supply-chain trojan that sailed straight past a clean SOC-2 certificate."`
2. **`4.5–15.0s` (`escalation`)**: `"Our KYC vendor wasn't malicious—their fourth-party CI runner got hijacked two hours earlier. Companies that trusted static annual questionnaires pulled poisoned code right into production checkout."`
3. **`15.0–35.0s` (`framework`)**: `"A SOC-2 report is a rear-view mirror snapshot, never a runtime shield. Modern Third-Party Risk Management scores vendors on Blast Radius: pin cryptographic hashes, restrict outbound egress to allowlisted domains, strip vendor tokens to minimum scope, and keep a kill-switch ready for every external integration."`
4. **`35.0–43.0s` (`micro_payoff`)**: `"In 2023, the MOVEit supply-chain cascade breached over 2,700 organizations worldwide through a single trusted third-party transfer tool."`
5. **`43.0–52.0s` (`cliffhanger_vote`)**: `"Season Two is locked—until forensics spots an internal NovaPay contractor token carrying full wildcard Admin rights. Season Three starts next: Vote A, B, or C!"`

### 6-Scene Remotion Timeline (`0–52s`)
| Scene | Window | `kind` | Key Visual Props |
|---|---|---|---|
| `sc-01` | `0–6s` | `comment_spotlight` | `optionPicked: "B"`, `percentage: 74`, `verdictLabel: "74% BLOCKED 4TH-PARTY SUPPLY TROJAN"`, `verdictTone: "success"` |
| `sc-02` | `6–15s` | `breach_terminal` | `EGRESS_SANDBOX // HASH MISMATCH`: `verifast-sdk@4.9.2` attempted DNS exfil to `cdn-metrics-verify[.]io` — DROPPED |
| `sc-03` | `15–26s` | `network_attack_graph` | `4th-Party CI` -> `3rd-Party KYC Vendor` -> `Blocked at NovaPay Pin + Egress Wall` -> `Core Ledger Untouched` |
| `sc-04` | `26–35s` | `risk_heatmap` | Vendor Risk Tiering: Runtime Egress Jail (`MITIGATE`), SLA Indemnity (`TRANSFER`), Multi-Vendor Failover (`MITIGATE`) |
| `sc-05` | `35–43s` | `payoff_proof_card` | Season 2 Master Rule: *Compliance PDFs ≠ Runtime Security; bound every vendor's blast radius* + MOVEit `2,700+` Orgs |
| `sc-06` | `43–52s` | `vote_cliffhanger` | **Season 3 Bridge (IAM & Privilege)**: Contractor token has `*:*` Admin permissions: **A** Rotate Password Weekly, **B** Just-In-Time (JIT) Ephemeral Least Privilege, **C** Office IP Allowlist |
