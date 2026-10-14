// Progressive enhancement only: every page works without JavaScript.
(function () {
  // Show/hide form fields: data-show-if="field=value[,value]"
  const form = document.getElementById("assess-form");
  if (form) {
    const deps = form.querySelectorAll("[data-show-if]");
    const update = () => {
      deps.forEach((el) => {
        const [name, vals] = el.dataset.showIf.split("=");
        const field = form.elements[name];
        const value = field ? field.value : "";
        el.hidden = !vals.split(",").includes(value);
      });
    };
    form.addEventListener("change", update);
    update();
  }

  // Genotype rows: show filled rows plus one empty row; "+ Add another test" reveals the next
  const rows = Array.from(document.querySelectorAll("[data-genotype-row]"));
  if (rows.length) {
    const filled = (row) => Array.from(row.querySelectorAll("input[type=text], input[type=date], textarea"))
      .some((el) => el.value.trim() !== "");
    let last = 0;
    rows.forEach((row, i) => { if (filled(row)) last = i; });
    rows.forEach((row, i) => { row.hidden = i > last; });
    const add = document.getElementById("add-genotype");
    if (add) add.addEventListener("click", () => {
      const next = rows.find((r) => r.hidden);
      if (next) next.hidden = false;
      if (!rows.some((r) => r.hidden)) add.hidden = true;
    });
  }

  // ART history rows: same progressive reveal
  const artRows = Array.from(document.querySelectorAll("[data-art-row]"));
  if (artRows.length) {
    const used = (row) => Array.from(row.querySelectorAll("input, select")).some((el) => el.value.trim() !== "");
    let lastArt = 0;
    artRows.forEach((row, i) => { if (used(row)) lastArt = i; });
    artRows.forEach((row, i) => { row.hidden = i > lastArt; });
    const addArt = document.getElementById("add-art");
    if (addArt) addArt.addEventListener("click", () => {
      const next = artRows.find((r) => r.hidden);
      if (next) next.hidden = false;
      if (!artRows.some((r) => r.hidden)) addArt.hidden = true;
    });
  }

  // Save / load a case as a local JSON file — nothing is stored on the server
  const save = document.getElementById("save-case");
  if (form && save) {
    save.addEventListener("click", () => {
      const data = {};
      new FormData(form).forEach((value, key) => {
        if (key in data) data[key] = [].concat(data[key], value); else data[key] = value;
      });
      const blob = new Blob([JSON.stringify({ artNavigatorCase: 1, fields: data }, null, 1)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "art-navigator-case.json";
      a.click();
      URL.revokeObjectURL(a.href);
    });
  }
  const load = document.getElementById("load-case");
  if (form && load) {
    load.addEventListener("change", () => {
      const file = load.files[0];
      if (!file) return;
      file.text().then((text) => {
        let fields;
        try { fields = JSON.parse(text).fields; } catch (e) { alert("Not an ART Navigator case file."); return; }
        if (!fields) { alert("Not an ART Navigator case file."); return; }
        form.reset();
        Array.from(form.elements).forEach((el) => {
          if (!el.name || !(el.name in fields)) { if (el.type === "checkbox") el.checked = false; return; }
          const val = fields[el.name];
          if (el.type === "checkbox") el.checked = [].concat(val).includes(el.value) || val === "on";
          else if (el.type !== "file") el.value = Array.isArray(val) ? val[0] : val;
        });
        form.dispatchEvent(new Event("change"));
        document.querySelectorAll("[data-genotype-row], [data-art-row]").forEach((r) => { r.hidden = false; });
      });
    });
  }

  // Tabs: <div class="tabs" data-tabs> buttons with aria-controls
  document.querySelectorAll("[data-tabs]").forEach((bar) => {
    const buttons = bar.querySelectorAll("button[aria-controls]");
    const select = (btn) => {
      buttons.forEach((b) => {
        const on = b === btn;
        b.setAttribute("aria-selected", on);
        document.getElementById(b.getAttribute("aria-controls")).hidden = !on;
      });
      try { history.replaceState(null, "", "#" + btn.getAttribute("aria-controls")); } catch (e) {}
    };
    buttons.forEach((b) => b.addEventListener("click", () => select(b)));
    const initial = Array.from(buttons).find((b) => "#" + b.getAttribute("aria-controls") === location.hash);
    select(initial || buttons[0]);
  });
})();

// Quiz progress — kept in this browser only (localStorage), never sent anywhere.
(function () {
  const KEY = "art-navigator-quiz";
  const load = () => {
    try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; }
  };
  const save = (data) => {
    try { localStorage.setItem(KEY, JSON.stringify(data)); } catch (e) { /* private browsing */ }
  };

  // Record the result when a question has been answered
  const card = document.querySelector("[data-quiz]");
  if (card) {
    const params = new URLSearchParams(location.search);
    if (params.has("a")) {
      const data = load();
      data[card.dataset.quiz] = params.get("a") === card.dataset.answer;
      save(data);
    }
  }

  // Show marks and the running score on the index
  const marks = document.querySelectorAll("[data-mark]");
  if (marks.length) {
    const data = load();
    let right = 0, done = 0;
    marks.forEach((el) => {
      const result = data[el.dataset.mark];
      if (result === undefined) return;
      done += 1;
      if (result) right += 1;
      el.textContent = result ? "✓" : "✗";
      el.style.color = result ? "var(--ok)" : "var(--bad)";
    });
    const box = document.getElementById("score-card");
    if (box && done) {
      box.hidden = false;
      document.getElementById("score-bar").style.width = Math.round((right / done) * 100) + "%";
      document.getElementById("score-text").textContent =
        `${right} of ${done} answered correctly (${marks.length} questions in total).`;
    }
    const reset = document.getElementById("reset-progress");
    if (reset) reset.addEventListener("click", () => { save({}); location.reload(); });
  }
})();
