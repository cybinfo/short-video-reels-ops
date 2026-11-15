(function () {
  var STORAGE_KEY = "cyberjasoos_launch_checks_v1";
  var STORAGE_KEY_V2 = "cj-guide-checks-v2";
  var THEME_KEY = "cyberjasoos_launch_theme_v1";
  var THEME_KEY_V2 = "cj-guide-theme";
  var TAB_KEY = "cyberjasoos_active_tab_v1";
  var VALID_TABS = { factory: "factory", launch: "launch", ops: "launch", cli: "cli", spec: "spec", arch: "spec", setup: "setup", all: "all", gates: "all" };
  var checks = Array.prototype.slice.call(document.querySelectorAll(".step-check"));
  var progFill = document.getElementById("progFill");
  var setupProgFill = document.getElementById("setupProgressFill");
  var progText = document.getElementById("progText");
  var progWrap = document.getElementById("progBarWrap");
  var tabBtns = Array.prototype.slice.call(document.querySelectorAll("[data-tab-btn], [data-tab]"));
  var tabPanels = Array.prototype.slice.call(document.querySelectorAll("[data-tab-panel]"));
  var gatesPanel = document.getElementById("panel-gates");
  var searchInput = document.getElementById("searchInput");
  var searchClearBtn = document.getElementById("searchClearBtn");
  var searchStatus = document.getElementById("searchStatus");
  var activeTab = "factory";

  function loadTheme() {
    try {
      var savedTheme = localStorage.getItem(THEME_KEY_V2) || localStorage.getItem(THEME_KEY);
      if (savedTheme === "light" || savedTheme === "dark") {
        document.documentElement.setAttribute("data-theme", savedTheme);
      }
    } catch (e) {}
  }

  function clearSearchHidden() {
    Array.prototype.slice.call(document.querySelectorAll(".is-search-hidden")).forEach(function (el) {
      el.classList.remove("is-search-hidden");
    });
    Array.prototype.slice.call(document.querySelectorAll(".search-match")).forEach(function (el) {
      el.classList.remove("search-match");
    });
  }

  function renderTabs(viewTab) {
    var canonical = VALID_TABS[viewTab] || "factory";
    tabBtns.forEach(function (btn) {
      var btnTab = VALID_TABS[btn.getAttribute("data-tab-btn") || btn.getAttribute("data-tab")] || "factory";
      var isSel = btnTab === canonical;
      btn.setAttribute("aria-selected", isSel ? "true" : "false");
      btn.classList.toggle("active", isSel);
    });
    tabPanels.forEach(function (panel) {
      var pName = VALID_TABS[panel.getAttribute("data-tab-panel")] || panel.getAttribute("data-tab-panel");
      if (canonical === "all" || pName === canonical) {
        panel.removeAttribute("hidden");
        panel.classList.add("active");
      } else {
        panel.setAttribute("hidden", "");
        panel.classList.remove("active");
      }
    });
    if (gatesPanel) {
      if (canonical === "all") {
        gatesPanel.removeAttribute("hidden");
        gatesPanel.classList.add("active");
      } else {
        gatesPanel.setAttribute("hidden", "");
        gatesPanel.classList.remove("active");
      }
    }
  }

  function setActiveTab(tabId, persist) {
    var nextTab = VALID_TABS[tabId] || "factory";
    activeTab = nextTab;
    if (persist && searchInput && searchInput.value) {
      searchInput.value = "";
    }
    clearSearchHidden();
    renderTabs(nextTab);
    if (searchStatus) {
      searchStatus.textContent = nextTab === "all" ? "Showing all 5 workspace tabs (20/20 checklist steps visible)" : "Tip: Type above to instant-filter across all 5 tabs";
    }
    if (persist) {
      try {
        localStorage.setItem(TAB_KEY, nextTab);
      } catch (e) {}
    }
  }

  function applySearch() {
    if (!searchInput) return;
    var q = (searchInput.value || "").trim().toLowerCase();
    clearSearchHidden();
    if (!q) {
      renderTabs(activeTab);
      if (searchStatus) {
        searchStatus.textContent = activeTab === "all" ? "Showing all 5 workspace tabs (20/20 checklist steps visible)" : "Tip: Type above to instant-filter across all 5 tabs";
      }
      return;
    }
    renderTabs("all");
    var matchedCards = 0;
    var matchedItems = 0;
    Array.prototype.slice.call(document.querySelectorAll(".phase-card")).forEach(function (card) {
      var units = Array.prototype.slice.call(
        card.querySelectorAll(".step-item, .stage-card, .auto-card, .meta-table tbody tr, .tele-line, .standalone-copy")
      );
      var h2 = card.querySelector("h2");
      var headHit = h2 && h2.textContent.toLowerCase().indexOf(q) !== -1;
      var unitHits = 0;
      units.forEach(function (u) {
        if (u.textContent.toLowerCase().indexOf(q) !== -1) {
          unitHits += 1;
          u.classList.add("search-match");
        } else if (!headHit) {
          u.classList.add("is-search-hidden");
        }
      });
      if (unitHits > 0 || headHit || (!units.length && card.textContent.toLowerCase().indexOf(q) !== -1)) {
        card.classList.add("search-match");
        if (headHit && unitHits > 0) {
          units.forEach(function (u) {
            if (u.textContent.toLowerCase().indexOf(q) === -1) u.classList.add("is-search-hidden");
          });
        }
        matchedCards += 1;
        matchedItems += unitHits || 1;
      } else {
        card.classList.add("is-search-hidden");
      }
    });
    if (searchStatus) {
      searchStatus.textContent = "Filter \"" + q + "\": " + matchedItems + " match(es) across " + matchedCards + " section(s)";
    }
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
    if (setupProgFill) setupProgFill.style.width = pct + "%";
    if (progWrap) progWrap.setAttribute("aria-valuenow", String(pct));
    if (progText) progText.textContent = doneCount + " / " + checks.length + " Completed (" + pct + "%)";
    try {
      var serialized = JSON.stringify(state);
      localStorage.setItem(STORAGE_KEY, serialized);
      localStorage.setItem(STORAGE_KEY_V2, serialized);
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
    var saved = JSON.parse(localStorage.getItem(STORAGE_KEY_V2) || localStorage.getItem(STORAGE_KEY) || "{}");
    checks.forEach(function (cb) {
      if (saved[cb.id]) cb.checked = true;
    });
    var savedTab = localStorage.getItem(TAB_KEY);
    if (savedTab && VALID_TABS[savedTab]) activeTab = VALID_TABS[savedTab];
  } catch (e) {}

  loadTheme();
  setActiveTab(activeTab, false);
  updateProgress();

  tabBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      setActiveTab(btn.getAttribute("data-tab-btn") || btn.getAttribute("data-tab") || "factory", true);
    });
  });

  if (searchInput) {
    searchInput.addEventListener("input", applySearch);
  }
  if (searchClearBtn && searchInput) {
    searchClearBtn.addEventListener("click", function () {
      searchInput.value = "";
      applySearch();
      searchInput.focus();
    });
  }

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
        localStorage.setItem(THEME_KEY_V2, cur);
      } catch (e) {}
    });
  }

  Array.prototype.slice.call(document.querySelectorAll(".copy-btn")).forEach(function (btn) {
    var orig = btn.textContent;
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.getAttribute("data-copy"));
      if (!target) return;
      copyText(target.textContent || "");
      btn.setAttribute("data-copied", "1");
      btn.classList.add("copied");
      btn.textContent = "Copied!";
      setTimeout(function () {
        btn.removeAttribute("data-copied");
        btn.classList.remove("copied");
        btn.textContent = orig;
      }, 1600);
    });
  });
})();
