#!/usr/bin/env node
/**
 * Layer 3 E2E & Smoke Runner: Verifies docs/index.html creator skin consumption,
 * asset link integrity, and Remotion engine structure without network listeners.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..", "..");

function assert(condition, message) {
  if (!condition) {
    console.error(`[FAIL] ${message}`);
    process.exit(1);
  }
}

const indexHtmlPath = path.join(repoRoot, "docs", "index.html");
const sharedCssPath = path.join(repoRoot, "docs", "assets", "00-personal-ui-shared.css");
const guideCssPath = path.join(repoRoot, "docs", "assets", "guide.css");
const enginePkgPath = path.join(repoRoot, "engine", "package.json");
const registryPath = path.join(repoRoot, "engine", "src", "generated", "episodeRegistry.ts");

assert(fs.existsSync(indexHtmlPath), "Missing docs/index.html");
assert(fs.existsSync(sharedCssPath), "Missing docs/assets/00-personal-ui-shared.css");
assert(fs.existsSync(guideCssPath), "Missing docs/assets/guide.css");
assert(fs.existsSync(enginePkgPath), "Missing engine/package.json");
assert(fs.existsSync(registryPath), "Missing engine/src/generated/episodeRegistry.ts");

const html = fs.readFileSync(indexHtmlPath, "utf8");
assert(html.includes('data-brand="creator"'), 'docs/index.html missing data-brand="creator"');
assert(
  html.indexOf('href="assets/00-personal-ui-shared.css"') < html.indexOf('href="assets/guide.css"'),
  "00-personal-ui-shared.css must be linked right before guide.css"
);

const guideCss = fs.readFileSync(guideCssPath, "utf8");
for (const token of ["--bg-primary", "--accent-crimson", "--emerald", "--amber", "--pui-font-sans"]) {
  assert(guideCss.includes(token), `guide.css missing token mapping: ${token}`);
}

const enginePkg = JSON.parse(fs.readFileSync(enginePkgPath, "utf8"));
assert(Boolean(enginePkg.dependencies && enginePkg.dependencies.remotion), "engine/package.json missing remotion dependency");

console.log("[PASS] SocialMediaShortVideo E2E smoke verification passed (docs/index.html + Remotion engine).");
