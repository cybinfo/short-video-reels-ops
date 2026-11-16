(function initPersonalUIPrimitives() {
  "use strict";

  function isLoopbackIpHost(hostname) {
    const h = String(hostname ?? "")
      .trim()
      .toLowerCase();
    return h === "127.0.0.1" || h === "[::1]" || h === "::1";
  }

  function redirectLoopbackIpToLocalhostForPasskey(loc) {
    const locationObj =
      loc || (typeof window !== "undefined" && window.location ? window.location : null);
    if (!locationObj || !isLoopbackIpHost(locationObj.hostname)) {
      return false;
    }
    const portPart = locationObj.port ? `:${locationObj.port}` : "";
    const pathname = locationObj.pathname || "/";
    const search = locationObj.search || "";
    const hash = locationObj.hash || "";
    const targetUrl = `http://localhost${portPart}${pathname}${search}${hash}`;
    try {
      locationObj.href = targetUrl;
    } catch {}
    return true;
  }

  function formatPaiseINR(paise, showPaise = true) {
    if (paise === null || paise === undefined || Number.isNaN(Number(paise))) {
      return "NOT AVAILABLE";
    }
    const n = Math.round(Number(paise));
    const neg = n < 0;
    const absP = Math.abs(n);
    const rupees = showPaise ? Math.floor(absP / 100) : Math.round(absP / 100);
    const rem = absP % 100;
    let s = String(rupees);
    if (s.length > 3) {
      const last3 = s.slice(-3);
      let rest = s.slice(0, -3);
      const groups = [];
      while (rest.length > 0) {
        groups.unshift(rest.slice(-2));
        rest = rest.slice(0, -2);
      }
      s = groups.join(",") + "," + last3;
    }
    const prefix = neg ? "-₹" : "₹";
    return showPaise ? `${prefix}${s}.${String(rem).padStart(2, "0")}` : `${prefix}${s}`;
  }

  async function shareOrCopyText(opts) {
    const options = opts || {};
    const title = options.title !== undefined ? String(options.title) : "";
    const text = options.text !== undefined ? String(options.text) : "";
    const btnEl = options.btnEl || null;
    if (typeof navigator !== "undefined" && typeof navigator.share === "function") {
      try {
        await navigator.share({ title, text });
        return { method: "share", ok: true };
      } catch (err) {
        if (err && err.name === "AbortError") {
          return { method: "share", ok: false, aborted: true };
        }
      }
    }
    if (
      typeof navigator !== "undefined" &&
      navigator.clipboard &&
      typeof navigator.clipboard.writeText === "function"
    ) {
      try {
        await navigator.clipboard.writeText(text);
        if (btnEl) {
          const orig =
            (typeof btnEl.getAttribute === "function" && btnEl.getAttribute("data-orig-label")) ||
            (btnEl.textContent ? btnEl.textContent.trim() : "") ||
            "Share";
          if (typeof btnEl.setAttribute === "function") {
            btnEl.setAttribute("data-orig-label", orig);
          }
          btnEl.textContent = "Copied ✓";
          setTimeout(() => {
            btnEl.textContent = orig;
          }, 1500);
        }
        return { method: "clipboard", ok: true };
      } catch {}
    }
    return { method: "none", ok: false };
  }

  function applyDocumentContrastFilter(pixels, contrastFactor = 1.24) {
    if (!pixels || typeof pixels.length !== "number") {
      return pixels;
    }
    const factor = Number.isFinite(Number(contrastFactor)) ? Number(contrastFactor) : 1.24;
    for (let i = 0; i + 2 < pixels.length; i += 4) {
      for (let c = 0; c < 3; c += 1) {
        const v = pixels[i + c];
        const stretched = Math.round((v - 128) * factor + 132);
        pixels[i + c] = stretched < 0 ? 0 : stretched > 255 ? 255 : stretched;
      }
    }
    return pixels;
  }

  async function enhanceCapturedImageFile(file, contrastFactor = 1.22) {
    if (!file || typeof file.type !== "string") {
      return file;
    }
    const mime = file.type.toLowerCase();
    if (!mime.startsWith("image/") || mime === "image/svg+xml") {
      return file;
    }
    if (
      typeof document === "undefined" ||
      typeof document.createElement !== "function" ||
      typeof createImageBitmap !== "function" ||
      typeof File !== "function"
    ) {
      return file;
    }
    try {
      const bitmap = await createImageBitmap(file);
      const width = bitmap.width || 0;
      const height = bitmap.height || 0;
      if (width <= 0 || height <= 0) {
        if (typeof bitmap.close === "function") bitmap.close();
        return file;
      }
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        if (typeof bitmap.close === "function") bitmap.close();
        return file;
      }
      ctx.drawImage(bitmap, 0, 0, width, height);
      if (typeof bitmap.close === "function") bitmap.close();
      const imageData = ctx.getImageData(0, 0, width, height);
      applyDocumentContrastFilter(imageData.data, contrastFactor);
      ctx.putImageData(imageData, 0, 0);
      const blob = await new Promise((resolve) => {
        if (typeof canvas.toBlob === "function") {
          canvas.toBlob((b) => resolve(b), "image/jpeg", 0.92);
        } else {
          resolve(null);
        }
      });
      if (!blob) {
        return file;
      }
      const baseName = String(file.name || "capture.jpg").replace(/\.[^.]+$/, "");
      return new File([blob], `${baseName}.jpg`, {
        type: "image/jpeg",
        lastModified: file.lastModified || Date.now(),
      });
    } catch {
      return file;
    }
  }

  const BRAND_GEOMETRY = Object.freeze({
    K_LEFT: "M20 24.45Q19.1 24.45 18.3 25.3L14.6 29.0C12.2 31.4 8.6 30.2 8.6 26.6V25.6",
    K_RIGHT: "M31.4 25.6V26.6C31.4 30.2 27.8 31.4 25.4 29.0L21.7 25.3Q20.9 24.45 20 24.45",
    TUCK_SHADOW: "M8.6 25.0V27.0M31.4 25.0V27.0",
    M_LEFT: "M8.6 25.8V13.4C8.6 9.8 12.2 8.6 14.6 11.0L18.3 14.7Q19.1 15.55 20 15.55",
    M_RIGHT: "M20 15.55Q20.9 15.55 21.7 14.7L25.4 11.0C27.8 8.6 31.4 9.8 31.4 13.4V25.8",
    CLOSED_RIBBON:
      "M20 15.55Q20.9 15.55 21.7 14.7L25.4 11.0C27.8 8.6 31.4 9.8 31.4 13.4V26.6C31.4 30.2 27.8 31.4 25.4 29.0L21.7 25.3Q20 23.6 18.3 25.3L14.6 29.0C12.2 31.4 8.6 30.2 8.6 26.6V13.4C8.6 9.8 12.2 8.6 14.6 11.0L18.3 14.7Q19.1 15.55 20 15.55Z",
  });

  let _brandSeq = 0;
  function _escapeAttr(val) {
    return String(val ?? "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function renderBrandMarkSvg(opts) {
    const options = opts || {};
    const size = Math.max(12, Math.round(Number(options.size) || 32));
    const tone = options.tone === "light" || options.tone === "dark" ? options.tone : "auto";
    _brandSeq += 1;
    const uid = _escapeAttr(options.uid || `pui-mk-${_brandSeq}`);
    const cls = options.className ? ` ${_escapeAttr(options.className)}` : "";
    const kl = `${uid}-kl`;
    const kr = `${uid}-kr`;
    const mll = `${uid}-mll`;
    const mrl = `${uid}-mrl`;
    const mld = `${uid}-mld`;
    const mrd = `${uid}-mrd`;

    const lightM = `<g class="${tone === "auto" ? "pui-mark-m-light" : ""}">
      <path d="${BRAND_GEOMETRY.M_LEFT}" stroke="url(#${mll})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round" />
      <path d="${BRAND_GEOMETRY.M_RIGHT}" stroke="url(#${mrl})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round" />
    </g>`;
    const darkM = `<g class="${tone === "auto" ? "pui-mark-m-dark" : ""}">
      <path d="${BRAND_GEOMETRY.M_LEFT}" stroke="url(#${mld})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round" />
      <path d="${BRAND_GEOMETRY.M_RIGHT}" stroke="url(#${mrd})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round" />
    </g>`;

    return `<span class="pui-brand-mark${cls}" data-slot="personal-brand-mark" aria-hidden="true"><svg width="${size}" height="${size}" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="${kl}" x1="9" y1="30" x2="20" y2="23" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#9a3412"/><stop offset="52%" stop-color="#f97316"/><stop offset="100%" stop-color="#fde047"/></linearGradient><linearGradient id="${kr}" x1="20" y1="23" x2="31" y2="30" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#fef08a"/><stop offset="42%" stop-color="#f59e0b"/><stop offset="100%" stop-color="#c2410c"/></linearGradient><linearGradient id="${mll}" x1="8" y1="9" x2="20" y2="17" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#6366f1"/><stop offset="100%" stop-color="#312e81"/></linearGradient><linearGradient id="${mrl}" x1="19" y1="15" x2="32" y2="25" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#a855f7"/><stop offset="45%" stop-color="#6366f1"/><stop offset="100%" stop-color="#4338ca"/></linearGradient><linearGradient id="${mld}" x1="8" y1="9" x2="20" y2="17" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#818cf8"/><stop offset="100%" stop-color="#4f46e5"/></linearGradient><linearGradient id="${mrd}" x1="19" y1="15" x2="32" y2="25" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#d8b4fe"/><stop offset="45%" stop-color="#818cf8"/><stop offset="100%" stop-color="#4f46e5"/></linearGradient></defs><path d="${BRAND_GEOMETRY.K_LEFT}" stroke="url(#${kl})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round"/><path d="${BRAND_GEOMETRY.K_RIGHT}" stroke="url(#${kr})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round"/><path d="${BRAND_GEOMETRY.TUCK_SHADOW}" stroke="#7c2d12" stroke-opacity="0.42" stroke-width="5.6" stroke-linecap="round"/>${tone === "dark" ? darkM : tone === "light" ? lightM : lightM + darkM}</svg></span>`;
  }

  function renderBrandLoaderSvg(opts) {
    const options = opts || {};
    const size = Math.max(14, Math.round(Number(options.size) || 24));
    const tone = options.tone === "light" ? "light" : "dark";
    const stacked = Boolean(options.stacked);
    const label = options.label !== undefined ? String(options.label) : "";
    const ariaLabel = _escapeAttr(options.ariaLabel || label || "Loading");
    _brandSeq += 1;
    const uid = _escapeAttr(options.uid || `pui-ldr-${_brandSeq}`);
    const ci = `${uid}-ci`;
    const ca = `${uid}-ca`;
    const trackColor = tone === "light" ? "rgba(79,70,229,0.14)" : "rgba(129,140,248,0.18)";
    const indigoStops =
      tone === "light"
        ? '<stop offset="0%" stop-color="#a855f7"/><stop offset="50%" stop-color="#6366f1"/><stop offset="100%" stop-color="#312e81"/>'
        : '<stop offset="0%" stop-color="#e9d5ff"/><stop offset="50%" stop-color="#818cf8"/><stop offset="100%" stop-color="#4f46e5"/>';
    const labelHtml = label ? `<span class="pui-loader-label">${_escapeAttr(label)}</span>` : "";

    return `<span class="pui-loader${stacked ? " pui-loader--stacked" : ""}" data-slot="personal-brand-loader" role="status" aria-live="polite" aria-label="${ariaLabel}"><svg width="${size}" height="${size}" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><defs><linearGradient id="${ci}" x1="8" y1="9" x2="32" y2="25" gradientUnits="userSpaceOnUse">${indigoStops}</linearGradient><linearGradient id="${ca}" x1="9" y1="30" x2="31" y2="23" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#fef08a"/><stop offset="48%" stop-color="#f59e0b"/><stop offset="100%" stop-color="#ea580c"/></linearGradient></defs><path d="${BRAND_GEOMETRY.CLOSED_RIBBON}" pathLength="100" stroke="${trackColor}" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round"/><path d="${BRAND_GEOMETRY.CLOSED_RIBBON}" pathLength="100" stroke="url(#${ci})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="36 64" class="pui-loader-comet-indigo"/><path d="${BRAND_GEOMETRY.CLOSED_RIBBON}" pathLength="100" stroke="url(#${ca})" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="28 72" class="pui-loader-comet-amber"/></svg>${labelHtml}</span>`;
  }

  const PersonalUIPrimitives = {
    BRAND_GEOMETRY,
    isLoopbackIpHost,
    redirectLoopbackIpToLocalhostForPasskey,
    formatPaiseINR,
    shareOrCopyText,
    applyDocumentContrastFilter,
    enhanceCapturedImageFile,
    renderBrandMarkSvg,
    renderBrandLoaderSvg,
  };

  if (typeof globalThis !== "undefined") {
    globalThis.PersonalUIPrimitives = PersonalUIPrimitives;
  }
  if (typeof window !== "undefined") {
    window.PersonalUIPrimitives = PersonalUIPrimitives;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = PersonalUIPrimitives;
  }
})();
