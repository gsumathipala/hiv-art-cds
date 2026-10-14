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
