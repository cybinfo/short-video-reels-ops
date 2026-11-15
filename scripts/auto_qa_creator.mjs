#!/usr/bin/env node
/**
 * scripts/auto_qa_creator.mjs — Unified 5-Gate Auto-QA & Self-Healing Runner for SocialMediaShortVideo
 *
 *   Gate 1: Python Unit & Self-Healing Test Suite (`python3 -m unittest discover -s tests -p "test_*.py"`)
 *   Gate 2: Episode Contract & Registry Sync Gate (`validate_episode.py --all` + `sync_episode_registry.py --check`)
 *   Gate 3: Shared Personal UI Auto-Heal & Zero-Drift Lockstep (`ensureSharedPersonalUiSynced`)
 *   Gate 4: Headless Chrome Multi-Viewport UAT (Mobile Light/Dark, Tablet, Desktop across 6 tabs + 5 ceremonies)
 *   Gate 5: Retina Screenshot Evidence Pack & Auto-Heal Telemetry Ledger (`tests/screenshots/auto-qa/`)
 */

import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  QA_VIEWPORTS,
  assertViewportErgonomics,
  attachBrowserErrorTrap,
  collectViewportErgonomics,
  ensureSharedPersonalUiSynced,
  loadPuppeteer,
  resolveChromePath,
  runGateCommand,
  verifyScreenshotEvidencePack,
  writeAutoHealTelemetryLedger,
} from "../../shared/personal-ui/personal-auto-qa-core.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const OUT_DIR = path.join(ROOT, "tests", "screenshots", "auto-qa");
const INDEX_HTML = path.join(ROOT, "docs", "index.html");
const TABS = ["factory", "setup", "ops", "arch", "gates", "cli"];

const args = new Set(process.argv.slice(2));
const uiOnly = process.env.UI_ONLY === "1" || args.has("--browser-only");
const skipBrowser = args.has("--skip-browser");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function assertCheck(cond, msg) {
  if (!cond) throw new Error(`Creator Auto-QA failed: ${msg}`);
}

async function clickVisible(page, selector) {
  const clicked = await page.evaluate((sel) => {
    const candidates = Array.from(document.querySelectorAll(sel));
    const target =
      candidates.find((el) => {
        const st = window.getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0;
      }) || candidates[0];
    if (!target) return false;
    target.scrollIntoView({ block: "center", inline: "center" });
    target.click();
    return true;
  }, selector);
  assertCheck(clicked, `Could not find visible element to click for selector: ${selector}`);
}

async function sweepAllTabs(page, viewportLabel) {
  for (const tabId of TABS) {
    await clickVisible(page, `[data-tab="${tabId}"]`);
    await sleep(60);
    const activeOk = await page.evaluate((id) => {
      const panel = document.getElementById(`panel-${id}`);
      return Boolean(panel && panel.classList.contains("active") && !panel.hasAttribute("hidden"));
    }, tabId);
    assertCheck(activeOk, `${viewportLabel} tab '${tabId}' did not activate #panel-${tabId}.active`);
    const metrics = await collectViewportErgonomics(page);
    assertCheck(metrics.brand === "creator", `${viewportLabel}:${tabId} expected brand='creator', got ${metrics.brand}`);
    assertViewportErgonomics(metrics, `${viewportLabel} [tab=${tabId}]`, { allowDocOverflowPx: 1 });
  }
}

