(function () {
  const body = document.body;
  const btn = document.getElementById("navToggle");
  const backdrop = document.querySelector("[data-nav-close]");
  const MINI_KEY = "cmsNavMini";

  function isMobile() {
    return window.matchMedia("(max-width: 900px)").matches;
  }

  function setMini(on) {
    body.classList.toggle("nav-mini", !!on);
    try { localStorage.setItem(MINI_KEY, on ? "1" : "0"); } catch(e){}
  }

  function restoreMini() {
    try {
      const v = localStorage.getItem(MINI_KEY);
      if (v === "1") setMini(true);
    } catch(e){}
  }

  function openMobileNav() {
    body.classList.add("nav-open");
    if (btn) btn.setAttribute("aria-expanded", "true");
  }
  function closeMobileNav() {
    body.classList.remove("nav-open");
    if (btn) btn.setAttribute("aria-expanded", "false");
  }

  function toggle() {
    if (isMobile()) {
      if (body.classList.contains("nav-open")) closeMobileNav(); else openMobileNav();
    } else {
      setMini(!body.classList.contains("nav-mini"));
    }
  }

  function normalisePath(path) {
    if (!path) return "/";
    try {
      const url = new URL(path, window.location.origin);
      path = url.pathname;
    } catch (e) {
      // leave as-is
    }
    if (path.length > 1 && path.endsWith("/")) {
      path = path.slice(0, -1);
    }
    return path || "/";
  }

  function highlightActiveNav() {
    const current = normalisePath(window.location.pathname);
    const links = document.querySelectorAll(".cms-nav nav a[href]");
    let winner = null;
    let bestScore = 0;

    links.forEach((link) => {
      const href = link.getAttribute("href");
      if (!href || href.startsWith("#")) {
        return;
      }
      let target = normalisePath(href);
      if (target === "/") {
        return;
      }
      const match =
        current === target || current.startsWith(target + "/");
      if (match && target.length > bestScore) {
        winner = link;
        bestScore = target.length;
      }
    });

    if (winner) {
      winner.classList.add("is-active");
      winner.setAttribute("aria-current", "page");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    restoreMini();
    if (btn) btn.addEventListener("click", toggle);
    if (backdrop) backdrop.addEventListener("click", closeMobileNav);
    window.addEventListener("resize", () => {
      // leave mobile open state when resizing back to desktop
      if (!isMobile()) closeMobileNav();
    });
    highlightActiveNav();
  });
  document.addEventListener('click', function(e){
  const pop = e.target.closest('.popover');
  if (!pop && !e.target.classList.contains('cfg-cog')) {
    document.querySelectorAll('.popover').forEach(p=>p.remove());
  }
});
})();
document.body.addEventListener('htmx:configRequest', (e) => {
  const name = 'csrftoken';
  const match = document.cookie.match(new RegExp('(^|;)\\s*' + name + '=([^;]+)'));
  if (match) e.detail.headers['X-CSRFToken'] = match.pop();
});

function getCsrfToken() {
  const name = "csrftoken";
  const match = document.cookie.match(new RegExp("(^|;)\\s*" + name + "=([^;]+)"));
  return match ? match.pop() : "";
}

function initClearableFileButtons() {
  document.addEventListener('click', (event) => {
    const btn = event.target.closest('[data-file-clear]');
    if (!btn) return;

    const checkboxId = btn.getAttribute('data-file-clear');
    if (!checkboxId) return;

    const checkbox = document.getElementById(checkboxId);
    if (!checkbox) return;

    const shouldClear = !checkbox.checked;
    checkbox.checked = shouldClear;

    const inputId = btn.getAttribute('data-file-input');
    const fileInput = inputId ? document.getElementById(inputId) : null;
    if (shouldClear && fileInput) {
      fileInput.value = '';
      fileInput.dispatchEvent(new Event('change', { bubbles: true }));
    }

    const removeLabel = btn.dataset.labelRemove || 'Remove file';
    const undoLabel = btn.dataset.labelUndo || 'Undo remove';
    btn.textContent = shouldClear ? undoLabel : removeLabel;
    btn.setAttribute('aria-pressed', shouldClear ? 'true' : 'false');
  });
}

