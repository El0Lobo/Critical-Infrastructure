// app/static/events/events.js
(function () {
  "use strict";

  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function openModal(sel) {
    const el = document.querySelector(sel);
    if (el) el.hidden = false;
  }
  function closeModal(el) {
    if (el) el.hidden = true;
  }

  document.addEventListener("click", (ev) => {
    const opener = ev.target.closest("[data-open-modal]");
    if (opener) {
      ev.preventDefault();
      const sel = opener.getAttribute("data-open-modal");
      if (sel) openModal(sel);
    }

    const closer = ev.target.closest("[data-close-modal]");
    if (closer) {
      ev.preventDefault();
      const overlay = closer.closest(".modal-overlay");
      closeModal(overlay);
    }

    const overlay = ev.target.closest(".modal-overlay");
    if (overlay && !ev.target.closest(".modal-card")) {
      closeModal(overlay);
    }
  });

  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") {
      qsa(".modal-overlay").forEach((overlay) => closeModal(overlay));
    }
  });

  function initPerformerTable(table) {
    if (!table) return;
    const addBtn = table.parentElement.querySelector("[data-add-performer]");
    const tmpl = table.parentElement.querySelector("#performer-empty-template");
    const totalInput = qs('input[name$="-TOTAL_FORMS"]', table.parentElement);

    function updateIndexes() {
      const rows = qsa("tbody tr", table);
      rows.forEach((row, idx) => {
        row.dataset.index = idx;
      });
      if (totalInput) totalInput.value = rows.length;
    }

    function cloneRow() {
      if (!tmpl || !totalInput) return;
      const html = tmpl.innerHTML.trim();
      const index = parseInt(totalInput.value || "0", 10);
      const fragment = document.createElement("tbody");
      fragment.innerHTML = html.replace(/__prefix__/g, index);
      const row = fragment.firstElementChild;
      table.querySelector("tbody").appendChild(row);
      if (totalInput) totalInput.value = index + 1;
      bindRow(row);
    }

    function bindRow(row) {
      const removeBtn = row.querySelector("[data-remove-performer]");
      if (removeBtn) {
        removeBtn.addEventListener("click", () => {
          row.remove();
          updateIndexes();
        });
      }
    }

    if (addBtn) {
      addBtn.addEventListener("click", (ev) => {
        ev.preventDefault();
        cloneRow();
      });
    }

    qsa("tbody tr", table).forEach(bindRow);
  }

  function toggleShiftPreset(wrapper) {
    if (!wrapper) return;
    const requires = wrapper.querySelector('input[name="requires_shifts"]');
    const standardField = wrapper.querySelector('[data-field-name="standard_shifts"]');
    const standardInputs = standardField ? Array.from(standardField.querySelectorAll('input[type="checkbox"]')) : [];
    if (!requires) return;

    if (standardInputs.some((input) => input.checked)) {
      requires.checked = true;
    }

    const apply = () => {
      if (standardField) {
        standardField.classList.toggle("disabled", !requires.checked);
        standardInputs.forEach((input) => {
          input.disabled = !requires.checked;
        });
      }
    };

    requires.addEventListener("change", apply);
    apply();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initPerformerTable(qs("[data-performer-table]"));
    qsa(".form-section").forEach((section) => toggleShiftPreset(section));
  });
})();