async function main() {
  const startedAt = Date.now();
  let registryAutoHealed = false;

  if (!uiOnly) {
    runGateCommand(
      "Gate 1: Python Unit & Self-Healing Test Suite",
      'python3 -m unittest discover -s tests -p "test_*.py"',
      { cwd: ROOT },
    );

    console.log("\n▶ Gate 2: Episode Contract & Registry Sync Gate");
    try {
      execSync("python3 scripts/sync_episode_registry.py --check", { cwd: ROOT, stdio: "pipe" });
    } catch (_) {
      console.log("  ↻ Registry drift detected — auto-healing via scripts/sync_episode_registry.py...");
      execSync("python3 scripts/sync_episode_registry.py", { cwd: ROOT, stdio: "inherit" });
      registryAutoHealed = true;
    }
    runGateCommand(
      "Gate 2: Validate All Episodes & Verify Registry Lockstep",
      "python3 scripts/validate_episode.py --all && python3 scripts/sync_episode_registry.py --check",
      { cwd: ROOT },
    );
  }

  const syncResult = ensureSharedPersonalUiSynced({ autoHeal: true, target: "creator" });
  const htmlRaw = fs.readFileSync(INDEX_HTML, "utf8");
  assertCheck(htmlRaw.includes('data-brand="creator"'), 'docs/index.html missing data-brand="creator"');
  assertCheck(
    htmlRaw.includes('href="assets/00-personal-ui-shared.css"'),
    "docs/index.html missing assets/00-personal-ui-shared.css link",
  );
  assertCheck(
    htmlRaw.includes('src="assets/00-personal-ui-primitives.js"'),
    "docs/index.html missing assets/00-personal-ui-primitives.js script",
  );
  console.log("✓ Gate 3 passed (Shared Personal UI synced + creator skin verified)");

  if (skipBrowser) {
    console.log("\n✅ Creator Studio Fast Auto-QA (Gates 1-3) passed.");
    return;
  }

  console.log("\n▶ Gate 4: Headless Chrome Multi-Viewport UAT + 5 Interactive Ceremonies");
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const puppeteer = await loadPuppeteer([ROOT]);
  let browser = null;
  const expectedShots = [
    "01-creator-mobile-factory-light.png",
    "02-creator-mobile-factory-dark.png",
    "03-creator-mobile-gates-light.png",
    "04-creator-tablet-architecture.png",
    "05-creator-desktop-cli-hub.png",
  ];

  try {
    browser = await puppeteer.launch({
      executablePath: resolveChromePath(),
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
    });
    const page = await browser.newPage();
    const errorTrap = attachBrowserErrorTrap(page);
    const targetUrl = `file://${path.join(ROOT, "docs/index.html")}`;

    await page.setViewport(QA_VIEWPORTS.mobile);
    await page.goto(targetUrl, { waitUntil: "networkidle0", timeout: 20000 });
    await sleep(120);

    // Ceremony 1 & Mobile Dark Sweep across all 6 tabs
    await sweepAllTabs(page, "Mobile Dark (390x844)");
    await clickVisible(page, '[data-tab="factory"]');
    await sleep(80);
    await page.screenshot({ path: path.join(OUT_DIR, "02-creator-mobile-factory-dark.png") });

    // Ceremony 2: Theme toggle (#themeBtn -> light & dark + localStorage cj-guide-theme)
    await clickVisible(page, "#themeBtn");
    await sleep(100);
    const lightState = await page.evaluate(() => ({
      theme: document.documentElement.getAttribute("data-theme"),
      stored: localStorage.getItem("cj-guide-theme"),
    }));
    assertCheck(
      lightState.theme === "light" && lightState.stored === "light",
      `Theme toggle to light failed: ${JSON.stringify(lightState)}`,
    );
    await sweepAllTabs(page, "Mobile Light (390x844)");
    await clickVisible(page, '[data-tab="factory"]');
    await sleep(80);
    await page.screenshot({ path: path.join(OUT_DIR, "01-creator-mobile-factory-light.png") });

    await clickVisible(page, '[data-tab="gates"]');
    await sleep(80);
    await page.screenshot({ path: path.join(OUT_DIR, "03-creator-mobile-gates-light.png") });

    // Toggle back to dark and verify
    await clickVisible(page, "#themeBtn");
    await sleep(80);
    const darkState = await page.evaluate(() => ({
      theme: document.documentElement.getAttribute("data-theme"),
      stored: localStorage.getItem("cj-guide-theme"),
    }));
    assertCheck(
      darkState.theme === "dark" && darkState.stored === "dark",
      `Theme toggle back to dark failed: ${JSON.stringify(darkState)}`,
    );

    // Ceremony 3: Search filtering (#searchInput -> "Remotion", .search-match > 0, #searchClearBtn)
    await page.evaluate(() => {
      const inp = document.getElementById("searchInput");
      if (inp) {
        inp.value = "Remotion";
        inp.dispatchEvent(new Event("input", { bubbles: true }));
      }
    });
    await sleep(100);
    const searchHits = await page.evaluate(() => document.querySelectorAll(".search-match").length);
    assertCheck(searchHits > 0, `Expected .search-match > 0 for 'Remotion', got ${searchHits}`);
    await clickVisible(page, "#searchClearBtn");
    await sleep(80);
    const postClearHits = await page.evaluate(() => document.querySelectorAll(".search-match").length);
    assertCheck(postClearHits === 0, `Expected 0 .search-match after #searchClearBtn, got ${postClearHits}`);

    // Ceremony 4: Copy command ceremony (.copy-btn -> .copied class feedback)
    await clickVisible(page, '[data-tab="factory"]');
    await sleep(60);
    await clickVisible(page, ".copy-btn");
    await sleep(60);
    const hasCopiedClass = await page.evaluate(() => Boolean(document.querySelector(".copy-btn.copied")));
    assertCheck(hasCopiedClass, "Expected .copy-btn.copied class feedback after clicking .copy-btn");

    // Ceremony 5: Interactive checklist persistence (.step-check -> #setupProgressFill + cj-guide-checks-v2)
    await clickVisible(page, '[data-tab="setup"]');
    await sleep(60);
    await clickVisible(page, "#panel-setup .step-check");
    await sleep(80);
    const checkState = await page.evaluate(() => ({
      width: document.getElementById("setupProgressFill")?.style.width || "",
      stored: localStorage.getItem("cj-guide-checks-v2") || "",
    }));
    assertCheck(
      checkState.width !== "" && checkState.width !== "0%" && checkState.stored.includes("1"),
      `Checklist persistence failed: ${JSON.stringify(checkState)}`,
    );
    await clickVisible(page, "#resetBtn");
    await sleep(60);

    // Tablet (820x1180)
    await page.setViewport(QA_VIEWPORTS.tablet);
    await sleep(100);
    await sweepAllTabs(page, "Tablet (820x1180)");
    await clickVisible(page, '[data-tab="arch"]');
    await sleep(80);
    await page.screenshot({ path: path.join(OUT_DIR, "04-creator-tablet-architecture.png") });

    // Desktop (1440x900)
    await page.setViewport(QA_VIEWPORTS.desktop);
    await sleep(100);
    await sweepAllTabs(page, "Desktop (1440x900)");
    await clickVisible(page, '[data-tab="cli"]');
    await sleep(80);
    await page.screenshot({ path: path.join(OUT_DIR, "05-creator-desktop-cli-hub.png") });

    errorTrap.assertZeroErrors("Creator Studio Browser UAT");
    console.log("✓ Gate 4 passed (Mobile Light/Dark, Tablet, Desktop across 6 tabs + 5 interactive ceremonies)");

    console.log("\n▶ Gate 5: Evidence Pack & Telemetry Ledger");
    const count = verifyScreenshotEvidencePack(OUT_DIR, expectedShots);
    const ledgerPath = writeAutoHealTelemetryLedger(
      {
        app: "SocialMediaShortVideo",
        brand: "creator",
        uiOnly,
        durationMs: Date.now() - startedAt,
        registryAutoHealed,
        personalUiHealed: syncResult?.healed ?? 0,
        personalUiDrifted: syncResult?.drifted ?? 0,
        viewportsAudited: ["mobile-light", "mobile-dark", "tablet", "desktop"],
        tabsSwept: TABS,
        ceremoniesPassed: 5,
        screenshotsVerified: count,
      },
      OUT_DIR,
    );
    console.log(`✓ Gate 5 passed (${count}/${expectedShots.length} Retina PNGs + telemetry ledger at ${ledgerPath})`);
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
  console.log("\n✅ All 5 Creator Studio Auto-QA Gates passed with 0 defects.");
}

main().catch((err) => {
  console.error(`\n✗ Creator Studio Auto-QA FAILED: ${err.message || err}`);
  process.exit(1);
});
