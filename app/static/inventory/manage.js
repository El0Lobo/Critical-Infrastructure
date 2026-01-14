(function () {
  const form = document.getElementById("inventoryFilters");
  if (!form) return;

  let timer = null;
  function submitSoon() {
    if (timer) {
      window.clearTimeout(timer);
    }
    timer = window.setTimeout(() => form.submit(), 300);
  }

  form.querySelectorAll('input[type="search"], select').forEach((el) => {
    el.addEventListener("input", submitSoon);
    el.addEventListener("change", submitSoon);
  });
})();
