/* Navigation toggle on narrow screens (SRS UI-1) and staff keyboard shortcuts (SRS UI-3). */
(function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Live panels refresh themselves (SRS NFR-P5: a change is visible within 5 seconds).
  // Without scripting the page still shows current data on every load.
  document.querySelectorAll("[data-live]").forEach(function (panel) {
    var interval = parseInt(panel.dataset.interval, 10) || 5000;
    setInterval(function () {
      if (document.hidden) { return; }
      fetch(panel.dataset.live, { credentials: "same-origin", headers: { "X-Requested-With": "fetch" } })
        .then(function (response) { return response.ok ? response.text() : null; })
        .then(function (html) { if (html) { panel.innerHTML = html; } })
        .catch(function () { /* keep the last good data */ });
    }, interval);
  });

  // Print buttons (unit labels). No inline script, so the page works under a strict policy.
  document.querySelectorAll("[data-print]").forEach(function (button) {
    button.addEventListener("click", function () { window.print(); });
  });

  if (document.body.dataset.shortcuts !== "on") { return; }

  // event.code is used so the shortcuts work on any keyboard layout, including macOS
  // where Alt+letter types a different character.
  var actions = {
    KeyN: '[data-shortcut="new"]',
    KeyS: '[data-shortcut="save"]',
    KeyF: '[data-shortcut="search"]'
  };
  document.addEventListener("keydown", function (event) {
    if (event.altKey && actions[event.code]) {
      var target = document.querySelector(actions[event.code]);
      if (target) {
        event.preventDefault();
        if (event.code === "KeyF") { target.focus(); } else { target.click(); }
      }
    } else if (event.key === "Escape") {
      var cancel = document.querySelector('[data-shortcut="cancel"]');
      if (cancel) { cancel.click(); }
    }
  });
})();
