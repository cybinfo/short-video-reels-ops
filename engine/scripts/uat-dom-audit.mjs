#!/usr/bin/env node
import {execFileSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';

const require = createRequire(import.meta.url);
const ENGINE_DIR = path.resolve(import.meta.dirname, '..');
const ROOT_DIR = path.resolve(ENGINE_DIR, '..');
const RENDERER_DIST = path.join(ENGINE_DIR, 'node_modules', '@remotion', 'renderer', 'dist');
const {bundle} = require('@remotion/bundler');
const {getCompositions, openBrowser, renderStill} = require('@remotion/renderer');
const {setPropsAndEnv} = require(path.join(RENDERER_DIST, 'set-props-and-env.js'));
const {seekToFrame} = require(path.join(RENDERER_DIST, 'seek-to-frame.js'));
const {puppeteerEvaluateWithCatch} = require(path.join(RENDERER_DIST, 'puppeteer-evaluate.js'));
const {makeOrReuseServer} = require(path.join(RENDERER_DIST, 'prepare-server.js'));

const UAT_RENDER_DIR = path.join(ROOT_DIR, 'renders', 'uat');
const DEFAULT_REPORT_PATH = path.join(UAT_RENDER_DIR, 'dom-audit-report.json');
const SKIP_DIR_NAMES = new Set(['briefs', 'audio', '__pycache__', 'node_modules']);

function parseCliArgs(argv) {
  let episode = null;
  let report = null;
  let renderSamples = false;
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') {
      console.log('Usage: node scripts/uat-dom-audit.mjs [--episode <id_or_json_path>] [--report <output_json_path>] [--render-samples]');
      process.exit(0);
    } else if (arg === '--episode' && i + 1 < argv.length) {
      episode = argv[++i];
    } else if (arg.startsWith('--episode=')) {
      episode = arg.slice('--episode='.length);
    } else if (arg === '--report' && i + 1 < argv.length) {
      report = argv[++i];
    } else if (arg.startsWith('--report=')) {
      report = arg.slice('--report='.length);
    } else if (arg === '--render-samples') {
      renderSamples = true;
    }
  }
  return {episode, report, renderSamples};
}

function discoverEpisodeManifests(episodesRoot) {
  const discovered = [];
  function walk(curDir) {
    if (!fs.existsSync(curDir)) return;
    const entries = fs.readdirSync(curDir, {withFileTypes: true});
    for (const entry of entries) {
      const name = entry.name;
      if (name.startsWith('.') || name.endsWith('~') || name.endsWith('.tmp')) continue;
      const fullPath = path.join(curDir, name);
      if (entry.isDirectory()) {
        if (SKIP_DIR_NAMES.has(name.toLowerCase())) continue;
        walk(fullPath);
      } else if (entry.isFile()) {
        const lower = name.toLowerCase();
        if (!lower.endsWith('.json') || lower === 'schema.json' || lower.endsWith('.brief.json')) {
          continue;
        }
        try {
          const data = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
          if (data && typeof data === 'object' && typeof data.id === 'string' && Array.isArray(data.scenes)) {
            discovered.push({
              absPath: path.resolve(fullPath),
              manifest: data,
              season: Number(data.season ?? 999),
              epNum: Number(data.episode ?? data.episodeNumber ?? 999),
            });
          }
        } catch {
          // Skip unreadable or non-manifest JSON files
        }
      }
    }
  }
  walk(episodesRoot);
  discovered.sort((a, b) => a.season - b.season || a.epNum - b.epNum || a.manifest.id.localeCompare(b.manifest.id));
  return discovered;
}

