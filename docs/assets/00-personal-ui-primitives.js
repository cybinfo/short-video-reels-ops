/* ==========================================================================
 * AUTO-GENERATED / SYNCED BY ClaudeCode/shared/personal-ui/sync-personal-ui.mjs
 * Source of Truth: /Users/rajat.seth/Desktop/ClaudeCode/shared/personal-ui/personal-ui-primitives.js
 * Shared runtime JS primitives across Personal apps (Family Office & ManageKar).
 * ========================================================================== */

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

  const PersonalUIPrimitives = {
    isLoopbackIpHost,
    redirectLoopbackIpToLocalhostForPasskey,
    formatPaiseINR,
    shareOrCopyText,
    applyDocumentContrastFilter,
    enhanceCapturedImageFile,
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
