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