function resolveTargetEpisodes(allItems, episodeArg) {
  if (!episodeArg) return allItems.map((item) => item.manifest);
  const trimmed = episodeArg.trim();
  const candCwd = path.resolve(process.cwd(), trimmed);
  const candRoot = path.resolve(ROOT_DIR, trimmed);
  const baseStem = path.basename(trimmed, '.json');
  const matched = allItems.filter(
    (item) =>
      item.manifest.id === trimmed ||
      item.manifest.id === baseStem ||
      item.absPath === candCwd ||
      item.absPath === candRoot
  );
  if (matched.length > 0) return matched.map((item) => item.manifest);
  for (const directCand of [candCwd, candRoot]) {
    if (fs.existsSync(directCand) && fs.statSync(directCand).isFile()) {
      const data = JSON.parse(fs.readFileSync(directCand, 'utf8'));
      if (data?.id && Array.isArray(data.scenes)) return [data];
    }
  }
  console.error(`Episode not found for --episode ${episodeArg}`);
  process.exit(1);
}

async function run() {
  const cli = parseCliArgs(process.argv.slice(2));
  const reportPath = cli.report ? path.resolve(process.cwd(), cli.report) : DEFAULT_REPORT_PATH;
  fs.mkdirSync(UAT_RENDER_DIR, {recursive: true});
  fs.mkdirSync(path.dirname(reportPath), {recursive: true});

  execFileSync('python3', [path.join(ROOT_DIR, 'scripts', 'sync_episode_registry.py'), '--quiet'], {
    cwd: ROOT_DIR,
    stdio: 'pipe',
  });

  const allDiscovered = discoverEpisodeManifests(path.join(ROOT_DIR, 'episodes'));
  const selectedManifests = resolveTargetEpisodes(allDiscovered, cli.episode);

  const entryPoint = path.join(ENGINE_DIR, 'src', 'index.ts');
  const bundleLocation = await bundle({
    entryPoint,
    publicDir: path.join(ENGINE_DIR, 'public'),
  });

  const browser = await openBrowser('chrome');
  const consoleErrors = [];
  const defects = [];
  const auditedScenes = [];
  const renderedSamples = new Set();
  let episodesAuditedCount = 0;

  let cleanupServerFn = null;
  const initialWatchdogMs = Math.max(60000, selectedManifests.length * 15000);
  let watchdog = setTimeout(() => {
    console.error(`UAT DOM audit timed out after ${Math.round(initialWatchdogMs / 1000)}s`);
    process.exit(2);
  }, initialWatchdogMs);
  watchdog.unref();

  try {
    const compositions = await getCompositions(bundleLocation, {
      puppeteerInstance: browser,
    });
    const compMap = new Map(compositions.map((c) => [c.id, c]));

    const srvBundle = await makeOrReuseServer(
      null,
      {
        webpackConfigOrServeUrl: bundleLocation,
        port: null,
        remotionRoot: ENGINE_DIR,
        offthreadVideoThreads: 2,
        logLevel: 'warn',
        indent: false,
        offthreadVideoCacheSizeInBytes: null,
        binariesDirectory: null,
        forceIPv4: false,
      },
      {onDownload: undefined}
    );
    cleanupServerFn = srvBundle.cleanupServer;
    const serveUrl = srvBundle.server.serveUrl;
    const offthreadPort = srvBundle.server.offthreadPort;

    const episodes = [];
    const seenIds = new Set();
    for (const manifest of selectedManifests) {
      episodes.push(manifest);
      seenIds.add(manifest.id);
    }
    if (!cli.episode) {
      for (const c of compositions) {
        const bundledManifest = c.defaultProps?.manifest;
        if (bundledManifest?.id && Array.isArray(bundledManifest.scenes) && !seenIds.has(bundledManifest.id)) {
          episodes.push(bundledManifest);
          seenIds.add(bundledManifest.id);
        }
      }
    }
    episodesAuditedCount = episodes.length;
    const dynamicWatchdogMs = Math.max(60000, episodes.length * 15000);
    clearTimeout(watchdog);
    watchdog = setTimeout(() => {
      console.error(`UAT DOM audit timed out after ${Math.round(dynamicWatchdogMs / 1000)}s`);
      process.exit(2);
    }, dynamicWatchdogMs);
    watchdog.unref();

    for (const manifest of episodes) {
      const comp = compMap.get(manifest.id) ?? (cli.episode ? compositions[0] : null);
      if (!comp) {
        defects.push({episode: manifest.id, type: 'MISSING_COMPOSITION'});
        continue;
      }
      let runtimeWords = compMap.has(manifest.id) ? (comp.defaultProps?.words ?? []) : [];
      const capRel = manifest.voiceConfig?.captionsFile ?? `audio/${manifest.id}.captions.json`;
      const capAbs = path.join(ENGINE_DIR, 'public', capRel);
      if (fs.existsSync(capAbs)) {
        try {
          runtimeWords = JSON.parse(fs.readFileSync(capAbs, 'utf8'));
        } catch {
          // Keep bundled fallback words
        }
      }
      const effectiveProps = {
        ...(comp.defaultProps ?? {}),
        manifest,
        words: runtimeWords,
        audioPublicPath: manifest.voiceConfig?.audioFile ?? `audio/${manifest.id}.wav`,
        showSafeZone: false,
      };
      const effectivePropsJson = JSON.stringify(effectiveProps);
      const effectiveDurationInFrames = Math.max(1, Math.round((manifest.durationSeconds ?? 50) * comp.fps));

      const hasBrandAvatar =
        fs.existsSync(path.join(ENGINE_DIR, 'public', 'brand', 'ciso-avatar.png')) ||
        fs.existsSync(path.join(ENGINE_DIR, 'public', 'brand', 'kabir-avatar.png'));
      const page = await browser.newPage({
        context: srvBundle.server.sourceMap,
        logLevel: 'warn',
        indent: false,
        pageIndex: 0,
        onBrowserLog: (log) => {
          if (log.type === 'error') {
            if (!hasBrandAvatar && /404|Failed to load resource/i.test(log.text || '')) {
              return;
            }
            consoleErrors.push({episode: manifest.id, text: log.text});
          }
        },
      });
      await page.setViewport({width: comp.width, height: comp.height, deviceScaleFactor: 1});

      await setPropsAndEnv({
        serializedInputPropsWithCustomSchema: effectivePropsJson,
        envVariables: {},
        page,
        serveUrl,
        initialFrame: 0,
        timeoutInMilliseconds: 15000,
        proxyPort: offthreadPort,
        retriesRemaining: 1,
        audioEnabled: false,
        videoEnabled: true,
        indent: false,
        logLevel: 'warn',
        onServeUrlVisited: () => undefined,
      });

      await puppeteerEvaluateWithCatch({
        pageFunction: (id, props, durationInFrames, fps, height, width, defaultCodec, defaultOutName) => {
          window.remotion_setBundleMode({
            type: 'composition',
            compositionName: id,
            serializedResolvedPropsWithSchema: props,
            compositionDurationInFrames: durationInFrames,
            compositionFps: fps,
            compositionHeight: height,
            compositionWidth: width,
            compositionDefaultCodec: defaultCodec,
            compositionDefaultOutName: defaultOutName,
          });
        },
        args: [
          comp.id,
          effectivePropsJson,
          effectiveDurationInFrames,
          comp.fps,
          comp.height,
          comp.width,
          comp.defaultCodec,
          comp.defaultOutName,
        ],
        frame: null,
        page,
        timeoutInMilliseconds: 15000,
      });

      // Dynamic peak-shake frame sampling for detective_crime_hook (0.0 cold open + exact cutRatios & +1.5% peak-shake frames)
      for (let sceneIndex = 0; sceneIndex < manifest.scenes.length; sceneIndex++) {
        const scene = manifest.scenes[sceneIndex];
        const isNoir = manifest.visualTheme === 'noir_cinema';
        const hookCuts = Array.isArray(scene.props?.cutRatios) && scene.props.cutRatios.length >= 2
          ? scene.props.cutRatios
          : [0.38, 0.82];
        const PEAK_SHAKE_PROBE_RATIOS = [
          0.0,
          Number(hookCuts[0].toFixed(3)),
          Number(Math.min(0.98, hookCuts[0] + 0.015).toFixed(3)),
          Number(hookCuts[1].toFixed(3)),
          Number(Math.min(0.99, hookCuts[1] + 0.015).toFixed(3)),
        ];
        const probeRatios = isNoir
          ? scene.kind === 'detective_crime_hook'
            ? PEAK_SHAKE_PROBE_RATIOS
            : scene.kind === 'detective_wifi_clue'
              ? [0.48, 0.8]
              : scene.kind === 'detective_suspect_board'
                ? [0.35, 0.9]
                : [0.8]
          : [0.8];

        for (const ratio of probeRatios) {
          const probeSec = scene.startSec + (scene.endSec - scene.startSec) * ratio;
          const probeFrame = Math.min(
            comp.durationInFrames - 1,
            Math.max(0, Math.round(probeSec * comp.fps))
          );

          await seekToFrame({
            frame: probeFrame,
            page,
            composition: comp.id,
            timeoutInMilliseconds: 15000,
            indent: false,
            logLevel: 'warn',
            attempt: 0,
          });

        const probeResult = await puppeteerEvaluateWithCatch({
          pageFunction: (sceneKind, visualTheme) => {
            // Master & Kinetic Caption Safe-Zone Box (y: 1296..1468 container; noir x: 132..948, legacy x: 140..940)
            const SAFE_ZONE = {
              left: 70,
              right: 1010,
              top: 196,
              bottom: 1475,
              hudTop: 196,
              stageTop: 296,
              stageBottom: 1276,
              captionLeft: 140,
              captionRight: 940,
              noirCaptionLeft: 132,
              noirCaptionRight: 948,
              captionTop: 1296,
              captionBottom: 1468,
              centerX: 540,
            };

            const issues = [];
            const rootFill = document.querySelector('div[style*="1080"]') || document.body;
            const allDivs = Array.from(document.querySelectorAll('div'));

            const hudRoot =
              document.querySelector('[data-role="hud-header"]') ||
              allDivs.find((d) => {
                if (d.closest('[data-ambient="true"]')) return false;
                const r = d.getBoundingClientRect();
                return Math.abs(r.top - SAFE_ZONE.hudTop) <= 10 && Math.abs(r.width - 940) <= 16;
              });

            const stageRoot =
              document.querySelector('[data-role="stage-card"]') ||
              allDivs.find((d) => {
                if (d.closest('[data-ambient="true"]')) return false;
                const r = d.getBoundingClientRect();
                const matchesStandard =
                  Math.abs(r.left - SAFE_ZONE.left) <= 16 && Math.abs(r.width - 940) <= 28;
                const matchesNoir =
                  Math.abs(r.left - 84) <= 16 && Math.abs(r.width - 912) <= 32;
                return (
                  (matchesStandard || matchesNoir) &&
                  r.top >= 285 &&
                  r.top <= 320 &&
                  r.height >= 920
                );
              });

            const captionRoot =
              document.querySelector('[data-role="word-captions"]') ||
              allDivs.find((d) => {
                if (d.closest('[data-ambient="true"]')) return false;
                const r = d.getBoundingClientRect();
                return r.top >= 1285 && r.top <= 1340 && r.width >= 760;
              });

            // Check 1: HORIZONTAL_OFF_CENTER (primary stage cards & HUD header within ±6px of x = 540px)
            if (hudRoot) {
              const hr = hudRoot.getBoundingClientRect();
              const hudCenter = (hr.left + hr.right) / 2;
              if (Math.abs(hudCenter - SAFE_ZONE.centerX) > 6) {
                issues.push({
                  code: 'HORIZONTAL_OFF_CENTER',
                  target: 'hud',
                  centerX: Math.round(hudCenter * 10) / 10,
                  box: [Math.round(hr.left), Math.round(hr.right)],
                });
              }
            }
            if (stageRoot) {
              const sr = stageRoot.getBoundingClientRect();
              const stageCenter = (sr.left + sr.right) / 2;
              if (Math.abs(stageCenter - SAFE_ZONE.centerX) > 6) {
                issues.push({
                  code: 'HORIZONTAL_OFF_CENTER',
                  target: 'stage',
                  centerX: Math.round(stageCenter * 10) / 10,
                  box: [Math.round(sr.left), Math.round(sr.right)],
                });
              }
            }

            if (visualTheme === 'noir_cinema') {
              if (hudRoot) {
                const hr = hudRoot.getBoundingClientRect();
                if (!(Math.abs(hr.left - 84) <= 3 && Math.abs(hr.right - 996) <= 3)) {
                  issues.push({
                    code: 'ASYMMETRIC_NOIR_RAIL',
                    target: 'hud',
                    box: [Math.round(hr.left), Math.round(hr.right)],
                  });
                }
              }
              if (stageRoot) {
                const sr = stageRoot.getBoundingClientRect();
                if (
                  !(
                    Math.abs(sr.left - 84) <= 3 &&
                    Math.abs(sr.right - 996) <= 3 &&
                    Math.abs(sr.left - (1080 - sr.right)) <= 3
                  )
                ) {
                  issues.push({
                    code: 'ASYMMETRIC_NOIR_RAIL',
                    target: 'stage',
                    box: [Math.round(sr.left), Math.round(sr.right)],
                  });
                }
              }
            }

            let maxStageBottom = stageRoot ? stageRoot.getBoundingClientRect().bottom : 0;
            let minCaptionTop = captionRoot ? captionRoot.getBoundingClientRect().top : 9999;

            const all = Array.from(rootFill.querySelectorAll('div, span, p, h1, h2, h3, svg'));
            for (const el of all) {
              if (el.closest('[data-ambient="true"]')) continue;

              const styleAttr = el.getAttribute('style') || '';
              if (styleAttr.includes('NaN')) {
                issues.push({code: 'NAN_STYLE', tag: el.tagName, text: (el.textContent || '').slice(0, 50)});
              }
              const cs = window.getComputedStyle(el);
              if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity || '1') < 0.05) {
                continue;
              }
              const rect = el.getBoundingClientRect();
              if (rect.width >= 1070 && rect.height >= 1910) continue; // root / camera wrapper
              if (rect.width <= 1 || rect.height <= 1) continue;

              const text = (el.textContent || '').trim();
              const isDecorativeBar = text.length === 0 && rect.height <= 24;

              if (stageRoot && stageRoot.contains(el)) {
                if (rect.bottom > maxStageBottom) maxStageBottom = rect.bottom;
              }
              if (captionRoot && captionRoot.contains(el)) {
                if (rect.top < minCaptionTop) minCaptionTop = rect.top;
              }

              // Check internal clipping on overflow:hidden containers + stage/HUD/caption root boxes
              const isExplicitBox = el === stageRoot || el === captionRoot || el === hudRoot;

              // Transform-aware iPhone Instagram Reels Right Action Rail check (rect.right <= 955 for any non-ambient element overlapping y: 1000..1480)
              if (
                visualTheme === 'noir_cinema' &&
                el !== stageRoot &&
                rect.bottom > 1000 &&
                rect.top < 1480
              ) {
                const isWideStageCard =
                  Boolean(stageRoot && stageRoot.contains(el)) && rect.width >= 760;
                const centerDelta = Math.abs((rect.left + rect.right) / 2 - SAFE_ZONE.centerX);
                if (
                  rect.right > 955 ||
                  (isWideStageCard && (rect.left < 124 || centerDelta > 6))
                ) {
                  issues.push({
                    code: 'IG_MOBILE_RIGHT_RAIL_OVERLAP',
                    right: Math.round(rect.right * 10) / 10,
                    left: Math.round(rect.left * 10) / 10,
                    centerX: Math.round(((rect.left + rect.right) / 2) * 10) / 10,
                    box: [
                      Math.round(rect.left),
                      Math.round(rect.top),
                      Math.round(rect.right),
                      Math.round(rect.bottom),
                    ],
                    sample: text.slice(0, 60),
                  });
                }
              }
              if (
                !isDecorativeBar &&
                (cs.overflowY === 'hidden' || cs.overflow === 'hidden' || isExplicitBox) &&
                el.scrollHeight > el.clientHeight + 3
              ) {
                issues.push({
                  code: 'VERTICAL_CLIP',
                  scrollH: Math.round(el.scrollHeight),
                  clientH: Math.round(el.clientHeight),
                  top: Math.round(rect.top),
                  sample: text.slice(0, 70),
                });
              }
              if (
                (cs.overflowX === 'hidden' || cs.overflow === 'hidden' || isExplicitBox) &&
                el.scrollWidth > el.clientWidth + 3
              ) {
                issues.push({
                  code: 'HORIZONTAL_CLIP',
                  scrollW: Math.round(el.scrollWidth),
                  clientW: Math.round(el.clientWidth),
                  left: Math.round(rect.left),
                  sample: text.slice(0, 70),
                });
              }

              // Check leaf text nodes against Instagram Reels 9:16 Safe Zone (caption container y: 1296..1468)
              const hasDirectText = Array.from(el.childNodes).some(
                (n) => n.nodeType === Node.TEXT_NODE && (n.textContent || '').trim().length > 0
              );
              if (hasDirectText) {
                const outOfMasterSafeZone =
                  rect.left < SAFE_ZONE.left - 4 ||
                  rect.right > SAFE_ZONE.right + 4 ||
                  rect.top < SAFE_ZONE.top - 4 ||
                  rect.bottom > SAFE_ZONE.bottom + 4;
                const stageSpill =
                  stageRoot &&
                  stageRoot.contains(el) &&
                  (rect.top < SAFE_ZONE.stageTop - 4 || rect.bottom > SAFE_ZONE.stageBottom + 4);
                const effCaptionLeft =
                  visualTheme === 'noir_cinema' ? SAFE_ZONE.noirCaptionLeft : SAFE_ZONE.captionLeft;
                const effCaptionRight =
                  visualTheme === 'noir_cinema' ? SAFE_ZONE.noirCaptionRight : SAFE_ZONE.captionRight;
                const captionSpill =
                  captionRoot &&
                  captionRoot.contains(el) &&
                  (rect.left < effCaptionLeft - 4 ||
                    rect.right > effCaptionRight + 4 ||
                    rect.top < SAFE_ZONE.captionTop - 4 ||
                    rect.bottom > SAFE_ZONE.captionBottom + 4);
                if (outOfMasterSafeZone || stageSpill || captionSpill) {
                  issues.push({
                    code: 'SAFE_ZONE_BREACH',
                    box: [
                      Math.round(rect.left),
                      Math.round(rect.top),
                      Math.round(rect.right),
                      Math.round(rect.bottom),
                    ],
                    sample: text.slice(0, 60),
                  });
                }
                if (visualTheme === 'noir_cinema') {
                  const computedFontPx = parseFloat(cs.fontSize || '20');
                  if (computedFontPx < 20) {
                    issues.push({
                      code: 'NOIR_MICRO_TEXT',
                      fontSize: computedFontPx,
                      sample: text.slice(0, 60),
                    });
                  }
                  if (rect.left < 80 || rect.right > 1000) {
                    issues.push({
                      code: 'REELS_RIGHT_RAIL_OVERLAP',
                      right: Math.round(rect.right),
                      box: [
                        Math.round(rect.left),
                        Math.round(rect.top),
                        Math.round(rect.right),
                        Math.round(rect.bottom),
                      ],
                      sample: text.slice(0, 60),
                    });
                  }
                }
              }
            }

            if (stageRoot) {
              const sr = stageRoot.getBoundingClientRect();
              for (const child of Array.from(stageRoot.querySelectorAll('div, span, p, h1, h2, h3'))) {
                if (child.closest('[data-ambient="true"]')) continue;
                const ccs = window.getComputedStyle(child);
                if (ccs.display === 'none' || ccs.visibility === 'hidden' || parseFloat(ccs.opacity || '1') < 0.05) continue;
                const cr = child.getBoundingClientRect();
                if (cr.width <= 4 || cr.height <= 4) continue;
                if (cr.left < sr.left - 1 || cr.right > sr.right + 1 || cr.top < sr.top - 1 || cr.bottom > sr.bottom + 1) {
                  issues.push({
                    code: 'STAGE_CARD_PROTRUSION',
                    box: [Math.round(cr.left), Math.round(cr.top), Math.round(cr.right), Math.round(cr.bottom)],
                    stageBox: [Math.round(sr.left), Math.round(sr.top), Math.round(sr.right), Math.round(sr.bottom)],
                    sample: (child.textContent || '').trim().slice(0, 60),
                  });
                }
              }

              const overlapArea = (a, b) =>
                Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) *
                Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));

              const svgTexts = Array.from(stageRoot.querySelectorAll('svg text'));
              const explicitNodeCards = Array.from(stageRoot.querySelectorAll('[data-node-card="true"]'));
              const graphCanvas = stageRoot.children[1];
              const graphNodes =
                explicitNodeCards.length > 0
                  ? explicitNodeCards
                  : graphCanvas
                    ? Array.from(graphCanvas.children).filter((c) => c.tagName === 'DIV')
                    : [];

              for (const st of svgTexts) {
                if (st.closest('[data-ambient="true"]')) continue;
                const tr = st.getBoundingClientRect();
                if (
                  tr.left < SAFE_ZONE.left - 4 ||
                  tr.right > SAFE_ZONE.right + 4 ||
                  tr.top < SAFE_ZONE.stageTop - 4 ||
                  tr.bottom > SAFE_ZONE.stageBottom + 4
                ) {
                  issues.push({
                    code: 'SAFE_ZONE_BREACH',
                    box: [Math.round(tr.left), Math.round(tr.top), Math.round(tr.right), Math.round(tr.bottom)],
                    sample: (st.textContent || '').trim().slice(0, 60),
                  });
                }
                const pillRectEl = st.previousElementSibling;
                if (pillRectEl && pillRectEl.tagName.toLowerCase() === 'rect') {
                  const pr = pillRectEl.getBoundingClientRect();
                  if (tr.width > pr.width - 6) {
                    issues.push({
                      code: 'HORIZONTAL_CLIP',
                      scrollW: Math.round(tr.width),
                      clientW: Math.round(pr.width),
                      left: Math.round(tr.left),
                      sample: (st.textContent || '').trim().slice(0, 70),
                    });
                  }
                }
              }

              // Check 2: GRAPH_PILL_NODE_OVERLAP on network_attack_graph scenes
              if (sceneKind === 'network_attack_graph' || explicitNodeCards.length > 0) {
                const svgRects = Array.from(stageRoot.querySelectorAll('svg rect')).filter(
                  (rEl) => !rEl.closest('defs') && !rEl.closest('[data-ambient="true"]')
                );
                for (const rEl of svgRects) {
                  const rcs = window.getComputedStyle(rEl);
                  if (rcs.display === 'none' || rcs.visibility === 'hidden' || parseFloat(rcs.opacity || '1') < 0.05) {
                    continue;
                  }
                  const pr = rEl.getBoundingClientRect();
                  if (pr.width <= 4 || pr.height <= 4) continue;
                  const siblingText =
                    rEl.nextElementSibling && rEl.nextElementSibling.tagName.toLowerCase() === 'text'
                      ? (rEl.nextElementSibling.textContent || '').trim()
                      : 'svg-pill';
                  for (const nd of graphNodes) {
                    const ncs = window.getComputedStyle(nd);
                    if (ncs.display === 'none' || ncs.visibility === 'hidden' || parseFloat(ncs.opacity || '1') < 0.05) {
                      continue;
                    }
                    const nr = nd.getBoundingClientRect();
                    const area = overlapArea(pr, nr);
                    if (area > 4) {
                      issues.push({
                        code: 'GRAPH_PILL_NODE_OVERLAP',
                        overlapArea: Math.round(area),
                        pillBox: [Math.round(pr.left), Math.round(pr.top), Math.round(pr.right), Math.round(pr.bottom)],
                        nodeBox: [Math.round(nr.left), Math.round(nr.top), Math.round(nr.right), Math.round(nr.bottom)],
                        sample: siblingText.slice(0, 60),
                      });
                    }
                  }
                }
              }
            }

            let maxLowerCardRightPx = 0;
            if (stageRoot && visualTheme === 'noir_cinema') {
              for (const node of Array.from(stageRoot.querySelectorAll('div'))) {
                const nr = node.getBoundingClientRect();
                if (nr.bottom > 1000 && nr.top < 1480 && nr.width >= 760) {
                  if (nr.right > maxLowerCardRightPx) {
                    maxLowerCardRightPx = nr.right;
                  }
                }
              }
            }

            if (stageRoot && captionRoot && maxStageBottom > minCaptionTop - 4) {
              issues.push({
                code: 'STAGE_CAPTION_OVERLAP',
                stageBottom: Math.round(maxStageBottom),
                captionTop: Math.round(minCaptionTop),
              });
            }

            return JSON.stringify({
              issues: issues.slice(0, 12),
              maxLowerCardRightPx: Math.round(maxLowerCardRightPx * 10) / 10,
            });
          },
          args: [scene.kind, manifest.visualTheme || 'cyber_dark'],
          frame: probeFrame,
          page,
          timeoutInMilliseconds: 15000,
        });

        const rawPayload = typeof probeResult === 'string' ? probeResult : probeResult?.value;
        const parsedPayload = JSON.parse(rawPayload || '{"issues":[],"maxLowerCardRightPx":0}');
        const parsedIssues = Array.isArray(parsedPayload)
          ? parsedPayload
          : parsedPayload.issues || [];
        const maxLowerCardRightPx = Number(parsedPayload.maxLowerCardRightPx || 0);

          auditedScenes.push({
            episode: manifest.id,
            sceneId: scene.id,
            sceneIndex,
            kind: scene.kind,
            frame: probeFrame,
            ratio,
            isPeakShakeProbe: isNoir && scene.kind === 'detective_crime_hook',
            maxLowerCardRightPx,
            issueCount: parsedIssues.length,
          });

          for (const issue of parsedIssues) {
            defects.push({
              ...issue,
              episode: manifest.id,
              sceneId: scene.id,
              sceneIndex,
              kind: scene.kind,
              frame: probeFrame,
              ratio,
            });
          }

          // Save 1 PNG sample per unique component kind across the full suite (or when --render-samples is set)
          const shouldRenderSamples = !cli.episode || cli.renderSamples;
          if (shouldRenderSamples && ratio >= 0.75 && !renderedSamples.has(scene.kind)) {
            renderedSamples.add(scene.kind);
            const outPng = path.join(UAT_RENDER_DIR, `sample-${scene.kind}-${manifest.id}-f${probeFrame}.png`);
            await renderStill({
              composition: comp,
              serveUrl: bundleLocation,
              puppeteerInstance: browser,
              frame: probeFrame,
              output: outPng,
              overwrite: true,
            });
          }
        }
      }
      await page.close();
    }
  } finally {
    clearTimeout(watchdog);
    if (cleanupServerFn) await cleanupServerFn(false).catch(() => {});
    await browser.close({silent: true});
  }

  const peakShakeProbes = auditedScenes.filter((s) => s.isPeakShakeProbe);
  const peakShakeMaxRightPx = peakShakeProbes.reduce(
    (acc, s) => Math.max(acc, s.maxLowerCardRightPx || 0),
    0
  );
  const report = {
    timestamp: new Date().toISOString(),
    episodeFilter: cli.episode || null,
    episodesAudited: episodesAuditedCount,
    scenesAudited: auditedScenes.length,
    peakShakeProbesCount: peakShakeProbes.length,
    peakShakeMaxRightPx,
    peakShakeRightRailLimitPx: 955,
    peakShakeProbes: peakShakeProbes.map((s) => ({
      episode: s.episode,
      sceneId: s.sceneId,
      sceneIndex: s.sceneIndex,
      frame: s.frame,
      ratio: s.ratio,
      maxLowerCardRightPx: s.maxLowerCardRightPx,
    })),
    uniqueKindsRendered: Array.from(renderedSamples),
    consoleErrorCount: consoleErrors.length,
    defectCount: defects.length,
    consoleErrors,
    defects,
  };
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
  process.exit(defects.length > 0 || consoleErrors.length > 0 ? 1 : 0);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