document.addEventListener('DOMContentLoaded', function () {
  // Detect unread on the inbox page you’re already rendering
  const hasUnread = !!document.querySelector('.thread-list .thread-item.unread');
  const navLink = document.querySelector('a.nav-link-inbox');
  if (navLink) navLink.classList.toggle('has-unread', hasUnread);

  // OPTIONAL: if you mark threads read via JS, also update the nav live:
  document.addEventListener('thread:read-state-changed', function (e) {
    // Dispatch this custom event wherever you toggle read state
    const anyUnread = !!document.querySelector('.thread-list .thread-item.unread');
    const link = document.querySelector('a.nav-link-inbox');
    if (link) link.classList.toggle('has-unread', anyUnread);
  });
  initClearableFileButtons();
});

(function () {
  const pickerState = {
    modal: null,
    overlay: null,
    panel: null,
    list: null,
    uploadBtn: null,
    uploadInput: null,
    emptyMsg: null,
    onSelect: null,
    currentKind: "image",
    loading: false,
  };

  function ensurePicker() {
    if (pickerState.modal) return;
    const modal = document.createElement("div");
    modal.className = "cms-asset-picker is-hidden";
    modal.innerHTML = `
      <div class="cms-asset-picker__overlay" data-picker-close></div>
      <div class="cms-asset-picker__panel" role="dialog" aria-modal="true" aria-labelledby="cmsAssetPickerTitle">
        <header class="cms-asset-picker__header">
          <div>
            <h2 id="cmsAssetPickerTitle">Choose an asset</h2>
            <p class="muted">Images from the Digital Assets library.</p>
          </div>
          <button type="button" class="cms-asset-picker__close" data-picker-close aria-label="Close">×</button>
        </header>
        <div class="cms-asset-picker__actions">
          <button type="button" class="btn btn-xs btn-outline-secondary" data-picker-upload>Upload image</button>
          <input type="file" accept="image/*" class="sr-only" data-picker-upload-input>
        </div>
        <div class="cms-asset-picker__grid" data-picker-list></div>
        <p class="muted" data-picker-empty style="display:none;">No assets yet. Upload one to get started.</p>
      </div>
    `;
    document.body.appendChild(modal);
    pickerState.modal = modal;
    pickerState.overlay = modal.querySelector("[data-picker-close]");
    pickerState.panel = modal.querySelector(".cms-asset-picker__panel");
    pickerState.list = modal.querySelector("[data-picker-list]");
    pickerState.uploadBtn = modal.querySelector("[data-picker-upload]");
    pickerState.uploadInput = modal.querySelector("[data-picker-upload-input]");
    pickerState.emptyMsg = modal.querySelector("[data-picker-empty]");

    modal.addEventListener("click", (event) => {
      if (event.target.matches("[data-picker-close]")) {
        closePicker();
      }
    });
    pickerState.uploadBtn.addEventListener("click", () => pickerState.uploadInput.click());
    pickerState.uploadInput.addEventListener("change", handleUpload);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !modal.classList.contains("is-hidden")) {
        closePicker();
      }
    });
  }

  function closePicker() {
    if (!pickerState.modal) return;
    pickerState.modal.classList.add("is-hidden");
    pickerState.onSelect = null;
    pickerState.list.innerHTML = "";
    pickerState.emptyMsg.style.display = "none";
    document.body.classList.remove("cms-asset-picker-open");
  }

  function renderAssets(assets) {
    pickerState.list.innerHTML = "";
    if (!assets.length) {
      pickerState.emptyMsg.style.display = "block";
      return;
    }
    pickerState.emptyMsg.style.display = "none";
    assets.forEach((asset) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "cms-asset-picker__item";
      const thumb =
        asset.kind === "image" && asset.url
          ? `<span class="cms-asset-picker__thumb" style="background-image:url('${asset.url}')"></span>`
          : `<span class="cms-asset-picker__thumb cms-asset-picker__thumb--icon">${(asset.kind || "file").slice(0,1).toUpperCase()}</span>`;
      button.innerHTML = `${thumb}<span class="cms-asset-picker__label">${asset.title || asset.slug || "Asset"}</span>`;
      button.addEventListener("click", () => {
        if (typeof pickerState.onSelect === "function") {
          pickerState.onSelect(asset);
        }
        closePicker();
      });
      pickerState.list.appendChild(button);
    });
  }

  function fetchAssets(kind) {
    pickerState.loading = true;
    const params = new URLSearchParams();
    if (kind) params.append("kind", kind);
  return fetch(`/cms/pages/api/assets/?${params.toString()}`, {
    headers: { "X-Requested-With": "XMLHttpRequest" },
    credentials: "same-origin",
  })
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load assets");
        return response.json();
      })
      .then((data) => data.assets || [])
      .finally(() => {
        pickerState.loading = false;
      });
  }

  function handleUpload(event) {
    const file = event.target.files && event.target.files[0];
    event.target.value = "";
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("kind", "image");
  fetch("/cms/pages/api/assets/upload/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
      "X-Requested-With": "XMLHttpRequest",
    },
    credentials: "same-origin",
    body: formData,
  })
      .then((response) => {
        if (!response.ok) return response.text().then((text) => Promise.reject(text || "Upload failed"));
        return response.json();
      })
      .then((payload) => {
        const asset = payload.asset;
        if (!asset) return;
        if (typeof pickerState.onSelect === "function") {
          pickerState.onSelect(asset);
        }
        closePicker();
      })
      .catch((error) => {
        alert(error || "Could not upload asset.");
      });
  }

  function openPicker({ kind = "image", onSelect } = {}) {
    ensurePicker();
    pickerState.currentKind = kind;
    pickerState.onSelect = onSelect;
    pickerState.modal.classList.remove("is-hidden");
    document.body.classList.add("cms-asset-picker-open");
    pickerState.list.innerHTML = "<p class=\"muted\" style=\"padding:1rem;\">Loading…</p>";
    fetchAssets(kind)
      .then((assets) => {
        renderAssets(assets);
      })
      .catch(() => {
        pickerState.list.innerHTML =
          "<p class=\"muted\" style=\"padding:1rem;\">Could not load assets.</p>";
      });
  }

  window.cmsAssetPicker = {
    open: openPicker,
  };

  window.cmsTinyMCEAssets = function cmsTinyMCEAssets() {
    return {
      file_picker_types: "image media",
      file_picker_callback: function (cb, value, meta) {
        const kind = meta && meta.filetype === "image" ? "image" : "file";
        openPicker({
          kind,
          onSelect(asset) {
            const title = asset.title || asset.slug || "";
            cb(asset.url, { title });
          },
        });
      },
      images_upload_handler: function (blobInfo) {
        return new Promise((resolve, reject) => {
          const formData = new FormData();
          formData.append("file", blobInfo.blob(), blobInfo.filename());
          formData.append("kind", "image");
          fetch("/cms/pages/api/assets/upload/", {
            method: "POST",
            headers: {
              "X-CSRFToken": getCsrfToken(),
              "X-Requested-With": "XMLHttpRequest",
            },
            body: formData,
          })
            .then((response) => {
              if (!response.ok) {
                return response.text().then((text) =>
                  Promise.reject(text || "Upload failed")
                );
              }
              return response.json();
            })
            .then((payload) => {
              if (payload && payload.asset && payload.asset.url) {
                resolve(payload.asset.url);
              } else {
                reject("Upload failed");
              }
            })
            .catch((error) => reject(error || "Upload failed"));
        });
      },
    };
  };
})();
