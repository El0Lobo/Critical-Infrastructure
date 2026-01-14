// static/pos/pos.js
(function () {
  "use strict";

  // ---------- DOM ----------
  let root, endpoints, el = {};
  let posConfig = {
    taxRate: "0.00",
    showTax: true,
    applyTax: true,
    showDiscounts: true,
    applyDiscounts: true,
  };
  const state = {
    cart: null,
    selectedLineId: null, // for item-scope discounts
    quickButtons: [],
  };

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    root = document.getElementById("pos-root");
    if (!root) {
      console.error("[POS] #pos-root not found");
      return;
    }
    try {
      endpoints = JSON.parse(root.getAttribute("data-endpoints"));
    } catch {
      console.error("[POS] invalid data-endpoints JSON");
      return;
    }

    const cfgRaw = root.getAttribute("data-config");
    if (cfgRaw) {
      try {
        const parsed = JSON.parse(cfgRaw);
        posConfig = {
          ...posConfig,
          taxRate: parsed.taxRate ?? posConfig.taxRate,
          showTax: typeof parsed.showTax === "boolean" ? parsed.showTax : posConfig.showTax,
          applyTax: typeof parsed.applyTax === "boolean" ? parsed.applyTax : posConfig.applyTax,
          showDiscounts:
            typeof parsed.showDiscounts === "boolean" ? parsed.showDiscounts : posConfig.showDiscounts,
          applyDiscounts:
            typeof parsed.applyDiscounts === "boolean"
              ? parsed.applyDiscounts
              : posConfig.applyDiscounts,
        };
      } catch (err) {
        console.warn("[POS] Failed to parse POS config", err);
      }
    }

    // cache elements
    el.search = root.querySelector("#posSearch");
    el.results = root.querySelector("#posResults");
    el.cartLines = root.querySelector("#cartLines");
    el.cartTotals = root.querySelector("#cartTotals"); // contains the _cart_totals include
    el.quickButtons = root.querySelector("#quickButtons");
    el.kind = root.querySelector("#paymentKind");
    el.amount = root.querySelector("#paymentAmount");
    el.btnCheckout = root.querySelector("#btnCheckout");
    el.btnClear = root.querySelector("#btnClearCart");

    bindEvents();
    bootstrap();
  }

  async function bootstrap() {
    try {
      const buttonPromise =
        posConfig.showDiscounts && endpoints.buttons
          ? getJSON(endpoints.buttons)
          : Promise.resolve(null);
      const totalsPromise = getJSON(endpoints.totals);
      const browsePromise = endpoints.browse ? getJSON(endpoints.browse) : Promise.resolve(null);

      const [btns, cart, browse] = await Promise.all([buttonPromise, totalsPromise, browsePromise]);

      if (posConfig.showDiscounts) {
        state.quickButtons = (btns && btns.buttons) || [];
        renderQuickButtons(state.quickButtons);
      }
      renderCart(cart);

      if (browse && browse.categories) {
        renderBrowseGrouped(browse.categories);
      } else if (endpoints.browse) {
        const b = await getJSON(endpoints.browse);
        renderBrowseGrouped((b && b.categories) || []);
      }
    } catch (e) {
      console.error(e);
      toast("Failed to initialize POS.", "error");
    }
  }

  // ---------- Events ----------
  function bindEvents() {
    // Search (debounced) + Enter to force search
    if (el.search) {
      el.search.addEventListener("input", debounce(onSearch, 180));
      el.search.addEventListener("keydown", (e) => {
        if (e.key === "Enter") onSearch();
        if (e.key === "Escape") {
          el.search.value = "";
          showBrowse();
        }
      });
    }

    // Clicks inside results area:
    // - Toggle category collapse
    // - Click size button (data-add-id = variant id)
    if (el.results) {
      el.results.addEventListener("click", (ev) => {
        const hdr = ev.target.closest("[data-cat-toggle]");
        if (hdr) {
          hdr.parentElement.classList.toggle("is-collapsed");
          return;
        }
        const btn = ev.target.closest("[data-add-id]");
        if (!btn) return;
        addItem(btn.getAttribute("data-add-id")).catch(logAndToast("Add failed."));
      });
    }

    // Cart interactions (delegate)
    if (el.cartLines) {
      el.cartLines.addEventListener("click", onCartClick);
      el.cartLines.addEventListener("change", onCartChange);
    }

    // Clear cart
    if (el.btnClear) {
      el.btnClear.addEventListener("click", () => {
        clearCart().catch(logAndToast("Clear failed."));
      });
    }

    // Quick buttons
    if (el.quickButtons) {
      el.quickButtons.addEventListener("click", (ev) => {
        const b = ev.target.closest("button[data-type][data-scope]");
        if (!b) return;
        const scope = b.getAttribute("data-scope"); // ORDER|ITEM
        const type = b.getAttribute("data-type");   // PERCENT|AMOUNT|FREE
        const value = b.getAttribute("data-value") || "0";
        const reasonId = b.getAttribute("data-reason-id") || "";
        const label = b.getAttribute("data-label") || "";
        const buttonId = b.getAttribute("data-btn-id") || "";
        if (scope === "ITEM") {
          if (!state.selectedLineId) {
            toast("Select a cart line first for item discount.", "error");
            return;
          }
          applyDiscount({ scope, type, value, reasonId, itemId: state.selectedLineId, increment: true, label, buttonId })
            .catch(logAndToast("Discount failed."));
        } else {
          applyDiscount({ scope, type, value, reasonId, label })
            .catch(logAndToast("Discount failed."));
        }
      });
    }

    // Checkout
    if (el.btnCheckout) {
      el.btnCheckout.addEventListener("click", () => {
        const kind = (el.kind && el.kind.value) || "CASH";
        const raw = (el.amount && el.amount.value.trim()) || "";
        if (!raw) {
          toast("Enter payment amount.", "error");
          el.amount && el.amount.focus();
          return;
        }
        const val = Number(String(raw).replace(",", "."));
        if (!Number.isFinite(val) || val <= 0) {
          toast("Invalid payment amount.", "error");
          el.amount && el.amount.focus();
          return;
        }
        checkout(kind, val.toFixed(2)).catch((err) => {
          console.error(err);
          toast("Checkout failed.", "error");
        });
      });
    }
  }

  // Search handler (empty → show browse)
  async function onSearch() {
    const q = el.search.value.trim();
    if (!q) {
      showBrowse();
      return;
    }
    try {
      // NEW API SHAPE: { items: [{ id, name, variants: [{id, size, price}, ...] }, ...] }
      const data = await getJSON(endpoints.search + `?q=${encodeURIComponent(q)}`);
      renderSearchGrouped((data && data.items) || []);
    } catch (e) {
      console.error(e);
      toast("Search failed.", "error");
    }
  }

  async function showBrowse() {
    if (!endpoints.browse) {
      el.results.innerHTML = `<div class="empty">Type to search…</div>`;
      return;
    }
    try {
      const data = await getJSON(endpoints.browse);
      renderBrowseGrouped((data && data.categories) || []);
    } catch (e) {
      console.error(e);
      toast("Browse load failed.", "error");
    }
  }

  // Cart clicks: select line, qty inc/dec, remove
  function onCartClick(ev) {
    const selectBtn = ev.target.closest("[data-select-id]");
    if (selectBtn) {
      const id = selectBtn.getAttribute("data-select-id");
      state.selectedLineId = state.selectedLineId === id ? null : id;
      // update selection visuals
      el.cartLines.querySelectorAll(".cart-line").forEach((row) => {
        const isSel = row.getAttribute("data-id") === state.selectedLineId;
        row.classList.toggle("is-selected", !!isSel);
        const dot = row.querySelector("[data-select-id]");
        if (dot) dot.textContent = isSel ? "●" : "○";
      });
      return;
    }

    const inc = ev.target.closest("[data-inc-id]");
    const dec = ev.target.closest("[data-dec-id]");
    const rm = ev.target.closest("[data-remove-id]");

    if (inc || dec) {
      const id = (inc || dec).getAttribute(inc ? "data-inc-id" : "data-dec-id");
      const input = el.cartLines.querySelector(`input[data-qty-id="${cssEscape(id)}"]`);
      if (!input) return;
      const cur = parseInt(input.value || "0", 10);
      let next = cur + (inc ? 1 : -1);
      if (next < 0) next = 0;
      input.value = String(next);
      updateQty(id, next).catch(logAndToast("Qty update failed."));
      return;
    }

    if (rm) {
      const id = rm.getAttribute("data-remove-id");
      removeItem(id).catch(logAndToast("Remove failed."));
    }
  }

  // Cart changes: direct qty input
  function onCartChange(ev) {
    const input = ev.target.closest("input[data-qty-id]");
    if (!input) return;
    const id = input.getAttribute("data-qty-id");
    let qty = parseInt(input.value || "0", 10);
    if (!Number.isFinite(qty) || qty < 0) qty = 0;
    updateQty(id, qty).catch(logAndToast("Qty update failed."));
  }

  // ---------- Rendering ----------
  // Build a single item tile with variant/size buttons
  function buildItemCard(item) {
    const card = document.createElement("div");
    card.className = "pos-item-card";
    card.innerHTML = `
      <div class="pos-item-head">
        <div class="pos-item-title">${esc(item.name)}</div>
      </div>
      <div class="pos-variant-row"></div>
    `;
    const row = card.querySelector(".pos-variant-row");
    (item.variants || []).forEach(v => {
      const btn = document.createElement("button");
      btn.className = "btn size";
      btn.type = "button";
      btn.setAttribute("data-add-id", v.id); // variant id used by addItem()
      btn.textContent = `${v.size} — ${v.price}`;
      row.appendChild(btn);
    });
    return card;
  }

  // Search results (flat list of items with variant buttons)
  function renderSearchGrouped(items) {
    el.results.innerHTML = "";
    if (!items.length) {
      el.results.innerHTML = `<div class="empty">No items found</div>`;
      return;
    }
    const grid = document.createElement("div");
    grid.className = "results-grid";
    items.forEach(item => grid.appendChild(buildItemCard(item)));
    el.results.appendChild(grid);
  }

  // Browse categories → sections → grid of item cards
  function renderBrowseGrouped(categories) {
    el.results.innerHTML = "";
    if (!categories.length) {
      el.results.innerHTML = `<div class="empty">No items available.</div>`;
      return;
    }
    for (const cat of categories) {
      const sec = document.createElement("section");
      sec.className = "cat-section";
      sec.innerHTML = `
        <button class="cat-header" type="button" data-cat-toggle>
          <span class="chev">▾</span>
          <span class="cat-name">${esc(cat.name)}</span>
        </button>
        <div class="cat-body">
          <div class="cat-grid"></div>
        </div>
      `;
      const grid = sec.querySelector(".cat-grid");
      (cat.items || []).forEach(item => grid.appendChild(buildItemCard(item)));
      el.results.appendChild(sec);
    }
    // Optional: start collapsed
    // el.results.querySelectorAll(".cat-section").forEach(s => s.classList.add("is-collapsed"));
  }

  function renderQuickButtons(buttons) {
    if (!el.quickButtons) return;
    el.quickButtons.innerHTML = "";
    if (!buttons.length) {
      el.quickButtons.innerHTML = `<div class="empty">No quick buttons configured.</div>`;
      return;
    }
    for (const b of buttons) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "qbtn";
      btn.textContent = b.label;
      btn.title = `${b.label} — ${b.scope} ${b.type}${b.type !== "FREE" ? " " + b.value : ""}`;
      btn.setAttribute("data-type", b.type);
      btn.setAttribute("data-scope", b.scope);
      btn.setAttribute("data-value", b.value);
      if (b.reason_id) btn.setAttribute("data-reason-id", b.reason_id);
      if (b.label) btn.setAttribute("data-label", b.label);
      if (b.id) btn.setAttribute("data-btn-id", b.id);
      el.quickButtons.appendChild(btn);
    }
  }

  // Compact cart: main row + tiny meta row
  function renderCart(cart) {
    state.cart = cart;
    el.cartLines.innerHTML = "";

    const lines = (cart && cart.lines) || [];
    const orderDiscount = cart && cart.order_discount;
    const orderFreeTotal =
      orderDiscount &&
      orderDiscount.type === "FREE" &&
      Number(cart.totals && cart.totals.grand_total) <= 0.0001;
    const orderHasDiscount =
      orderDiscount && Number(cart.totals && cart.totals.discount_total) > 0;
    if (!lines.length) {
      el.cartLines.innerHTML = `<div class="empty-cart">Cart is empty</div>`;
      updateTotals({ subtotal: "0.00", discount_total: "0.00", tax_total: "0.00", grand_total: "0.00" });
      state.selectedLineId = null;
      return;
    }

    for (const line of lines) {
      const isSel = String(state.selectedLineId) === String(line.id);
      const wrap = document.createElement("div");
      wrap.className = "cart-line" + (isSel ? " is-selected" : "");
      wrap.setAttribute("data-id", String(line.id));

      const discountEntries = Array.isArray(line.discounts)
        ? line.discounts
        : line.discount
        ? [line.discount]
        : [];
      const primaryDiscount =
        discountEntries.find((entry) => entry && entry.type === "FREE") || discountEntries[0] || null;
      const lineSubtotal = Number(line.calc_subtotal || "0");
      const lineTotal = Number(line.calc_total || "0");
      const isLineFree = lineTotal <= 0.0001;
      const discountReason = primaryDiscount || (orderFreeTotal ? orderDiscount : null);
      const showFreeBadge =
        (isLineFree || orderFreeTotal) &&
        discountReason &&
        discountReason.type === "FREE";
      const discountBadge = showFreeBadge ? `<span class="badge">FREE</span>` : "";
      const titleMain = line.title_main || line.title || "";
      const titleDetail = line.variant_label || "";
      const notes = [];
      const freeUnits = Number(line.free_units || 0);
      const discountUnits = Number(line.discount_units || 0);
      if (!showFreeBadge && freeUnits > 0) {
        notes.push(`Contains ${freeUnits} free`);
      }
      if (discountUnits > 0) {
        notes.push(`Contains ${discountUnits} discounted`);
      }
      if (!notes.length && !showFreeBadge && orderHasDiscount) {
        notes.push(orderDiscount.type === "FREE" ? "Contains free" : "Contains discount");
      }
      const titleBlock = `
        <div class="title-text">${esc(titleMain)} ${discountBadge}</div>
        ${titleDetail ? `<div class="title-detail">${esc(titleDetail)}</div>` : ""}
        ${notes.map((note) => `<div class="title-detail title-detail--note">${note}</div>`).join("")}
      `;

      const metaBits = [
        `<span class="sub">Sub: <strong>${esc(line.calc_subtotal)}</strong></span>`,
      ];
      if (posConfig.showDiscounts) {
        metaBits.push(
          `<span class="disc">Disc: <strong>${esc(line.calc_discount)}</strong></span>`
        );
      }
      if (posConfig.showTax) {
        metaBits.push(`<span class="tax">Tax: <strong>${esc(line.calc_tax)}</strong></span>`);
      }

      wrap.innerHTML = `
        <div class="row compact">
          <button class="select" type="button" data-select-id="${line.id}" aria-pressed="${isSel ? "true" : "false"}">${isSel ? "●" : "○"}</button>
          <div class="title">${titleBlock}</div>
          <div class="qty">
            <button class="qty-btn" type="button" data-dec-id="${line.id}" aria-label="Decrease quantity">−</button>
            <input type="number" min="0" step="1" class="qty-input" data-qty-id="${line.id}" value="${Number(line.qty)}" inputmode="numeric" pattern="[0-9]*">
            <button class="qty-btn" type="button" data-inc-id="${line.id}" aria-label="Increase quantity">+</button>
          </div>
          <div class="unit">${esc(line.unit_price)}</div>
          <div class="line-total"><strong>${esc(line.calc_total)}</strong></div>
          <button class="remove" type="button" data-remove-id="${line.id}" title="Remove">✕</button>
        </div>
        <div class="row meta">
          ${metaBits.join("")}
        </div>
      `;
      el.cartLines.appendChild(wrap);
    }

    updateTotals(cart.totals || { subtotal: "0.00", discount_total: "0.00", tax_total: "0.00", grand_total: "0.00" });
  }

  function updateTotals(t) {
    if (!el.cartTotals) return;
    const map = {
      subtotal: '[data-total-subtotal]',
      discount_total: '[data-total-discount]',
      tax_total: '[data-total-tax]',
      grand_total: '[data-total-grand]',
    };
    for (const [k, sel] of Object.entries(map)) {
      const node = el.cartTotals.querySelector(sel);
      if (node) node.textContent = String(t[k] ?? "0.00");
    }
  }

  // ---------- Server actions ----------
  async function refreshCart() {
    const data = await getJSON(endpoints.totals);
    renderCart(data);
  }

  async function addItem(id, qty = 1) {
    const data = await postForm(endpoints.add, { id, qty });
    renderCart(data);
  }

  async function removeItem(id) {
    const data = await postForm(endpoints.remove, { id });
    renderCart(data);
    if (String(state.selectedLineId) === String(id)) state.selectedLineId = null;
  }

  async function updateQty(id, qty) {
    const data = await postForm(endpoints.update, { id, qty });
    renderCart(data);
  }

  async function clearCart() {
    const data = await postForm(endpoints.clear, {});
    renderCart(data);
    state.selectedLineId = null;
  }

  async function applyDiscount({ scope, type, value = "0", reasonId = "", itemId = "", increment = false, label = "", buttonId = "" }) {
    const payload = { scope, type, value };
    if (reasonId) payload.reason_id = reasonId;
    if (label) payload.label = label;
    if (buttonId) payload.button_id = buttonId;
    if (scope === "ITEM") {
      payload.item_id = itemId;
      if (increment) payload.increment = "true";
    }
    const data = await postForm(endpoints.applyDiscount, payload);
    renderCart(data);
  }

  async function checkout(kind, amount) {
    const data = await postForm(endpoints.checkout, { kind, amount, close: "true" });
    toast(`Payment recorded. Sale #${data.sale_id}`, "success");
    await refreshCart();
    if (el.amount) el.amount.value = "";
  }

  // ---------- Net helpers (Django CSRF safe) ----------
  async function getJSON(url) {
    const res = await fetch(url, {
      credentials: "same-origin",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    if (!res.ok) throw new Error(`GET ${url} → ${res.status}`);
    return res.json();
  }

  function toFormData(obj) {
    const fd = new FormData();
    Object.entries(obj).forEach(([k, v]) => fd.append(k, v));
    return fd;
  }

  async function postForm(url, bodyObj) {
    const res = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCsrf(),
      },
      body: toFormData(bodyObj),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`POST ${url} → ${res.status} ${text || ""}`);
    }
    return res.json();
  }

  function getCsrf(name = "csrftoken") {
    const m = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
    return m ? decodeURIComponent(m[2]) : "";
  }

  // ---------- Utilities ----------
  function debounce(fn, ms) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(null, args), ms);
    };
  }

  function esc(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function cssEscape(id) {
    return (window.CSS && CSS.escape) ? CSS.escape(String(id)) : String(id).replace(/"/g, '\\"');
  }

  function logAndToast(msg, type = "error") {
    return (err) => {
      console.error(err);
      toast(msg, type);
    };
  }

  function toast(message, type = "info") {
    const div = document.createElement("div");
    div.className = `pos-toast ${type}`;
    div.textContent = message;
    Object.assign(div.style, {
      position: "fixed",
      right: "14px",
      bottom: "14px",
      background: type === "error" ? "#2a1111" : type === "success" ? "#0f2314" : "#121212",
      color: "#eeeeeeff",
      border: "1px solid #333",
      padding: "10px 12px",
      borderRadius: "10px",
      opacity: "0",
      transform: "translateY(10px)",
      transition: ".25s",
      zIndex: 9999,
    });
    document.body.appendChild(div);
    requestAnimationFrame(() => {
      div.style.opacity = "1";
      div.style.transform = "translateY(0)";
    });
    setTimeout(() => {
      div.style.opacity = "0";
      div.style.transform = "translateY(10px)";
      setTimeout(() => div.remove(), 250);
    }, 2200);
  }
})();
