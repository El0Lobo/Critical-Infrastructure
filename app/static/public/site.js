(function () {
  "use strict";

  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function openModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.hidden = false;
    document.body.classList.add("modal-open");
  }

  function closeModal(el) {
    if (!el) return;
    el.hidden = true;
    if (!document.querySelector(".modal-overlay:not([hidden])")) {
      document.body.classList.remove("modal-open");
    }
  }

  document.addEventListener("click", (event) => {
    const opener = event.target.closest("[data-modal-open]");
    if (opener) {
      event.preventDefault();
      const targetId = opener.getAttribute("data-modal-open");
      if (targetId) openModal(targetId);
      return;
    }

    const closer = event.target.closest("[data-modal-close]");
    if (closer) {
      event.preventDefault();
      const overlay = closer.closest(".modal-overlay");
      closeModal(overlay);
      return;
    }

    const overlay = event.target.closest(".modal-overlay");
    if (overlay && !event.target.closest(".modal-card")) {
      closeModal(overlay);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      qsa(".modal-overlay").forEach((overlay) => closeModal(overlay));
    }
  });

  function initArchiveFilters(wrapper) {
    const cards = qsa(".page-events-archive__card", wrapper);
    const categoryButtons = qsa("[data-filter-category]", wrapper);
    const searchInput = wrapper.querySelector("[data-filter-search]");
    const pastToggle = wrapper.querySelector("[data-filter-past]");
    let activeCategory = "all";
    let showPast = wrapper.getAttribute("data-show-past-default") === "true";
    let searchTerm = "";

    function isPast(card) {
      const start = card.getAttribute("data-event-start");
      if (!start) return false;
      const parsed = new Date(start);
      if (Number.isNaN(parsed.getTime())) return false;
      return parsed < new Date();
    }

    function applyFilters() {
      cards.forEach((card) => {
        const title = (card.getAttribute("data-event-title") || "").toLowerCase();
        const categories = (card.getAttribute("data-event-categories") || "").toLowerCase();
        const matchesCategory =
          activeCategory === "all" || categories.split(",").includes(activeCategory);
        const matchesSearch = !searchTerm || title.includes(searchTerm);
        const matchesPast = showPast || !isPast(card);
        card.style.display = matchesCategory && matchesSearch && matchesPast ? "" : "none";
      });
    }

    categoryButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        activeCategory = btn.getAttribute("data-filter-category") || "all";
        categoryButtons.forEach((item) => {
          item.classList.toggle("is-active", item === btn);
          item.classList.toggle("btn-outline-secondary", item !== btn);
        });
        applyFilters();
      });
    });

    if (searchInput) {
      searchInput.addEventListener("input", (event) => {
        searchTerm = event.target.value.trim().toLowerCase();
        applyFilters();
      });
    }

    if (pastToggle) {
      pastToggle.classList.toggle("is-active", showPast);
      pastToggle.addEventListener("click", () => {
        showPast = !showPast;
        pastToggle.classList.toggle("is-active", showPast);
        applyFilters();
      });
    }

    applyFilters();
  }

  document.addEventListener("DOMContentLoaded", () => {
    qsa("[data-events-archive]").forEach(initArchiveFilters);
  });
})();
