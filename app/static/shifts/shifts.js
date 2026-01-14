// app/static/shifts/shifts.js
(function () {
  "use strict";

  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function openModal(sel) {
    if (!sel) return;
    const el = document.querySelector(sel);
    if (el) el.hidden = false;
  }
  function closeModal(el) {
    if (el) el.hidden = true;
  }

  function applyAssignAction(form, shiftId) {
    if (!form) return;
    const baseAction = form.dataset.baseAction || form.getAttribute('data-base-action');
    if (!baseAction) return;
    const hidden = qs('input[name="shift_id"]', form);
    const select = qs('[data-assign-select]', form);
    const effectiveId = shiftId || (hidden ? hidden.value : '') || (select ? select.value : '');
    if (!effectiveId) return;
    if (hidden) hidden.value = effectiveId;
    if (select && select.value !== effectiveId) select.value = effectiveId;
    form.dataset.baseAction = baseAction;
    const action = baseAction.replace('__id__', effectiveId);
    form.setAttribute('action', action);
    form.action = action;
    form.setAttribute('hx-post', action);
  }

  function updateSummary(form, eventTitle) {
    const select = qs('[data-assign-select]', form);
    const summaryEl = qs('[data-assign-summary]', form.closest('.modal-card') || document);
    if (!summaryEl) return;
    const shiftLabel = select ? select.options[select.selectedIndex]?.textContent || '' : '';
    if (shiftLabel && eventTitle) {
      summaryEl.textContent = `${shiftLabel} - ${eventTitle}`;
    } else if (eventTitle) {
      summaryEl.textContent = eventTitle;
    } else if (shiftLabel) {
      summaryEl.textContent = shiftLabel;
    } else {
      summaryEl.textContent = '';
    }
  }

  function populateShiftSelect(form, options, selectedId, eventTitle) {
    const select = qs('[data-assign-select]', form);
    if (!select) return;
    select.innerHTML = '';
    (options || []).forEach((opt, idx) => {
      const optionEl = document.createElement('option');
      optionEl.value = String(opt.id);
      optionEl.textContent = opt.label || opt.title || opt.id;
      if (String(opt.id) === String(selectedId) || (!selectedId && idx === 0)) {
        optionEl.selected = true;
      }
      select.appendChild(optionEl);
    });
    if (select.options.length) {
      const value = select.value;
      const hidden = qs('input[name="shift_id"]', form);
      if (hidden) hidden.value = value;
      applyAssignAction(form, value);
    }
    updateSummary(form, eventTitle);
  }

  function prepareAssignModal(opener) {
    if (!opener) return;
    const modal = qs('#modal-assign');
    if (!modal) return;
    const form = qs('#shift-assign-form', modal);
    if (!form) return;

    const eventTitle = opener.getAttribute('data-event-title') || '';
    const optionsJson = opener.getAttribute('data-assign-options');
    form.dataset.eventTitle = eventTitle;
    let options = [];
    if (optionsJson) {
      try {
        options = JSON.parse(optionsJson);
      } catch (err) {
        console.error('Failed to parse assign options', err);
      }
    }

    const shiftId = opener.getAttribute('data-shift-id');
    const shiftTitle = opener.getAttribute('data-shift-title') || '';

    if (options.length) {
      populateShiftSelect(form, options, shiftId, eventTitle);
    } else if (shiftId) {
      const hidden = qs('input[name="shift_id"]', form);
      if (hidden) hidden.value = shiftId;
      applyAssignAction(form, shiftId);
      updateSummary(form, eventTitle || shiftTitle);
    } else {
      updateSummary(form, eventTitle);
    }

    const titleEl = qs('#modal-assign-title', modal);
    if (titleEl) {
      let label = 'Assign shift';
      if (eventTitle) {
        label += ` - ${eventTitle}`;
      }
      if (shiftTitle) {
        label += ` (${shiftTitle})`;
      }
      titleEl.textContent = label;
    }
  }

  document.addEventListener('click', (ev) => {
    const opener = ev.target.closest('[data-open-modal]');
    if (opener) {
      ev.preventDefault();
      const sel = opener.getAttribute('data-open-modal');
      if (sel === '#modal-assign') {
        prepareAssignModal(opener);
      }
      openModal(sel);
    }

    const closer = ev.target.closest('[data-close-modal]');
    if (closer) {
      ev.preventDefault();
      const overlay = closer.closest('.modal-overlay');
      closeModal(overlay);
    }

    const overlay = ev.target.closest('.modal-overlay');
    if (overlay && !ev.target.closest('.modal-card')) {
      closeModal(overlay);
    }
  });

  document.addEventListener('change', (ev) => {
    const select = ev.target.closest('[data-assign-select]');
    if (select) {
      const form = select.closest('#shift-assign-form');
      applyAssignAction(form, select.value);
      updateSummary(form, form.dataset.eventTitle || '');
    }
  });

  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') {
      qsa('.modal-overlay:not([hidden])').forEach((overlay) => closeModal(overlay));
    }
  });

  document.body.addEventListener('htmx:configRequest', (ev) => {
    const elt = ev.detail.elt;
    if (!elt) return;
    const form = elt.closest('#shift-assign-form');
    if (!form) return;
    applyAssignAction(form);
    const action = form.getAttribute('action');
    if (action) {
      ev.detail.path = action;
    }
  });

  document.addEventListener('submit', (ev) => {
    const form = ev.target.closest('#shift-assign-form');
    if (form) {
      applyAssignAction(form);
    }
  });
})();
