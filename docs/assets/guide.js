(function () {
  var STORAGE_KEY = "cyberjasoos_launch_checks_v1";
  var THEME_KEY = "cyberjasoos_launch_theme_v1";
  var checks = Array.prototype.slice.call(document.querySelectorAll(".step-check"));
  var progFill = document.getElementById("progFill");
  var progText = document.getElementById("progText");
  var progWrap = document.getElementById("progBarWrap");

  function loadTheme() {
    try {
      var savedTheme = localStorage.getItem(THEME_KEY);
      if (savedTheme === "light" || savedTheme === "dark") {
        document.documentElement.setAttribute("data-theme", savedTheme);
      }
    } catch (e) {}
  }

  function updateProgress() {
    var doneCount = 0;
    var state = {};
    checks.forEach(function (cb) {
      var row = cb.closest(".step-item");
      if (cb.checked) {
        doneCount += 1;
        state[cb.id] = 1;
        if (row) row.classList.add("done");
      } else if (row) {
        row.classList.remove("done");
      }
    });
    var pct = checks.length ? Math.round((doneCount / checks.length) * 100) : 0;
    if (progFill) progFill.style.width = pct + "%";
    if (progWrap) progWrap.setAttribute("aria-valuenow", String(pct));
    if (progText) progText.textContent = doneCount + " / " + checks.length + " Completed (" + pct + "%)";
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {}
  }

  function copyText(txt) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(txt).catch(function () {
        fallbackCopy(txt);
      });
    }
    fallbackCopy(txt);
    return Promise.resolve();
  }

  function fallbackCopy(txt) {
    try {
      var ta = document.createElement("textarea");
      ta.value = txt;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    } catch (e) {}
  }

  try {
    var saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    checks.forEach(function (cb) {
      if (saved[cb.id]) cb.checked = true;
    });
  } catch (e) {}

  loadTheme();
  updateProgress();

  checks.forEach(function (cb) {
    cb.addEventListener("change", updateProgress);
  });

  var resetBtn = document.getElementById("resetBtn");
  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      checks.forEach(function (cb) {
        cb.checked = false;
      });
      updateProgress();
    });
  }

  var themeBtn = document.getElementById("themeBtn");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var cur = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", cur);
      try {
        localStorage.setItem(THEME_KEY, cur);
      } catch (e) {}
    });
  }

  Array.prototype.slice.call(document.querySelectorAll(".copy-btn")).forEach(function (btn) {
    var orig = btn.textContent;
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.getAttribute("data-copy"));
      if (!target) return;
      var txt = target.textContent || "";
      copyText(txt);
      btn.setAttribute("data-copied", "1");
      btn.textContent = "Copied!";
      setTimeout(function () {
        btn.removeAttribute("data-copied");
        btn.textContent = orig;
      }, 1600);
    });
  });
})();
