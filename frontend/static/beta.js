(() => {
  function trackEvent(eventName, metadata = {}) {
    fetch("/api/product-events", {
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_name: eventName, ...metadata }),
    }).catch(() => {});
  }

  const toast = document.querySelector("[data-review-toast]");
  const toastMessage = toast?.querySelector("[data-toast-message]");
  const undoButton = toast?.querySelector("[data-toast-undo]");
  let toastTimer = null;
  let pendingUndo = null;

  function closeToast() {
    if (!toast) return;
    toast.classList.add("hidden");
    toast.classList.remove("flex");
    pendingUndo = null;
    if (toastTimer) window.clearTimeout(toastTimer);
    toastTimer = null;
  }

  function showToast(message, undoAction = null) {
    if (!toast || !toastMessage || !undoButton) return;
    if (toastTimer) window.clearTimeout(toastTimer);
    pendingUndo = undoAction;
    toastMessage.textContent = message;
    undoButton.classList.toggle("hidden", !undoAction);
    toast.classList.remove("hidden");
    toast.classList.add("flex");
    toastTimer = window.setTimeout(closeToast, 5000);
  }

  async function savePreference(itemId, payload) {
    const response = await fetch(`/api/onbid/${itemId}/preference`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`preference request failed: ${response.status}`);
    return response.json();
  }

  document.querySelectorAll("form[data-preference-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const card = form.closest("[data-review-card]");
      const itemId = card?.dataset.itemId;
      const action = form.dataset.preferenceForm;
      const submit = form.querySelector("button[type='submit']");
      const enabledInput = form.querySelector("input[name='enabled']");
      if (!itemId || !submit || !enabledInput || submit.disabled) return;

      const enabled = enabledInput.value === "true";
      submit.disabled = true;
      submit.setAttribute("aria-busy", "true");
      try {
        if (action === "passed") {
          await savePreference(itemId, { passed: enabled });
          if (enabled && card) {
            card.hidden = true;
            showToast("기본 목록에서 숨겼습니다", async () => {
              try {
                await savePreference(itemId, { passed: false });
                card.hidden = false;
                card.scrollIntoView({ block: "nearest" });
                showToast("패스를 실행 취소했습니다");
              } catch {
                showToast("실행 취소에 실패했습니다. 패스함에서 복구해 주세요.");
              }
            });
          } else if (!enabled && card) {
            card.hidden = true;
            showToast("패스함에서 복구했습니다");
          }
        } else if (action === "favorite") {
          await savePreference(itemId, { favorite: enabled });
          enabledInput.value = enabled ? "false" : "true";
          submit.textContent = enabled ? "관심 해제" : "관심";
          showToast(enabled ? "관심에 저장했습니다" : "관심에서 해제했습니다");
        }
      } catch {
        if (card) card.hidden = false;
        showToast("저장하지 못했습니다. 잠시 후 다시 시도해 주세요.");
      } finally {
        submit.disabled = false;
        submit.removeAttribute("aria-busy");
      }
    });
  });

  undoButton?.addEventListener("click", async () => {
    const action = pendingUndo;
    pendingUndo = null;
    if (action) await action();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    document.querySelectorAll("details[data-filter-drawer][open]").forEach((drawer) => drawer.removeAttribute("open"));
  });

  document.querySelectorAll("[data-copy-value]").forEach((button) => {
    button.addEventListener("click", async () => {
      const value = button.dataset.copyValue || "";
      const label = button.dataset.copyLabel || "정보";
      if (!value) return;
      try {
        await navigator.clipboard.writeText(value);
        showToast(`${label}를 복사했습니다`);
        if (label === "온비드 번호") trackEvent("copy_onbid_number", { state: true });
      } catch {
        showToast("복사하지 못했습니다. 값을 직접 선택해 주세요.");
      }
    });
  });

  document.querySelectorAll("[data-category-tab]").forEach((link) => link.addEventListener("click", () => {
    trackEvent("category_tab_click", { category: link.dataset.categoryTab || "all" });
  }));
  document.querySelectorAll("details[data-filter-drawer]").forEach((drawer) => drawer.addEventListener("toggle", () => {
    if (drawer.open) trackEvent("filter_open", { state: true });
  }));
  document.querySelectorAll("form[data-compact-filter], details[data-filter-drawer] form").forEach((form) => form.addEventListener("submit", () => {
    trackEvent("filter_apply", { sort: form.querySelector('[name="sort"]')?.value || "" });
  }));
  document.querySelectorAll('[name="sort"]').forEach((select) => select.addEventListener("change", () => trackEvent("sort_change", { sort: select.value })));
  document.querySelectorAll('[data-filter-clear]').forEach((link) => link.addEventListener("click", () => trackEvent("filter_clear", { state: true })));
  document.querySelectorAll('[data-compact-pagination] a').forEach((link) => link.addEventListener("click", () => trackEvent("pagination_click")));
  document.querySelectorAll('[data-review-card] h2 a').forEach((link) => link.addEventListener("click", () => {
    trackEvent("view_item_detail", { item_id: link.closest("[data-review-card]")?.dataset.itemId || "" });
  }));
  document.querySelectorAll('a[href^="/my/onbid/"]').forEach((link) => link.addEventListener("click", () => trackEvent("view_my_review")));
  document.querySelectorAll('[data-original-fallback]').forEach((link) => link.addEventListener("click", () => trackEvent("view_original_fallback")));
})();
