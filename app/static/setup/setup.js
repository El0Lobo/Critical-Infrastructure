/**
 * CMS Setup page behaviour.
 * Handles unsaved warnings, address autocomplete, formset helpers,
 * collapsible cards, and a couple of UI toggles.
 */
(function (window, document) {
  function onReady(cb) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', cb, { once: true });
    } else {
      cb();
    }
  }

  function initUnsavedWarning() {
    const form = document.getElementById('setup-form');
    const alertBox = document.getElementById('setup-unsaved');
    if (!form || !alertBox) return;

    const fields = Array.from(form.elements || []).filter((el) => el && el.name);

    const serialize = () =>
      fields
        .map((el) => {
          if (el.disabled || el.type === 'file') return '';
          if (el.type === 'checkbox' || el.type === 'radio') {
            return `${el.name}=${el.checked ? '1' : '0'}`;
          }
          return `${el.name}=${el.value ?? ''}`;
        })
        .filter(Boolean)
        .join('&');

    let initialState = serialize();
    let isDirty = false;

    function updateState() {
      const next = serialize();
      isDirty = next !== initialState;
      alertBox.hidden = !isDirty;
    }

    function handleBeforeUnload(event) {
      if (!isDirty) return;
      event.preventDefault();
      event.returnValue = '';
    }

    fields.forEach((el) => {
      el.addEventListener('input', updateState);
      el.addEventListener('change', updateState);
    });

    form.addEventListener('submit', () => {
      isDirty = false;
      alertBox.hidden = true;
      initialState = serialize();
    });

    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('pageshow', () => {
      initialState = serialize();
      updateState();
    });
  }

  function initMembershipToggle() {
    const checkbox = document.getElementById('id_membership_enabled');
    const block = document.getElementById('tiers-block');
    if (!checkbox || !block) return;

    const sync = () => {
      block.style.display = checkbox.checked ? 'block' : 'none';
    };

    checkbox.addEventListener('change', sync);
    sync();
  }

  function initAddressAutocomplete() {
    const searchInput = document.querySelector('[data-geo-search]');
    const resultsBox = document.querySelector('[data-geo-results]');
    if (!searchInput || !resultsBox) return;

    const fields = {
      street: document.getElementById('street-address'),
      number: document.getElementById('street-number'),
      postal: document.getElementById('postal-code'),
      city: document.getElementById('city'),
      country: document.getElementById('country'),
      lat: document.getElementById('geo-lat'),
      lng: document.getElementById('geo-lng'),
    };

    const debounce = (fn, delay = 350) => {
      let t;
      return (...args) => {
        window.clearTimeout(t);
        t = window.setTimeout(() => fn(...args), delay);
      };
    };

    function formatCoord(value) {
      const num = Number(value);
      if (Number.isFinite(num)) {
        return num.toFixed(6);
      }
      return value || '';
    }

    function hideResults() {
      resultsBox.hidden = true;
      resultsBox.innerHTML = '';
    }

    function applyResult(item) {
      searchInput.value = item.display_name || searchInput.value;
      const addr = item.address || {};
      if (fields.street && (addr.road || addr.pedestrian || addr.neighbourhood)) {
        fields.street.value = addr.road || addr.pedestrian || addr.neighbourhood || '';
      }
      if (fields.number && addr.house_number) {
        fields.number.value = addr.house_number;
      }
      if (fields.postal && addr.postcode) {
        fields.postal.value = addr.postcode;
      }
      if (fields.city && (addr.city || addr.town || addr.village)) {
        fields.city.value = addr.city || addr.town || addr.village || '';
      }
      if (fields.country && addr.country) {
        fields.country.value = addr.country;
      }
      if (fields.lat) {
        fields.lat.value = formatCoord(item.lat) || fields.lat.value;
      }
      if (fields.lng) {
        fields.lng.value = formatCoord(item.lon) || fields.lng.value;
      }
      hideResults();
    }

    function renderResults(items) {
      if (!items || !items.length) {
        hideResults();
        return;
      }

      const list = document.createElement('div');
      list.className = 'geo-suggestions__list';

      items.slice(0, 8).forEach((item) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'geo-suggestions__option';
        button.textContent = item.display_name;
        button.addEventListener('click', () => applyResult(item));
        list.appendChild(button);
      });

      resultsBox.innerHTML = '';
      resultsBox.appendChild(list);
      resultsBox.hidden = false;
    }

    const search = debounce(async (query) => {
      const value = query.trim();
      if (value.length < 3) {
        hideResults();
        return;
      }
      const url = new URL('https://nominatim.openstreetmap.org/search');
      url.searchParams.set('format', 'jsonv2');
      url.searchParams.set('addressdetails', '1');
      url.searchParams.set('q', value);

      try {
        const response = await fetch(url.toString(), {
          headers: { Accept: 'application/json' },
        });
        if (!response.ok) throw new Error('Search failed');
        const data = await response.json();
        renderResults(Array.isArray(data) ? data : []);
      } catch (error) {
        if (error.name === 'AbortError') return;
        hideResults();
      }
    }, 400);

    searchInput.addEventListener('input', (event) => search(event.target.value));
    document.addEventListener('click', (event) => {
      if (!resultsBox.contains(event.target) && event.target !== searchInput) {
        hideResults();
      }
    });
  }

  function initFormsetHelpers() {
    const addTierBtn = document.getElementById('add-tier');
    const addRoleBtn = document.getElementById('add-role');

    function replaceIndex(str, newIndex) {
      return str
        .replace(/-(\d+)-/g, `-${newIndex}-`)
        .replace(/_(\d+)_/g, `_${newIndex}_`);
    }

    function addForm(prefix, tableId, rowClass) {
      const totalForms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
      const templateRow = document.querySelector(`#${tableId} .${rowClass}`);
      if (!totalForms || !templateRow) return;

      const count = parseInt(totalForms.value, 10);
      const newRow = templateRow.cloneNode(true);

      newRow.querySelectorAll('input,select,textarea').forEach((el) => {
        if (el.name) el.name = replaceIndex(el.name, count);
        if (el.id) el.id = replaceIndex(el.id, count);

        if (el.type === 'checkbox' || el.type === 'radio') {
          el.checked = false;
        } else if (el.tagName === 'SELECT') {
          el.selectedIndex = -1;
        } else {
          el.value = '';
        }
      });

      const idField = newRow.querySelector("input[name$='-id']");
      if (idField) idField.value = '';
      const deleteField = newRow.querySelector("input[name$='-DELETE']");
      if (deleteField) {
        if (deleteField.type === 'checkbox') {
          deleteField.checked = false;
        } else {
          deleteField.value = '';
        }
      }

      newRow.style.display = '';
      document.getElementById(tableId).appendChild(newRow);
      totalForms.value = count + 1;
    }

    if (addTierBtn) {
      addTierBtn.addEventListener('click', () => addForm('tiers', 'tiers-table', 'tier-form'));
    }
    if (addRoleBtn) {
      addRoleBtn.addEventListener('click', () => addForm('roles', 'roles-table', 'role-form'));
    }

    function markFormRowDeleted(btn) {
      const row = btn.closest('tr');
      if (!row) return;
      const deleteField = row.querySelector("input[name$='-DELETE']");
      if (deleteField) {
        if (deleteField.type === 'checkbox') {
          deleteField.checked = true;
        } else {
          deleteField.value = 'on';
        }
      }
      row.style.display = 'none';
    }

    window.markFormRowDeleted = markFormRowDeleted;
  }

  function initCollapsibles() {
    const cards = document.querySelectorAll('.card');
    if (!cards.length) return;

    function storageSafe(fn) {
      try {
        return fn();
      } catch (error) {
        return null;
      }
    }

    cards.forEach((card) => {
      const heading = card.querySelector('h2');
      const toggleBtn = heading && heading.querySelector('.collapse-toggle');
      const body = card.querySelector('.card__body');
      if (!heading || !toggleBtn || !body) return;

      const key =
        card.getAttribute('data-collapsible-key') ||
        `setup:${(heading.textContent || '').trim().toLowerCase().replace(/\s+/g, '-')}`;

      const stored = storageSafe(() => window.localStorage.getItem(key));
      const defaultOpen = stored == null ? 'true' : stored === '1' ? 'true' : 'false';
      card.setAttribute('aria-expanded', defaultOpen);

      const toggle = () => {
        const isOpen = card.getAttribute('aria-expanded') === 'true';
        const nextState = !isOpen;
        card.setAttribute('aria-expanded', nextState ? 'true' : 'false');
        storageSafe(() => window.localStorage.setItem(key, nextState ? '1' : '0'));
      };

      toggleBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        toggle();
      });

      heading.addEventListener('click', (event) => {
        const target = event.target;
        if (target.closest('button, a, input, select, textarea')) {
          return;
        }
        toggle();
      });
    });
  }

  onReady(() => {
    initUnsavedWarning();
    initMembershipToggle();
    initAddressAutocomplete();
    initFormsetHelpers();
    initCollapsibles();
  });
})(window, document);
