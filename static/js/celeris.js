(function () {
  const root = document.documentElement;
  const shell = document.querySelector(".app-shell");

  const icons = {
    activity: '<path d="M22 12h-4l-3 8-6-16-3 8H2"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    coins: '<circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h1.5a1.5 1.5 0 0 1 0 3H7V6Z"/><path d="M7 9h2a1.5 1.5 0 0 1 0 3H7V9Z"/>',
    monitor: '<rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 22h8"/><path d="M12 18v4"/>',
    table: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a15 15 0 0 1 0 18"/><path d="M12 3a15 15 0 0 0 0 18"/>',
    syringe: '<path d="m18 2 4 4"/><path d="m17 7 3-3"/><path d="M19 9 8.7 19.3a2.4 2.4 0 0 1-3.4 0l-.6-.6a2.4 2.4 0 0 1 0-3.4L15 5"/><path d="m9 11 4 4"/><path d="m5 19-3 3"/>',
    handshake: '<path d="m11 17 2 2a2.8 2.8 0 0 0 4 0l3-3a2.8 2.8 0 0 0 0-4l-2-2"/><path d="m14 14 2 2"/><path d="m3 12 6-6 4 4-6 6H3v-4Z"/><path d="m14 6 2-2 5 5-2 2"/>',
    headset: '<path d="M3 13a9 9 0 0 1 18 0"/><path d="M21 13v4a2 2 0 0 1-2 2h-2v-6h4Z"/><path d="M3 13v4a2 2 0 0 0 2 2h2v-6H3Z"/><path d="M13 21h3a3 3 0 0 0 3-3"/>',
    wrench: '<path d="M14.7 6.3a4 4 0 0 0-5 5L3 18v3h3l6.7-6.7a4 4 0 0 0 5-5l-2.4 2.4-3-3 2.4-2.4Z"/>',
    shirt: '<path d="M20.4 7.2 16 4a4 4 0 0 1-8 0L3.6 7.2 6 12l2-1v9h8v-9l2 1 2.4-4.8Z"/>',
    "clipboard-plus": '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M9 14h6"/><path d="M12 11v6"/>',
    home: '<path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/>',
    menu: '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
    theme: '<path d="M12 3a6 6 0 0 0 9 7.2A9 9 0 1 1 12 3Z"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    key: '<circle cx="7.5" cy="14.5" r="4.5"/><path d="m11 11 8-8"/><path d="m16 4 4 4"/><path d="m15 8 2 2"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>',
    eraser: '<path d="m7 21-4-4L14 6l4 4L7 21Z"/><path d="m11 10 4 4"/><path d="M7 21h14"/>',
    play: '<path d="m6 3 14 9-14 9V3Z"/>',
    save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/>',
    trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>',
    "arrow-left": '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    "chevrons-left": '<path d="m11 17-5-5 5-5"/><path d="m18 17-5-5 5-5"/>',
    "corner-up-left": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 6 6v5"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "chevrons-right": '<path d="m13 17 5-5-5-5"/><path d="m6 17 5-5-5-5"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    check: '<path d="m20 6-11 11-5-5"/>',
    help: '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 1 1 5.8 1c0 2-3 2-3 4"/><path d="M12 17h.01"/>',
    plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
    "ban": '<circle cx="12" cy="12" r="9"/><path d="m7 17 10-10"/>',
  };

  function renderIcons() {
    document.querySelectorAll("[data-nav-icon]").forEach((element) => {
      const name = element.getAttribute("data-nav-icon") || "";
      const body = icons[name] || icons.table;
      element.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
    });
  }

  function setQueryMode(enabled) {
    document.body.classList.toggle("screen-query-mode", enabled);
    setActionStatus(enabled ? "CONSULTA" : "EDIÇÃO");
    const queryButton = document.querySelector("[data-query-toggle]");
    const cancelButton = document.querySelector("[data-query-cancel]");
    if (queryButton) {
      queryButton.dataset.queryMode = enabled ? "execute" : "open";
      queryButton.title = enabled ? "Executar consulta" : "Abrir consulta";
      queryButton.querySelector("[data-nav-icon]")?.setAttribute("data-nav-icon", enabled ? "play" : "search");
    }
    if (cancelButton) cancelButton.hidden = !enabled;
    document.querySelectorAll("[data-consultable], [data-primary-key]").forEach((field) => {
      const canQuery = field.dataset.consultable === "true" || field.dataset.primaryKey === "true";
      const canEdit = field.dataset.editable !== "false" && field.dataset.primaryKey !== "true";
      if (enabled && canQuery) {
        field.removeAttribute("readonly");
        field.removeAttribute("disabled");
      } else if (!canEdit) {
        if (field.matches("select, input[type='checkbox']")) {
          field.setAttribute("disabled", "disabled");
        } else {
          field.setAttribute("readonly", "readonly");
        }
      }
    });
  }

  function clearFormFields(form) {
    form?.querySelectorAll("input, select, textarea").forEach((field) => {
      if (field.type === "hidden") {
        if (field.name !== "csrfmiddlewaretoken") field.value = "";
        return;
      }
      if (field.type === "checkbox" || field.type === "radio") {
        field.checked = false;
        return;
      }
      if (field instanceof HTMLSelectElement) {
        if (field.multiple) {
          Array.from(field.options).forEach((option) => {
            option.selected = false;
          });
        } else {
          field.selectedIndex = 0;
        }
        field.dispatchEvent(new Event("change", { bubbles: true }));
        return;
      }
      field.value = "";
      field.classList.remove("field-invalid", "field-duplicate");
      field.setCustomValidity?.("");
    });
    form?.querySelectorAll("details").forEach((section, index) => {
      section.open = index === 0;
    });
    form?.dispatchEvent(new CustomEvent("celeris:reset-multiselects", { bubbles: true }));
    closeFloatingSelect();
    setQueryMode(false);
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = true;
    form?.setAttribute("data-dirty", "false");
    clearCurrentFormState(form);
  }

  function clearScreenData() {
    const form = getPrimaryForm();
    if (!form) return;
    if (form.method?.toLowerCase() === "get") {
      window.location.href = window.location.pathname;
      return;
    }
    if (form.matches("[data-editable-table]")) {
      resetEditableTableRows(form, false);
      form.dataset.dirty = "false";
      window.history.replaceState({}, "", window.location.pathname);
    } else {
      clearFormFields(form);
    }
    setActionStatus("EDIÇÃO");
  }

  function resetEditableTableRows(form, markDirty = false) {
    if (!form?.matches("[data-editable-table]")) return false;
    form.querySelectorAll("tbody tr").forEach((row) => row.remove());
    addEditableTableRow(form, markDirty);
    form.dataset.dirty = markDirty ? "true" : "false";
    updateTablePagerVisibility(form);
    return true;
  }

  function prepareEditableTableQueryRow(form) {
    if (!form?.matches("[data-editable-table]")) return;
    getEditableTableFields(form).forEach((field) => {
      if (field instanceof HTMLSelectElement) {
        if (!Array.from(field.options).some((option) => option.value === "")) {
          field.add(new Option("", ""), 0);
        }
        field.value = "";
      } else if (field.type === "checkbox" || field.type === "radio") {
        field.checked = false;
      } else {
        field.value = "";
      }
      field.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  const savedTheme = localStorage.getItem("celeris-theme");
  if (savedTheme === "dark") root.classList.add("dark");

  if (localStorage.getItem("celeris-sidebar") === "collapsed") {
    shell?.classList.add("sidebar-collapsed");
  }
  root.classList.remove("sidebar-state-collapsed");

  let sidebarFlyout = null;
  let sidebarFlyoutTrigger = null;
  let activeLookupField = null;
  let activeFloatingSelect = null;
  let floatingSelectSearch = "";
  let floatingSelectSearchTimer = null;
  let reverseEnterRequested = false;
  let sidebarAutoCollapseTimer = null;
  let isRestoringFormState = false;

  function scheduleSidebarAutoCollapse() {
    window.clearTimeout(sidebarAutoCollapseTimer);
    sidebarAutoCollapseTimer = window.setTimeout(() => {
      shell?.classList.add("sidebar-collapsed");
      localStorage.setItem("celeris-sidebar", "collapsed");
      closeSidebarFlyout();
    }, 10 * 60 * 1000);
  }

  function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;",
    }[char]));
  }

  function closeSidebarFlyout() {
    sidebarFlyout?.remove();
    sidebarFlyout = null;
    sidebarFlyoutTrigger = null;
  }

  function positionSidebarFlyout(flyout, trigger) {
    const triggerRect = trigger.getBoundingClientRect();
    const flyoutRect = flyout.getBoundingClientRect();
    const viewportGap = 8;
    const left = Math.min(triggerRect.right + viewportGap, window.innerWidth - flyoutRect.width - viewportGap);
    const top = Math.min(
      Math.max(viewportGap, triggerRect.top),
      window.innerHeight - flyoutRect.height - viewportGap
    );

    flyout.style.left = `${Math.max(viewportGap, left)}px`;
    flyout.style.top = `${Math.max(viewportGap, top)}px`;
  }

  function openSidebarFlyout(navGroup, trigger) {
    const menu = navGroup.querySelector(":scope > div");
    const label = navGroup.querySelector(":scope > summary .nav-label")?.textContent?.trim() || "Menu";
    if (!menu) return;

    if (sidebarFlyout && sidebarFlyoutTrigger === trigger) {
      closeSidebarFlyout();
      return;
    }

    closeSidebarFlyout();
    sidebarFlyoutTrigger = trigger;
    sidebarFlyout = document.createElement("div");
    sidebarFlyout.className = "sidebar-flyout";
    const title = document.createElement("div");
    title.className = "sidebar-flyout-title";
    title.textContent = label;
    sidebarFlyout.appendChild(title);
    sidebarFlyout.appendChild(menu.cloneNode(true));
    document.body.appendChild(sidebarFlyout);
    positionSidebarFlyout(sidebarFlyout, trigger);
  }

  function closeSiblingNavGroups(summary) {
    const navGroup = summary.closest(".nav-group");
    if (!navGroup || navGroup.open) return;

    document.querySelectorAll(".sidebar .nav-group[open]").forEach((openGroup) => {
      if (openGroup !== navGroup) openGroup.open = false;
    });
  }

  function ensureLookupModal() {
    let modal = document.querySelector("[data-lookup-modal]");
    if (modal) return modal;

    modal = document.createElement("div");
    modal.className = "lookup-modal";
    modal.dataset.lookupModal = "true";
    modal.hidden = true;
    modal.innerHTML = `
      <div class="lookup-dialog" role="dialog" aria-modal="true" aria-label="Consulta de campo">
        <div class="lookup-header">
          <strong>Consulta</strong>
          <button type="button" data-lookup-close title="Fechar">&times;</button>
        </div>
        <div class="lookup-search">
          <input data-lookup-search type="text" placeholder="Pesquisar">
          <button type="button" data-lookup-run>Consultar</button>
        </div>
        <div class="lookup-results" data-lookup-results></div>
      </div>
    `;
    document.body.appendChild(modal);
    return modal;
  }

  async function runLookup(modal) {
    if (!activeLookupField) return;
    const table = activeLookupField.dataset.lookupTable;
    if (!table) return;
    const search = modal.querySelector("[data-lookup-search]")?.value || "";
    const params = new URLSearchParams({
      table,
      q: search,
      value: activeLookupField.dataset.lookupValueField || "",
      display: activeLookupField.dataset.lookupDisplayField || "",
    });
    const resultsPanel = modal.querySelector("[data-lookup-results]");
    if (resultsPanel) resultsPanel.innerHTML = '<div class="lookup-empty">Consultando...</div>';
    const response = await fetch(`/lookup/?${params.toString()}`);
    const payload = await response.json();
    const results = payload.results || [];
    if (!resultsPanel) return;
    if (!results.length) {
      resultsPanel.innerHTML = '<div class="lookup-empty">Nenhum registro encontrado.</div>';
      return;
    }
    resultsPanel.innerHTML = results.map((item) => `
      <button type="button" data-lookup-select data-value="${escapeHTML(item.value)}">
        <span>${escapeHTML(item.value)}</span>
        <strong>${escapeHTML(item.label)}</strong>
      </button>
    `).join("");
  }

  function openLookup(field) {
    activeLookupField = field;
    const modal = ensureLookupModal();
    const search = modal.querySelector("[data-lookup-search]");
    modal.hidden = false;
    if (search) {
      search.value = field.value || "";
      search.focus();
    }
    runLookup(modal);
  }

  function closeLookup() {
    const modal = document.querySelector("[data-lookup-modal]");
    if (modal) modal.hidden = true;
    activeLookupField = null;
  }

  function setActionStatus(value) {
    const status = document.querySelector("[data-action-status]");
    if (status) status.textContent = value;
  }

  function getPrimaryForm() {
    return document.querySelector(".content form");
  }

  function hasDirtyForm() {
    return getPrimaryForm()?.dataset.dirty === "true";
  }

  function markInvalidFields(form) {
    form?.classList.add("form-submitted");
    const firstInvalid = form?.querySelector(":invalid");
    if (firstInvalid) {
      const section = firstInvalid.closest("details");
      if (section) section.open = true;
      firstInvalid.focus();
    }
    return Boolean(firstInvalid);
  }

  function setupServerValidationErrors() {
    let errors = {};
    try {
      errors = JSON.parse(document.body.dataset.formErrors || "{}");
    } catch (error) {
      errors = {};
    }
    const firstErrorName = Object.keys(errors)[0];
    Object.entries(errors).forEach(([fieldName, fieldErrors]) => {
      const field = document.querySelector(`[name="${CSS.escape(fieldName)}"]`);
      if (!field) return;
      field.classList.add("field-server-invalid");
      field.setAttribute("aria-invalid", "true");
      const label = field.closest("label");
      label?.classList.add("field-server-error");
      if (label && !label.querySelector(".field-error-message")) {
        const message = document.createElement("span");
        message.className = "field-error-message";
        message.textContent = (fieldErrors || []).map((item) => item.message || item).join(" ");
        label.appendChild(message);
      }
    });
    if (!firstErrorName) return;
    const firstField = document.querySelector(`[name="${CSS.escape(firstErrorName)}"]`);
    const section = firstField?.closest("details");
    if (section) section.open = true;
    firstField?.scrollIntoView({ behavior: "smooth", block: "center" });
    const blockingNotification = document.querySelector("[data-blocking-notification]");
    if (!blockingNotification || blockingNotification.hidden) {
      window.requestAnimationFrame(() => firstField?.focus());
    }
  }

  function ensureBlockingNotification() {
    let notification = document.querySelector("[data-blocking-notification]");
    if (notification) return notification;

    notification = document.createElement("div");
    notification.className = "blocking-notification";
    notification.dataset.blockingNotification = "true";
    notification.hidden = true;
    notification.innerHTML = `
      <div class="blocking-notification-backdrop" aria-hidden="true"></div>
      <section class="blocking-notification-card" role="dialog" aria-modal="true">
        <strong data-blocking-title>Notificação</strong>
        <p data-blocking-message></p>
        <div class="blocking-notification-extra" data-blocking-extra></div>
        <div class="blocking-notification-actions">
          <button class="toolbar-button" data-blocking-cancel type="button">Cancelar</button>
          <button class="toolbar-button" data-blocking-confirm type="button">OK</button>
        </div>
      </section>
    `;
    document.body.appendChild(notification);
    return notification;
  }

  function addNotificationToHistory(message, type = "info") {
    const list = document.querySelector(".notifications-list");
    if (!list) return;
    list.querySelector(".notification-empty")?.remove();
    const item = document.createElement("button");
    item.className = `notification-item ${type}`;
    item.dataset.notificationItem = "true";
    item.type = "button";
    item.innerHTML = `
      <span class="notification-time">${new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</span>
      <span class="notification-text"></span>
    `;
    item.querySelector(".notification-text").textContent = message;
    list.prepend(item);
    const badge = document.querySelector(".notification-badge");
    if (badge) {
      badge.textContent = String((Number(badge.textContent) || 0) + 1);
    } else {
      const toggle = document.querySelector("[data-notifications-toggle]");
      const newBadge = document.createElement("span");
      newBadge.className = "notification-badge";
      newBadge.textContent = "1";
      toggle?.appendChild(newBadge);
    }
    persistNotification(message, type);
  }

  function getPersistedNotifications() {
    try {
      return JSON.parse(localStorage.getItem("celeris-notifications") || "[]");
    } catch (error) {
      return [];
    }
  }

  function persistNotification(message, type = "info") {
    const notifications = getPersistedNotifications();
    if (notifications.some((notification) => notification.message === message && notification.type === type)) return;
    notifications.unshift({
      message,
      type,
      time: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
    });
    localStorage.setItem("celeris-notifications", JSON.stringify(notifications.slice(0, 50)));
  }

  function renderPersistedNotifications() {
    const list = document.querySelector(".notifications-list");
    if (!list) return;
    const currentTexts = new Set(Array.from(list.querySelectorAll(".notification-text")).map((item) => item.textContent.trim()));
    getPersistedNotifications().reverse().forEach((notification) => {
      if (currentTexts.has(notification.message)) return;
      list.querySelector(".notification-empty")?.remove();
      const item = document.createElement("button");
      item.className = `notification-item ${notification.type || "info"}`;
      item.dataset.notificationItem = "true";
      item.type = "button";
      item.innerHTML = `
        <span class="notification-time">${escapeHTML(notification.time || "")}</span>
        <span class="notification-text"></span>
      `;
      item.querySelector(".notification-text").textContent = notification.message;
      list.prepend(item);
    });
  }

  function showBlockingNotification(options = {}) {
    const {
      title = "Notificação",
      message = "",
      confirmText = "OK",
      cancelText = "",
      extraElement = null,
      onConfirm = null,
      store = false,
      type = "info",
      focusTarget = null,
      initialFocus = "confirm",
    } = options;
    const notification = ensureBlockingNotification();
    const titleElement = notification.querySelector("[data-blocking-title]");
    const messageElement = notification.querySelector("[data-blocking-message]");
    const extra = notification.querySelector("[data-blocking-extra]");
    const confirmButton = notification.querySelector("[data-blocking-confirm]");
    const cancelButton = notification.querySelector("[data-blocking-cancel]");

    if (store && message) addNotificationToHistory(message, type);
    titleElement.textContent = title;
    messageElement.textContent = message;
    extra.innerHTML = "";
    if (extraElement) extra.appendChild(extraElement);
    confirmButton.textContent = confirmText;
    cancelButton.textContent = cancelText || "Cancelar";
    cancelButton.hidden = !cancelText;
    notification.hidden = false;

    return new Promise((resolve) => {
      const finish = (result) => {
        notification.hidden = true;
        confirmButton.removeEventListener("click", confirmHandler);
        cancelButton.removeEventListener("click", cancelHandler);
        notification.removeEventListener("keydown", keyHandler);
        extra.innerHTML = "";
        if (focusTarget?.isConnected) {
          window.requestAnimationFrame(() => {
            const section = focusTarget.closest("details");
            if (section) section.open = true;
            focusTarget.focus();
            focusTarget.select?.();
          });
        }
        resolve(result);
      };
      const confirmHandler = () => {
        if (onConfirm && onConfirm() === false) return;
        finish(true);
      };
      const cancelHandler = () => finish(false);
      const keyHandler = (event) => {
        if (event.key === "Escape" && !cancelButton.hidden) {
          event.preventDefault();
          cancelHandler();
        }
      };
      confirmButton.addEventListener("click", confirmHandler);
      cancelButton.addEventListener("click", cancelHandler);
      notification.addEventListener("keydown", keyHandler);
      window.requestAnimationFrame(() => {
        const firstField = extra.querySelector("select, input, textarea");
        const preferredButton = initialFocus === "cancel" && !cancelButton.hidden ? cancelButton : confirmButton;
        (firstField || preferredButton).focus();
      });
    });
  }

  async function promptChangeReason(form) {
    if (form?.dataset.requiresChangeReason !== "true" || form.dataset.dirty !== "true") return true;
    const reasonField = form.querySelector('[name="motivo_alteracao"]');
    const noteField = form.querySelector('[name="observacao_alteracao"]');
    if (!reasonField || !noteField || (reasonField.value && noteField.value.trim())) return true;

    const extra = document.createElement("div");
    extra.innerHTML = `
      <label>Motivo da alteração
        <select data-change-reason-modal>${reasonField.innerHTML}</select>
      </label>
      <label>Observação
        <input data-change-note-modal type="text" maxlength="255" autocomplete="off">
      </label>
      <span class="blocking-notification-error" data-change-reason-error hidden></span>
    `;
    const select = extra.querySelector("[data-change-reason-modal]");
    const note = extra.querySelector("[data-change-note-modal]");
    const error = extra.querySelector("[data-change-reason-error]");
    select.value = reasonField.value || "";
    note.value = noteField.value || "";

    return showBlockingNotification({
      title: "Motivo da alteração",
      message: "Informe o motivo e a observação para registrar a alteração do paciente.",
      confirmText: "Confirmar",
      cancelText: "Cancelar",
      extraElement: extra,
      onConfirm: () => {
        if (!select.value || !note.value.trim()) {
          error.hidden = false;
          error.textContent = "Preencha o motivo e a observação da alteração.";
          return false;
        }
        reasonField.value = select.value;
        noteField.value = note.value.trim();
        return true;
      },
    });
  }

  async function submitPrimaryForm(form) {
    markInvalidFields(form);
    if (!form.reportValidity()) return false;
    if (!await promptChangeReason(form)) return false;
    form.requestSubmit();
    return true;
  }

  function getEditableTableForm() {
    return document.querySelector("form[data-editable-table]");
  }

  function getActiveEditableRow() {
    const active = document.activeElement?.closest?.("tr[data-editable-row]");
    return active || document.querySelector("tr[data-editable-row].selected");
  }

  function markFormDirty(form) {
    if (!form) return;
    form.dataset.dirty = "true";
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = false;
    setActionStatus("EDIÇÃO");
  }

  function addEditableTableRow(form, markDirty = true) {
    const template = form.querySelector("template[data-table-new-row]");
    const tbody = form.querySelector("tbody");
    if (!template || !tbody) return false;
    const fragment = template.content.cloneNode(true);
    const row = fragment.querySelector("tr");
    tbody.querySelector(".empty-cell")?.closest("tr")?.remove();
    tbody.appendChild(fragment);
    row?.querySelectorAll("[data-cep-state-select]").forEach(filterCepCitiesForState);
    updateTablePagerVisibility(form);
    if (markDirty) {
      markFormDirty(form);
    } else {
      form.dataset.dirty = "false";
      const saveButton = document.querySelector('[data-action="save"]');
      if (saveButton) saveButton.disabled = true;
    }
    row?.querySelector("input:not([readonly]):not([disabled]), select:not([disabled]), textarea:not([readonly]):not([disabled])")?.focus();
    return true;
  }

  function hasLoadedRecord(form = getPrimaryForm()) {
    if (!form || document.body.classList.contains("screen-query-mode")) return false;
    const primaryKey = form.querySelector('[data-primary-key="true"], .pk-label input');
    return Boolean(primaryKey?.value?.trim());
  }

  function hasSelectedPersistedRow(form = getEditableTableForm()) {
    if (!form || document.body.classList.contains("screen-query-mode")) return false;
    const row = getActiveEditableRow();
    const primaryKey = row?.querySelector('[data-primary-key="true"]');
    return Boolean(row && !row.hidden && primaryKey?.value?.trim());
  }

  function hasSelectedEditableRow(form = getEditableTableForm()) {
    if (!form || document.body.classList.contains("screen-query-mode")) return false;
    const row = getActiveEditableRow();
    return Boolean(row && !row.hidden && form.contains(row));
  }

  function getSelectedRowActiveField(form = getEditableTableForm()) {
    if (!form || document.body.classList.contains("screen-query-mode")) return null;
    const row = getActiveEditableRow();
    if (!row || row.hidden || !form.contains(row)) return null;
    return row.querySelector('select[name^="sn_ativo_"], select[name^="active_"], select[name="new_sn_ativo"], select[name="new_active"]');
  }

  function updateTablePagerVisibility(form = getEditableTableForm()) {
    const pager = form?.querySelector("[data-table-pager]");
    if (!pager) return;
    const visibleRows = Array.from(form.querySelectorAll("tbody tr[data-editable-row]:not([hidden])"));
    const hasLoadedRows = visibleRows.some((row) => row.querySelector('[data-primary-key="true"]')?.value?.trim());
    const hasPageAction = Boolean(pager.querySelector(".table-pager-link:not(.disabled)"));
    pager.hidden = !(hasLoadedRows && hasPageAction);
  }

  function setupInitialEditableRows() {
    if (window.location.search) return;
    document.querySelectorAll("form[data-editable-table]").forEach((form) => {
      if (!form.querySelector("tbody tr[data-editable-row]") && form.querySelector("template[data-table-new-row]")) {
        addEditableTableRow(form, false);
      }
    });
  }

  function removeEditableTableRow(form) {
    const row = getActiveEditableRow();
    if (!form || !row) return false;
    const deleteField = row.querySelector('[data-row-delete]');
    if (deleteField) {
      deleteField.value = "1";
      row.hidden = true;
    } else {
      row.remove();
    }
    markFormDirty(form);
    updateTablePagerVisibility(form);
    setupActionButtons();
    return true;
  }

  function focusEditableTableCell(currentField, direction) {
    const cell = currentField.closest("td");
    const row = currentField.closest("tr");
    const table = currentField.closest("table");
    if (!cell || !row || !table) return false;
    const cellIndex = Array.from(row.children).indexOf(cell);
    const rows = Array.from(table.querySelectorAll("tbody tr[data-editable-row]:not([hidden])"));
    const rowIndex = rows.indexOf(row);
    const nextRow = rows[rowIndex + direction];
    if (!nextRow && direction > 0) {
      const form = currentField.closest("form[data-editable-table]");
      if (form && addEditableTableRow(form)) return true;
    }
    const nextCell = nextRow?.children[cellIndex];
    const nextField = nextCell?.querySelector("input, select, textarea");
    if (!nextField) return false;
    nextField.focus();
    nextField.select?.();
    return true;
  }

  function getEditableTableFields(form) {
    const isQueryMode = document.body.classList.contains("screen-query-mode");
    return Array.from(form?.querySelectorAll("tbody tr[data-editable-row]:not([hidden]) input, tbody tr[data-editable-row]:not([hidden]) select, tbody tr[data-editable-row]:not([hidden]) textarea") || [])
      .filter((field) => {
        if (field.type === "hidden" || field.disabled || field.closest("tr")?.hidden) return false;
        if (field.readOnly && !(isQueryMode && field.dataset.primaryKey === "true")) return false;
        return true;
      });
  }

  function focusEditableTableNextField(currentField, reverse = false) {
    const form = currentField.closest("form[data-editable-table]");
    const fields = getEditableTableFields(form);
    const currentIndex = fields.indexOf(currentField);
    let target = fields[currentIndex + (reverse ? -1 : 1)];
    if (!target && !reverse && !document.body.classList.contains("screen-query-mode") && addEditableTableRow(form)) {
      target = getEditableTableFields(form).find((field) => !field.readOnly);
    }
    target = target || (reverse ? fields[fields.length - 1] : fields[0]);
    if (!target) return false;
    target.focus();
    target.select?.();
    return true;
  }

  async function handleCloseAction() {
    const form = getPrimaryForm();
    if (form?.dataset.dirty === "true") {
      const shouldSave = await showBlockingNotification({
        title: "Dados alterados",
        message: "Existem dados digitados. Deseja salvar antes de sair?",
        confirmText: "Salvar",
        cancelText: "Cancelar",
      });
      if (shouldSave) {
        await submitPrimaryForm(form);
        return;
      }
      const shouldDiscard = await showBlockingNotification({
        title: "Descartar alterações",
        message: "Descartar alterações e sair da tela?",
        confirmText: "Confirmar",
        cancelText: "Cancelar",
      });
      if (!shouldDiscard) return;
    }
    if (document.body.dataset.closeMode === "back") {
      window.location.href = document.body.dataset.closeUrl || document.body.dataset.tabKey || "/";
      return;
    }
    closeCurrentTab();
  }

  document.addEventListener("click", async function (event) {
    const overlayLink = event.target.closest("[data-screen-overlay-link]");
    if (overlayLink) {
      event.preventDefault();
      const overlay = document.querySelector("[data-screen-overlay]");
      const frame = overlay?.querySelector("[data-overlay-frame]");
      const title = overlay?.querySelector("[data-overlay-title]");
      if (overlay && frame) {
        const url = new URL(overlayLink.href, window.location.origin);
        url.searchParams.set("overlay", "1");
        frame.src = url.toString();
        if (title) title.textContent = overlayLink.textContent.trim() || "Cadastro auxiliar";
        overlay.hidden = false;
      }
      return;
    }

    const overlayClose = event.target.closest("[data-overlay-close]");
    if (overlayClose) {
      const overlay = overlayClose.closest("[data-screen-overlay]");
      const frame = overlay?.querySelector("[data-overlay-frame]");
      if (frame) frame.src = "about:blank";
      if (overlay) overlay.hidden = true;
      return;
    }

    const themeButton = event.target.closest("[data-theme-toggle]");
    if (themeButton) {
      root.classList.toggle("dark");
      const theme = root.classList.contains("dark") ? "dark" : "light";
      localStorage.setItem("celeris-theme", theme);
      if (document.body.dataset.username) {
        localStorage.setItem(`celeris-theme-user:${document.body.dataset.username}`, theme);
      }
      return;
    }

    const sidebarButton = event.target.closest("[data-sidebar-toggle]");
    if (sidebarButton) {
      shell?.classList.toggle("sidebar-collapsed");
      localStorage.setItem("celeris-sidebar", shell?.classList.contains("sidebar-collapsed") ? "collapsed" : "expanded");
      closeSidebarFlyout();
      scheduleSidebarAutoCollapse();
      return;
    }

    const queryButton = event.target.closest("[data-query-toggle]");
    if (queryButton) {
      const executing = queryButton.dataset.queryMode === "execute";
      const saveButton = document.querySelector('[data-action="save"]');
      const removeButton = document.querySelector('[data-action="remove"]');
      const form = document.querySelector(".content form");
      if (!executing) {
        if (form?.dataset.dirty === "true") {
          const shouldSave = await showBlockingNotification({
            title: "Dados alterados",
            message: "Existem dados alterados. Deseja salvar antes de abrir consulta?",
            confirmText: "Salvar",
            cancelText: "Não salvar",
          });
          if (shouldSave) {
            sessionStorage.setItem("celeris-open-query-after-save", "true");
            await submitPrimaryForm(form);
            return;
          }
          clearFormFields(form);
        }
        if (form?.matches("[data-editable-table]")) {
          resetEditableTableRows(form, false);
          window.history.replaceState({}, "", window.location.pathname);
        } else {
          clearFormFields(form);
        }
        setQueryMode(true);
        if (form?.matches("[data-editable-table]")) {
          prepareEditableTableQueryRow(form);
          const firstField = getEditableTableFields(form)[0];
          firstField?.focus();
          firstField?.select?.();
        }
        if (saveButton) saveButton.disabled = true;
        if (removeButton) removeButton.disabled = true;
      } else {
        if (form?.method?.toLowerCase() === "get") {
          form.requestSubmit();
          return;
        }
        const patientQueryTemplate = form?.dataset.patientQueryTemplate;
        const patientCode = form?.querySelector('[name="cd_paciente"]')?.value?.trim();
        if (patientQueryTemplate && patientCode) {
          window.location.href = patientQueryTemplate.replace("__ID__", encodeURIComponent(patientCode));
          return;
        }
        const queryUrl = form?.dataset.queryUrl;
        if (queryUrl) {
          const params = new URLSearchParams();
          Array.from(form.elements).forEach((field) => {
            if (!field.name || field.type === "hidden" || field.disabled || !String(field.value || "").trim()) return;
            if (field.matches('input[type="checkbox"], input[type="radio"]')) {
              if (field.checked) params.set(field.name, field.value || "true");
            } else if (field instanceof HTMLSelectElement && field.multiple) {
              Array.from(field.selectedOptions).forEach((option) => params.append(field.name, option.value));
            } else {
              params.set(field.name, field.value);
            }
          });
          if (["paciente", "prestador", "usuario"].includes(form.dataset.table)) {
            params.set("consultar", "1");
          } else {
            params.set("abrir", "1");
          }
          window.location.href = `${queryUrl}?${params.toString()}`;
          return;
        }
        if (form?.matches("[data-editable-table]")) {
          const queryValue = Array.from(form.querySelectorAll("input:not([type='hidden']), textarea, select"))
            .filter((field) => !field.readOnly && !field.disabled && String(field.value || "").trim())
            .map((field) => {
              if (field instanceof HTMLSelectElement) return field.value.trim();
              return field.value.trim();
            })[0] || "";
          clearCurrentFormState(form);
          const params = queryValue ? `?q=${encodeURIComponent(queryValue)}` : "?consultar=1";
          storeCurrentListPosition();
          window.location.href = `${window.location.pathname}${params}`;
          return;
        }
        setQueryMode(false);
        setupActionButtons();
      }
      renderIcons();
      return;
    }

    const cancelQueryButton = event.target.closest("[data-query-cancel]");
    if (cancelQueryButton) {
      clearFormFields(getPrimaryForm());
      setupActionButtons();
      renderIcons();
      return;
    }

    const closeAction = event.target.closest('[data-action="close"]');
    if (closeAction) {
      await handleCloseAction();
      return;
    }

    const saveAction = event.target.closest('[data-action="save"]');
    if (saveAction && !saveAction.disabled) {
      const form = document.querySelector(".content form");
      if (form) {
        storeCurrentListPosition();
        await submitPrimaryForm(form);
      }
      return;
    }

    const newAction = event.target.closest('[data-action="new"]');
    if (newAction && !newAction.disabled) {
      const tableForm = getEditableTableForm();
      if (tableForm && addEditableTableRow(tableForm)) return;
      const targetUrl = document.body.dataset.newUrl;
      if (targetUrl) {
        storeCurrentListPosition();
        const url = new URL(targetUrl, window.location.origin);
        if (url.origin === window.location.origin && !url.searchParams.has("return_to")) {
          url.searchParams.set("return_to", `${window.location.pathname}${window.location.search}`);
        }
        window.location.href = url.toString();
      }
      return;
    }

    const continueAction = event.target.closest('[data-action="continue"]');
    if (continueAction && !continueAction.disabled) {
      const targetUrl = document.body.dataset.continueUrl;
      if (targetUrl) window.location.href = targetUrl;
      return;
    }

    const removeAction = event.target.closest('[data-action="remove"]');
    if (removeAction && !removeAction.disabled) {
      const tableForm = getEditableTableForm();
      if (tableForm && removeEditableTableRow(tableForm)) return;
    }

    const toggleActiveAction = event.target.closest('[data-action="toggle-active"]');
    if (toggleActiveAction && !toggleActiveAction.disabled) {
      const tableForm = getEditableTableForm();
      const rowActiveField = getSelectedRowActiveField(tableForm);
      if (rowActiveField) {
        rowActiveField.value = rowActiveField.value === "true" ? "false" : "true";
        rowActiveField.dispatchEvent(new Event("change", { bubbles: true }));
        markFormDirty(tableForm);
        setupActionButtons();
        return;
      }
      if (!document.body.dataset.toggleActiveUrl) return;
      const confirmed = await showBlockingNotification({
        title: toggleActiveAction.title,
        message: `Confirma a ação de ${toggleActiveAction.title.toLowerCase()} este cadastro?`,
        confirmText: "Confirmar",
        cancelText: "Cancelar",
      });
      if (!confirmed) return;
      const csrfToken = document.querySelector(".content form [name='csrfmiddlewaretoken']")?.value;
      const response = await fetch(document.body.dataset.toggleActiveUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken || "" },
      });
      if (response.redirected) window.location.href = response.url;
      return;
    }

    const changePasswordAction = event.target.closest('[data-action="change-password"]');
    if (changePasswordAction && !changePasswordAction.disabled && document.body.dataset.passwordUrl) {
      const overlay = document.querySelector("[data-screen-overlay]");
      const frame = overlay?.querySelector("[data-overlay-frame]");
      const title = overlay?.querySelector("[data-overlay-title]");
      if (overlay && frame) {
        const url = new URL(document.body.dataset.passwordUrl, window.location.origin);
        url.searchParams.set("overlay", "1");
        frame.src = url.toString();
        if (title) title.textContent = "Alterar Senha";
        overlay.hidden = false;
      }
      return;
    }

    const clearAction = event.target.closest('[data-action="clear"]');
    if (clearAction && !clearAction.disabled) {
      clearScreenData();
      setupActionButtons();
      renderIcons();
      return;
    }

    const previousAction = event.target.closest('[data-action="previous"]');
    if (previousAction && !previousAction.disabled && document.body.dataset.previousUrl) {
      window.location.href = document.body.dataset.previousUrl;
      return;
    }

    const firstAction = event.target.closest('[data-action="first"]');
    if (firstAction && !firstAction.disabled && document.body.dataset.firstUrl) {
      window.location.href = document.body.dataset.firstUrl;
      return;
    }

    const nextAction = event.target.closest('[data-action="next"]');
    if (nextAction && !nextAction.disabled && document.body.dataset.nextUrl) {
      window.location.href = document.body.dataset.nextUrl;
      return;
    }

    const lastAction = event.target.closest('[data-action="last"]');
    if (lastAction && !lastAction.disabled && document.body.dataset.lastUrl) {
      window.location.href = document.body.dataset.lastUrl;
      return;
    }

    const tabClose = event.target.closest("[data-tab-close]");
    if (tabClose) {
      event.preventDefault();
      event.stopPropagation();
      closeTab(tabClose.dataset.tabUrl, tabClose.dataset.tabKey || tabClose.dataset.tabUrl);
      return;
    }

    const lookupTrigger = event.target.closest("[data-lookup-trigger]");
    if (lookupTrigger) {
      const field = lookupTrigger.closest(".field-lookup-wrap")?.querySelector("[data-lookup-table]");
      if (field) openLookup(field);
      return;
    }

    const lookupClose = event.target.closest("[data-lookup-close]");
    if (lookupClose) {
      closeLookup();
      return;
    }

    const lookupRun = event.target.closest("[data-lookup-run]");
    if (lookupRun) {
      runLookup(lookupRun.closest("[data-lookup-modal]"));
      return;
    }

    const lookupSelect = event.target.closest("[data-lookup-select]");
    if (lookupSelect && activeLookupField) {
      activeLookupField.value = lookupSelect.dataset.value || "";
      activeLookupField.dispatchEvent(new Event("input", { bubbles: true }));
      closeLookup();
      return;
    }

    const notificationsToggle = event.target.closest("[data-notifications-toggle]");
    if (notificationsToggle) {
      const panel = document.querySelector("[data-notifications-panel]");
      if (panel) panel.hidden = !panel.hidden;
      return;
    }

    const notificationsClear = event.target.closest("[data-notifications-clear]");
    if (notificationsClear) {
      localStorage.removeItem("celeris-notifications");
      const empty = document.createElement("div");
      empty.className = "notification-empty";
      empty.textContent = "Nenhuma notificação.";
      document.querySelector(".notifications-list")?.replaceChildren(empty);
      document.querySelector(".notification-badge")?.remove();
      return;
    }

    const notificationItem = event.target.closest("[data-notification-item]");
    if (notificationItem) {
      notificationItem.classList.toggle("open");
      return;
    }

    const collapsedSummary = event.target.closest(".sidebar .nav-group > summary");
    if (collapsedSummary && shell?.classList.contains("sidebar-collapsed")) {
      event.preventDefault();
      openSidebarFlyout(collapsedSummary.closest(".nav-group"), collapsedSummary);
      scheduleSidebarAutoCollapse();
      return;
    }

    if (collapsedSummary) {
      closeSidebarFlyout();
      closeSiblingNavGroups(collapsedSummary);
      scheduleSidebarAutoCollapse();
      return;
    }

    if (sidebarFlyout && !event.target.closest(".sidebar-flyout")) {
      closeSidebarFlyout();
    }
    const floatingSourceId = activeFloatingSelect?.dataset.fieldId;
    const clickedFloatingSource = floatingSourceId && event.target.closest(`#${CSS.escape(floatingSourceId)}`);
    if (activeFloatingSelect && !event.target.closest("[data-floating-select]") && !clickedFloatingSource) {
      closeFloatingSelect();
    }

    const editableCell = event.target.closest("form[data-editable-table] td");
    if (editableCell) {
      editableCell.closest("tbody")?.querySelectorAll("tr.selected").forEach((row) => row.classList.remove("selected"));
      editableCell.closest("tr[data-editable-row]")?.classList.add("selected");
      setupActionButtons();
    }

    const notificationsPanel = document.querySelector("[data-notifications-panel]");
    if (notificationsPanel && !notificationsPanel.hidden && !event.target.closest("[data-notifications-panel]")) {
      notificationsPanel.hidden = true;
    }
  });

  document.addEventListener("mousedown", function (event) {
    const select = event.target.closest(".content select");
    if (!select || select.closest("[data-blocking-notification]")) return;
    event.preventDefault();
    select.focus();
    if (activeFloatingSelect?.dataset.fieldId === select.id) return;
    openFloatingSelect(select);
  });

  document.addEventListener("click", function (event) {
    const select = event.target.closest(".content select");
    if (!select || select.closest("[data-blocking-notification]")) return;
    event.preventDefault();
    event.stopPropagation();
  });

  document.addEventListener("submit", function (event) {
    if (event.target.matches("[data-clear-tabs]")) {
      localStorage.removeItem("celeris-tabs");
    }
    if (event.target.matches(".content form") && event.target.method?.toLowerCase() !== "get") {
      clearCurrentFormState(event.target);
    }
    if (event.target.matches(".content form")) markInvalidFields(event.target);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      const overlay = document.querySelector("[data-screen-overlay]:not([hidden])");
      if (overlay) {
        const frame = overlay.querySelector("[data-overlay-frame]");
        if (frame) frame.src = "about:blank";
        overlay.hidden = true;
        return;
      }
      reverseEnterRequested = true;
      closeLookup();
      closeFloatingSelect();
      window.setTimeout(() => {
        reverseEnterRequested = false;
      }, 1200);
      return;
    }

    if (
      /^[1-6]$/.test(event.key)
      && document.querySelector(".provider-form")
      && !event.ctrlKey
      && !event.altKey
      && !event.metaKey
      && !event.target.matches("input, select, textarea, button, [contenteditable='true']")
    ) {
      const section = document.querySelector(`[data-provider-section="${event.key}"]`);
      if (section) {
        event.preventDefault();
        section.open = true;
        section.scrollIntoView({ behavior: "smooth", block: "start" });
        const firstField = Array.from(section.querySelectorAll("input, select, textarea"))
          .find((field) => field.type !== "hidden" && !field.disabled && !field.readOnly);
        window.setTimeout(() => focusField(firstField), 180);
      }
      return;
    }

    if (event.key === "ArrowDown" && event.target.matches("form[data-editable-table] input, form[data-editable-table] select, form[data-editable-table] textarea")) {
      if (!event.target.matches("select")) {
        event.preventDefault();
        focusEditableTableCell(event.target, 1);
      }
      return;
    }
    if (event.key === "ArrowUp" && event.target.matches("form[data-editable-table] input, form[data-editable-table] select, form[data-editable-table] textarea")) {
      if (!event.target.matches("select")) {
        event.preventDefault();
        focusEditableTableCell(event.target, -1);
      }
      return;
    }
    if (event.key === "Enter" && event.target.matches("[data-lookup-search]")) {
      event.preventDefault();
      runLookup(event.target.closest("[data-lookup-modal]"));
    }
    if (event.key === "Enter" && event.target.matches("form[data-editable-table] input, form[data-editable-table] select, form[data-editable-table] textarea")) {
      event.preventDefault();
      focusEditableTableNextField(event.target, event.shiftKey || reverseEnterRequested);
      reverseEnterRequested = false;
      return;
    }
    if (event.key === "Tab" && event.target.matches("form[data-editable-table] input, form[data-editable-table] select, form[data-editable-table] textarea")) {
      event.preventDefault();
      focusEditableTableNextField(event.target, event.shiftKey);
      return;
    }
    if (
      event.target.matches(".content select")
      && (
        event.key === "Enter"
        || event.key === "ArrowDown"
        || event.key === "ArrowUp"
        || (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey)
      )
    ) {
      event.preventDefault();
      const field = event.target;
      const isCurrentFloatingSelect = getFloatingSelectField() === field;
      if (!isCurrentFloatingSelect) openFloatingSelect(field);
      if (event.key === "Enter" && isCurrentFloatingSelect) {
        activeFloatingSelect?.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
      } else if (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key.length === 1) {
        window.setTimeout(() => {
          activeFloatingSelect?.dispatchEvent(new KeyboardEvent("keydown", { key: event.key, bubbles: true }));
        });
      }
      return;
    }
    if (event.key === "Enter" && event.target.matches(".content input, .content select, .content textarea")) {
      const field = event.target;
      event.preventDefault();
      if (event.shiftKey || reverseEnterRequested) {
        reverseEnterRequested = false;
        focusPreviousField(field);
      } else {
        focusNextField(field);
      }
    }
    if (event.key === "Tab" && !event.shiftKey && event.target.matches(".content input, .content select, .content textarea")) {
      const field = event.target;
      const visibleFields = getNavigableFields().filter((input) => input.offsetParent !== null);
      if (visibleFields[visibleFields.length - 1] === field) {
        event.preventDefault();
        focusNextField(field);
      }
    }
  });

  function getNavigableFields(includeClosed = false) {
    return Array.from(document.querySelectorAll(".content input, .content select, .content textarea"))
      .filter((field) => {
        if (field.closest("[hidden]")) return false;
        if (field.type === "hidden" || field.disabled || field.readOnly) return false;
        return includeClosed || field.offsetParent !== null;
      });
  }

  function focusNextField(currentField) {
    const fields = getNavigableFields(true);
    const currentIndex = fields.indexOf(currentField);
    let nextField = fields[currentIndex + 1];
    const nextSection = nextField?.closest("details");
    const currentSection = currentField.closest("details");
    if (nextSection && nextSection !== currentSection) {
      nextSection.open = true;
    }
    nextField = nextField || fields[0];
    if (!nextField) return;
    window.requestAnimationFrame(() => focusField(nextField));
  }

  function focusPreviousField(currentField) {
    const fields = getNavigableFields(true);
    const currentIndex = fields.indexOf(currentField);
    let previousField = fields[currentIndex - 1];
    previousField = previousField || fields[fields.length - 1];
    const previousSection = previousField?.closest("details");
    if (previousSection) previousSection.open = true;
    if (!previousField) return;
    window.requestAnimationFrame(() => focusField(previousField));
  }

  function closeFloatingSelect() {
    activeFloatingSelect?.remove();
    activeFloatingSelect = null;
    floatingSelectSearch = "";
    window.clearTimeout(floatingSelectSearchTimer);
  }

  function getFloatingSelectField() {
    const fieldId = activeFloatingSelect?.dataset.fieldId;
    return fieldId ? document.getElementById(fieldId) : null;
  }

  function positionFloatingSelect(panel, field) {
    const rect = field.getBoundingClientRect();
    const gap = 4;
    const width = Math.max(rect.width, 180);
    panel.style.width = `${width}px`;
    panel.style.left = `${Math.min(rect.left, window.innerWidth - width - gap)}px`;
    panel.style.top = `${Math.min(rect.bottom + gap, window.innerHeight - panel.offsetHeight - gap)}px`;
  }

  function openFloatingSelect(field) {
    closeFloatingSelect();
    const options = Array.from(field.options).filter((option) => !option.disabled);
    if (!options.length) return;
    const panel = document.createElement("div");
    panel.className = "floating-select-panel";
    panel.dataset.floatingSelect = "true";
    if (!field.id) field.id = `floating-select-${Date.now()}`;
    panel.dataset.fieldId = field.id;
    panel.innerHTML = options.map((option, index) => {
      const isEmpty = !option.value && !(option.text || "").trim();
      return `
      <button type="button" data-select-index="${index}" ${isEmpty ? 'data-empty-option="true"' : ""} class="${option.selected ? "active" : ""}">
        ${escapeHTML(option.text || option.value || "EM BRANCO")}
      </button>
    `;
    }).join("");
    document.body.appendChild(panel);
    activeFloatingSelect = panel;
    positionFloatingSelect(panel, field);
    const setActiveOption = (button) => {
      if (!button) return;
      panel.querySelectorAll("button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      button.scrollIntoView({ block: "nearest" });
    };
    const selectOption = (button) => {
      const option = options[Number(button.dataset.selectIndex)];
      if (!option) return;
      if (field.multiple) {
        option.selected = !option.selected;
        button.classList.toggle("active", option.selected);
        field.dispatchEvent(new Event("change", { bubbles: true }));
        return;
      }
      field.value = option.value;
      field.dispatchEvent(new Event("change", { bubbles: true }));
      closeFloatingSelect();
      focusNextField(field);
    };
    panel.addEventListener("mousedown", (event) => {
      if (event.target.closest("button")) event.preventDefault();
    });
    panel.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (button) selectOption(button);
    });
    panel.addEventListener("keydown", (event) => {
      const buttons = Array.from(panel.querySelectorAll("button"));
      const current = document.activeElement.closest?.("button") || panel.querySelector("button.active");
      const currentIndex = Math.max(buttons.indexOf(current), 0);
      if (event.key === "ArrowDown") {
        event.preventDefault();
        const nextButton = buttons[Math.min(currentIndex + 1, buttons.length - 1)];
        setActiveOption(nextButton);
        nextButton?.focus();
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        const previousButton = buttons[Math.max(currentIndex - 1, 0)];
        setActiveOption(previousButton);
        previousButton?.focus();
      } else if (event.key === "Enter") {
        event.preventDefault();
        if (event.shiftKey || reverseEnterRequested) {
          reverseEnterRequested = false;
          closeFloatingSelect();
          focusPreviousField(field);
        } else {
          selectOption(current || panel.querySelector("button.active") || buttons[0]);
        }
      } else if (event.key === "Tab") {
        event.preventDefault();
        closeFloatingSelect();
        if (event.shiftKey) {
          focusPreviousField(field);
        } else {
          focusNextField(field);
        }
      } else if (event.key === "Escape") {
        closeFloatingSelect();
        field.focus();
      } else if (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey) {
        floatingSelectSearch += event.key.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
        window.clearTimeout(floatingSelectSearchTimer);
        floatingSelectSearchTimer = window.setTimeout(() => {
          floatingSelectSearch = "";
        }, 900);
        const match = buttons.find((button) => (
          button.textContent || ""
        ).normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase().startsWith(floatingSelectSearch));
        if (match) {
          event.preventDefault();
          setActiveOption(match);
          match.focus();
        }
      }
    });
    window.requestAnimationFrame(() => {
      const activeButton = panel.querySelector("button.active:not([data-empty-option='true'])")
        || panel.querySelector("button:not([data-empty-option='true'])")
        || panel.querySelector("button");
      setActiveOption(activeButton);
      activeButton?.focus();
    });
  }

  function focusField(field) {
    field.focus();
    if (field instanceof HTMLInputElement) field.select?.();
  }

  window.addEventListener("resize", () => {
    closeSidebarFlyout();
    closeFloatingSelect();
  });
  window.addEventListener("scroll", () => {
    closeSidebarFlyout();
    if (activeFloatingSelect) {
      const fieldId = activeFloatingSelect.dataset.fieldId;
      const field = fieldId ? document.getElementById(fieldId) : null;
      if (field) positionFloatingSelect(activeFloatingSelect, field);
    }
  }, true);

  function normalizeFieldName(value) {
    return value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z0-9_]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .toUpperCase();
  }

  function normalizeTextValue(value) {
    return value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z0-9_% ]+/g, "")
      .toUpperCase();
  }

  function updateFieldStatus(field) {
    const status = document.querySelector("[data-field-status]");
    if (!status) return;

    if (!field) {
      status.textContent = "";
      return;
    }

    const labelText = field.closest("label")?.childNodes?.[0]?.textContent?.trim() || "";
    const businessLabel = labelText || field.getAttribute("aria-label") || field.placeholder || "Campo";
    const owner = field.closest("form[data-table], section[data-table]");
    const tableName = owner?.dataset.table;
    const rawFieldName = field.dataset.fieldName || field.name || "";
    const fieldName = rawFieldName.replace(/^new_/, "").replace(/_\d+$/, "");
    const isExactTableField = Boolean(
      tableName
      && fieldName
      && owner?.tagName === "FORM"
      && owner.method?.toLowerCase() !== "get"
      && field.type !== "hidden"
    );
    status.textContent = isExactTableField
      ? `${normalizeFieldName(tableName)}.${normalizeFieldName(fieldName)}`
      : businessLabel.trim();
  }

  function normalizeInputValue(field) {
    if (!(field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement)) return;
    if (field.dataset.mask) return;
    const type = field.type || "";
    if (["password", "email", "url", "number", "date", "time", "datetime-local", "month", "week"].includes(type)) return;
    const start = field.selectionStart;
    const end = field.selectionEnd;
    field.value = normalizeTextValue(field.value);
    if (typeof start === "number" && typeof end === "number") {
      field.setSelectionRange(start, end);
    }
  }

  document.addEventListener("focusin", function (event) {
    const field = event.target.closest("input, select, textarea");
    if (field) updateFieldStatus(field);
  });

  document.addEventListener("focusout", function (event) {
    return;
  });

  document.addEventListener("input", function (event) {
    const field = event.target.closest("input, textarea");
    if (!field) return;
    if (!field.closest("[data-preserve-input]")) {
      normalizeInputValue(field);
    }
    if (field.matches("[data-war-name]")) {
      field.dataset.manuallyEdited = "true";
    }
    if (field.matches("[data-war-name-source]")) {
      const warNameField = document.querySelector("[data-war-name]");
      const providerForm = field.closest(".provider-form");
      const isNewProvider = providerForm && !providerForm.dataset.providerId;
      const isQueryMode = document.body.classList.contains("screen-query-mode");
      if (warNameField && isNewProvider && !isQueryMode && !warNameField.value.trim() && !warNameField.dataset.manuallyEdited) {
        const nameParts = field.value.trim().split(/\s+/).filter(Boolean);
        warNameField.value = nameParts[0] || "";
      }
    }
    if (field.dataset.mask === "cpf") {
      field.value = formatCPF(field.value);
    } else if (field.dataset.mask === "celular") {
      field.value = formatCellphone(field.value);
    }
    if (isRestoringFormState) return;
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = false;
    setActionStatus("EDIÇÃO");
    const form = field.closest("form");
    form?.setAttribute("data-dirty", "true");
    persistCurrentFormState(form);
  });

  document.addEventListener("change", function (event) {
    if (!event.target.closest("input, select, textarea")) return;
    if (event.target.matches("[data-state-select]")) {
      loadCitiesForState(event.target.value);
    }
    if (event.target.matches("[data-linked-state]")) {
      loadLinkedCities(event.target.dataset.linkedState, event.target.value);
    }
    if (event.target.matches("[data-linked-cep]")) {
      loadAddressForCep(event.target.dataset.linkedCep, event.target.value);
    }
    if (event.target.matches("[data-option-label-target]")) {
      syncLinkedOptionLabel(event.target);
    }
    if (event.target.matches("[data-cep-state-select]")) {
      filterCepCitiesForState(event.target);
    }
    if (isRestoringFormState) return;
    if (event.target.matches("[data-provider-type]")) {
      const councilField = document.querySelector("[data-provider-council]");
      let councilMap = {};
      try {
        councilMap = JSON.parse(event.target.dataset.councilMap || "{}");
      } catch (error) {
        councilMap = {};
      }
      const council = councilMap[event.target.value];
      if (councilField && council) {
        councilField.value = council;
        councilField.dispatchEvent(new Event("change", { bubbles: true }));
      } else if (event.target.value) {
        if (councilField) councilField.value = "";
        showBlockingNotification({
          title: "Conselho não vinculado",
          message: "Este tipo de prestador não possui conselho vinculado. O cadastro pode continuar normalmente.",
          confirmText: "Ignorar",
          cancelText: "Fechar",
          type: "info",
          initialFocus: "cancel",
        }).then((ignored) => {
          if (ignored) {
            focusNextField(event.target);
          } else {
            event.target.focus();
          }
        });
      }
      if (event.target.matches("[data-provider-permissions]")) {
        applyProviderPermissionSuggestions(event.target.value);
      }
    }
    if (event.target.matches("[data-user-provider]") && event.target.value) {
      fetch(`/accounts/usuarios/prestador/${encodeURIComponent(event.target.value)}/dados/`)
        .then((response) => response.json())
        .then((payload) => {
          Object.entries(payload).forEach(([fieldName, value]) => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (!field || field.value || !value) return;
            if (field instanceof HTMLSelectElement && !Array.from(field.options).some((option) => option.value === value)) {
              field.add(new Option(value, value));
            }
            field.value = value;
            field.dispatchEvent(new Event("input", { bubbles: true }));
          });
        });
    }
    if (event.target.matches("[data-same-address]")) {
      copyResidentialAddressToCommercial(event.target.checked);
    }
    if (isRestoringFormState) return;
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = false;
    setActionStatus("EDIÇÃO");
    const form = event.target.closest("form");
    form?.setAttribute("data-dirty", "true");
    persistCurrentFormState(form);
  });

  async function loadCitiesForState(state) {
    const citySelect = document.querySelector("[data-city-select]");
    if (!citySelect) return;
    citySelect.innerHTML = '<option value=""></option>';
    if (!state) return;
    const response = await fetch(`/global/tabelas/auxiliares/cidades-opcoes/?uf=${encodeURIComponent(state)}`);
    const payload = await response.json();
    citySelect.innerHTML = '<option value=""></option>' + (payload.cidades || [])
      .map((city) => `<option value="${escapeHTML(city.value)}">${escapeHTML(city.label)}</option>`)
      .join("");
  }

  function isValidCPF(value) {
    const digits = onlyDigits(value);
    if (digits.length !== 11 || /^(\d)\1{10}$/.test(digits)) return false;
    const calculate = (size) => {
      let total = 0;
      for (let index = 0; index < size; index += 1) {
        total += Number(digits[index]) * (size + 1 - index);
      }
      return (total * 10 % 11) % 10;
    };
    return calculate(9) === Number(digits[9]) && calculate(10) === Number(digits[10]);
  }

  async function loadLinkedCities(group, state, selectedValue = "") {
    const citySelect = document.querySelector(`[data-linked-city="${CSS.escape(group)}"]`);
    if (!citySelect) return;
    citySelect.innerHTML = '<option value=""></option>';
    if (!state) return;
    const response = await fetch(`/global/tabelas/auxiliares/cidades-opcoes/?uf=${encodeURIComponent(state)}`);
    const payload = await response.json();
    citySelect.innerHTML = '<option value=""></option>' + (payload.cidades || [])
      .map((city) => `<option value="${escapeHTML(city.value)}">${escapeHTML(city.label)}</option>`)
      .join("");
    citySelect.value = selectedValue;
  }

  async function loadAddressForCep(group, cep) {
    if (!cep) return;
    const response = await fetch(`/global/tabelas/auxiliares/cep-opcao/?cep=${encodeURIComponent(cep)}`);
    const payload = await response.json();
    if (!payload.estado) {
      const shouldOpen = await showBlockingNotification({
        title: "CEP não cadastrado",
        message: "O CEP informado não existe no cadastro global. Deseja abrir a tela de CEPs?",
        confirmText: "Abrir CEPs",
        cancelText: "Continuar manualmente",
        type: "info",
      });
      if (shouldOpen) window.location.href = "/global/ceps/";
      return;
    }
    const stateSelect = document.querySelector(`[data-linked-state="${CSS.escape(group)}"]`);
    if (stateSelect) {
      stateSelect.value = payload.estado;
      await loadLinkedCities(group, payload.estado, payload.cidade || "");
    }
    const suffix = group === "comercial" ? "_comercial" : "";
    const addressFields = {
      [`tp_logradouro${suffix}`]: payload.tipo_logradouro,
      [`ds_endereco${suffix}`]: payload.logradouro,
      [`ds_bairro${suffix}`]: payload.bairro,
    };
    Object.entries(addressFields).forEach(([fieldName, value]) => {
      const field = document.querySelector(`[name="${fieldName}"]`);
      if (!field || !value) return;
      if (field instanceof HTMLSelectElement && !Array.from(field.options).some((option) => option.value === value)) {
        field.add(new Option(value, value));
      }
      field.value = value;
      field.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  function validateStructuredField(field, notify = false) {
    if (!field?.value?.trim()) {
      field?.classList.remove("field-invalid");
      field?.setCustomValidity?.("");
      return true;
    }
    let message = "";
    if (field.matches("[data-validate-cpf]") && !isValidCPF(field.value)) {
      message = "Informe um CPF válido.";
    } else if (field.matches("[data-validate-email]") && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value)) {
      message = "Informe um e-mail válido.";
    } else if (field.matches("[data-validate-cnes]") && !/^\d{7}$/.test(onlyDigits(field.value))) {
      message = "O CNES deve conter exatamente 7 dígitos.";
    }
    field.classList.toggle("field-invalid", Boolean(message));
    field.setCustomValidity(message);
    if (message && notify) {
      showBlockingNotification({
        title: "Valor inválido",
        message,
        confirmText: "OK",
        type: "error",
        focusTarget: field,
      });
    }
    return !message;
  }

  document.addEventListener("blur", async function (event) {
    const structuredField = event.target.closest("[data-validate-cpf], [data-validate-email], [data-validate-cnes]");
    if (structuredField && !validateStructuredField(structuredField, true)) return;
    const field = event.target.closest("[data-unique-patient]");
    if (!field || !field.value.trim()) return;
    const currentValue = field.value.trim();
    if (field.dataset.duplicateCheckedValue === currentValue) return;
    const form = field.closest("form");
    const params = new URLSearchParams({
      field: field.dataset.uniquePatient,
      value: currentValue,
      paciente: form?.dataset.patientId || "",
    });
    const response = await fetch(`/atendimento/pacientes/verificar-unico/?${params.toString()}`);
    const payload = await response.json();
    field.dataset.duplicateCheckedValue = currentValue;
    if (!payload.exists) {
      field.classList.remove("field-duplicate");
      field.setCustomValidity("");
      return;
    }
    field.classList.add("field-duplicate");
    field.setCustomValidity(payload.message || "Dado j? cadastrado.");
    await showBlockingNotification({
      title: "Registro já cadastrado",
      message: payload.message || "Dado já cadastrado para outro paciente.",
      confirmText: "OK",
      store: true,
      type: "error",
      focusTarget: field,
    });
  }, true);

  document.addEventListener("input", function (event) {
    const field = event.target.closest("[data-unique-patient]");
    const structuredField = event.target.closest("[data-validate-cpf], [data-validate-email], [data-validate-cnes]");
    if (structuredField) validateStructuredField(structuredField);
    if (!field) return;
    field.classList.remove("field-duplicate");
    field.setCustomValidity("");
    field.dataset.duplicateCheckedValue = "";
  });

  function onlyDigits(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function formatCPF(value) {
    const digits = onlyDigits(value).slice(0, 11);
    return digits
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d{1,2})/, "$1.$2.$3-$4");
  }

  function formatCellphone(value) {
    const digits = onlyDigits(value).slice(0, 11);
    if (digits.length <= 2) return digits.replace(/^(\d{0,2})/, "($1");
    if (digits.length <= 7) return digits.replace(/^(\d{2})(\d{0,1})(\d{0,4})/, "($1) $2 $3").trim();
    return digits.replace(/^(\d{2})(\d{1})(\d{4})(\d{0,4})/, "($1) $2 $3-$4").trim();
  }

  function setupSpecialtyManager() {
    const manager = document.querySelector("[data-specialty-manager]");
    if (!manager) return;
    const storage = manager.querySelector("[data-specialty-values]");
    const picker = manager.querySelector("[data-specialty-picker]");
    const chips = manager.querySelector("[data-specialty-chips]");
    const addButton = manager.querySelector("[data-specialty-add]");
    const openButton = manager.querySelector("[data-specialty-open]");
    const addRow = manager.querySelector("[data-specialty-add-row]");
    const primary = document.querySelector("[data-primary-specialty]");
    if (!storage || !picker || !chips || !addButton || !openButton || !addRow) return;

    const options = Array.from(storage.options).map((option) => ({
      value: option.value,
      label: option.textContent.trim(),
    })).filter((option) => option.value);

    const selectedValues = () => Array.from(storage.selectedOptions).map((option) => option.value);

    const render = () => {
      const selected = new Set(selectedValues());
      chips.innerHTML = options
        .filter((option) => selected.has(option.value))
        .map((option) => (
          `<span class="specialty-chip">${escapeHTML(option.label)}`
          + `<button type="button" data-specialty-remove="${escapeHTML(option.value)}" aria-label="Remover ${escapeHTML(option.label)}">&times;</button></span>`
        ))
        .join("");
      if (!chips.children.length) {
        chips.innerHTML = '<span class="specialty-empty">Nenhuma especialidade adicionada.</span>';
      }

      const pickerValue = picker.value;
      picker.innerHTML = '<option value="">Adicionar especialidade...</option>' + options
        .filter((option) => !selected.has(option.value))
        .map((option) => `<option value="${escapeHTML(option.value)}">${escapeHTML(option.label)}</option>`)
        .join("");
      picker.value = Array.from(picker.options).some((option) => option.value === pickerValue) ? pickerValue : "";

      if (primary) {
        const currentPrimary = primary.value;
        primary.innerHTML = '<option value=""></option>' + options
          .filter((option) => selected.has(option.value))
          .map((option) => `<option value="${escapeHTML(option.value)}">${escapeHTML(option.label)}</option>`)
          .join("");
        primary.value = selected.has(currentPrimary) ? currentPrimary : (selectedValues()[0] || "");
      }
    };

    const addSelected = () => {
      if (!picker.value) return;
      const option = Array.from(storage.options).find((item) => item.value === picker.value);
      if (option) {
        option.selected = true;
        storage.dispatchEvent(new Event("change", { bubbles: true }));
      }
      render();
      addRow.hidden = false;
      openButton.hidden = true;
      picker.focus();
    };

    const resetInterface = () => {
      picker.value = "";
      addRow.hidden = true;
      openButton.hidden = false;
      render();
    };

    openButton.addEventListener("click", () => {
      openButton.hidden = true;
      addRow.hidden = false;
      picker.focus();
    });
    addButton.addEventListener("click", addSelected);
    picker.addEventListener("change", addSelected);
    picker.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      addSelected();
    });
    storage.addEventListener("change", render);
    manager.closest("form")?.addEventListener("celeris:reset-multiselects", resetInterface);
    chips.addEventListener("click", (event) => {
      const removeButton = event.target.closest("[data-specialty-remove]");
      if (!removeButton) return;
      const option = Array.from(storage.options).find((item) => item.value === removeButton.dataset.specialtyRemove);
      if (option) {
        option.selected = false;
        storage.dispatchEvent(new Event("change", { bubbles: true }));
      }
      render();
    });
    render();
  }

  function setupAssignmentManagers() {
    document.querySelectorAll("[data-assignment-manager]").forEach((manager) => {
      const storage = manager.querySelector("[data-assignment-values]");
      const picker = manager.querySelector("[data-assignment-picker]");
      const chips = manager.querySelector("[data-assignment-chips]");
      const addButton = manager.querySelector("[data-assignment-add]");
      const openButton = manager.querySelector("[data-assignment-open]");
      const addRow = manager.querySelector("[data-assignment-add-row]");
      if (!storage || !picker || !chips || !addButton || !openButton || !addRow) return;
      const options = Array.from(storage.options)
        .filter((option) => option.value)
        .map((option) => ({ value: option.value, label: option.textContent.trim() }));
      const selectedValues = () => Array.from(storage.selectedOptions).map((option) => option.value);

      const render = () => {
        const selected = new Set(selectedValues());
        chips.innerHTML = options
          .filter((option) => selected.has(option.value))
          .map((option) => (
            `<span class="specialty-chip">${escapeHTML(option.label)}`
            + `<button type="button" data-assignment-remove="${escapeHTML(option.value)}" aria-label="Remover ${escapeHTML(option.label)}">&times;</button></span>`
          ))
          .join("");
        if (!chips.children.length) {
          chips.innerHTML = `<span class="specialty-empty">${escapeHTML(manager.dataset.assignmentEmpty || "Nenhum item atribuído.")}</span>`;
        }
        picker.innerHTML = '<option value="">Selecionar...</option>' + options
          .filter((option) => !selected.has(option.value))
          .map((option) => `<option value="${escapeHTML(option.value)}">${escapeHTML(option.label)}</option>`)
          .join("");
      };

      const addSelected = () => {
        const option = Array.from(storage.options).find((item) => item.value === picker.value);
        if (!option) return;
        option.selected = true;
        storage.dispatchEvent(new Event("change", { bubbles: true }));
        render();
        picker.focus();
      };

      const resetInterface = () => {
        picker.value = "";
        addRow.hidden = true;
        openButton.hidden = false;
        render();
      };

      openButton.addEventListener("click", () => {
        openButton.hidden = true;
        addRow.hidden = false;
        picker.focus();
      });
      addButton.addEventListener("click", addSelected);
      picker.addEventListener("change", addSelected);
      picker.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        addSelected();
      });
      storage.addEventListener("change", render);
      manager.closest("form")?.addEventListener("celeris:reset-multiselects", resetInterface);
      chips.addEventListener("click", (event) => {
        const removeButton = event.target.closest("[data-assignment-remove]");
        if (!removeButton) return;
        const option = Array.from(storage.options).find(
          (item) => item.value === removeButton.dataset.assignmentRemove
        );
        if (option) {
          option.selected = false;
          storage.dispatchEvent(new Event("change", { bubbles: true }));
        }
        render();
      });
      render();
    });
  }

  function setupRoleModuleVisibility() {
    const moduleFields = document.querySelectorAll("[data-role-module]");
    if (!moduleFields.length) return;
    const update = () => {
      moduleFields.forEach((field) => {
        const section = document.querySelector(`[data-role-screen-module="${field.dataset.roleModule}"]`);
        if (!section) return;
        section.hidden = !field.checked;
        if (!field.checked) {
          section.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
            checkbox.checked = false;
          });
        }
      });
    };
    moduleFields.forEach((field) => field.addEventListener("change", update));
    update();
  }

  function setupStandardCheckboxes() {
    document.querySelectorAll('form input[type="checkbox"]').forEach((checkbox) => {
      checkbox.closest("label")?.classList.add("provider-checkbox");
    });
  }

  function setupFormSectionAccordion() {
    document.querySelectorAll(".provider-form, .patient-form, .user-form, .role-form").forEach((form) => {
      form.querySelectorAll(":scope > details.form-section").forEach((section) => {
        section.addEventListener("toggle", () => {
          if (!section.open) return;
          form.querySelectorAll(":scope > details.form-section[open]").forEach((otherSection) => {
            if (otherSection !== section) otherSection.open = false;
          });
        });
      });
    });
  }

  function setupSortableTables() {
    const currentOrdering = new URLSearchParams(window.location.search).get("ordem") || "";
    const renderIndicator = (element, fieldName) => {
      element.querySelector(".sort-indicator")?.remove();
      if (currentOrdering !== fieldName && currentOrdering !== `-${fieldName}`) return;
      const indicator = document.createElement("span");
      indicator.className = "sort-indicator";
      indicator.textContent = currentOrdering.startsWith("-") ? "▼" : "▲";
      element.appendChild(indicator);
    };

    document.querySelectorAll("table th a").forEach((link) => {
      const ordering = new URL(link.href, window.location.origin).searchParams.get("ordem") || "";
      const fieldName = ordering.replace(/^-/, "");
      if (fieldName) renderIndicator(link, fieldName);
      link.addEventListener("click", () => storeCurrentListPosition());
    });
    document.querySelectorAll("table th[data-sort-field]").forEach((header) => {
      const fieldName = header.dataset.sortField;
      header.classList.add("sortable-column");
      header.tabIndex = 0;
      renderIndicator(header, fieldName);
      const applyOrdering = () => {
        const url = new URL(window.location.href);
        url.searchParams.set("ordem", currentOrdering === fieldName ? `-${fieldName}` : fieldName);
        storeCurrentListPosition();
        window.location.href = url.toString();
      };
      header.addEventListener("click", applyOrdering);
      header.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        applyOrdering();
      });
    });
  }

  function setupResizableTables() {
    document.querySelectorAll("table").forEach((table) => {
      const headers = Array.from(table.querySelectorAll("thead th"));
      let colgroup = table.querySelector("colgroup[data-resizable-columns]");
      if (!colgroup) {
        colgroup = document.createElement("colgroup");
        colgroup.dataset.resizableColumns = "true";
        headers.forEach(() => colgroup.appendChild(document.createElement("col")));
        table.prepend(colgroup);
      }
      headers.forEach((header, index) => {
        if (index >= headers.length - 1) return;
        if (header.querySelector(".column-resize-handle")) return;
        header.style.position = "sticky";
        const handle = document.createElement("span");
        handle.className = "column-resize-handle";
        handle.dataset.columnResize = String(index);
        handle.addEventListener("click", (event) => event.preventDefault());
        handle.addEventListener("mousedown", (event) => {
          event.preventDefault();
          event.stopPropagation();
          const startX = event.clientX;
          const startWidth = header.getBoundingClientRect().width;
          const col = colgroup.children[index];
          document.body.classList.add("column-resizing");
          const resize = (moveEvent) => {
            const nextWidth = Math.max(64, startWidth + moveEvent.clientX - startX);
            if (col) {
              col.style.width = `${nextWidth}px`;
              col.style.minWidth = `${nextWidth}px`;
            }
          };
          const stop = () => {
            document.body.classList.remove("column-resizing");
            document.removeEventListener("mousemove", resize);
            document.removeEventListener("mouseup", stop);
          };
          document.addEventListener("mousemove", resize);
          document.addEventListener("mouseup", stop);
        });
        header.appendChild(handle);
      });
    });
  }

  function syncLinkedOptionLabel(field) {
    const targetName = field.dataset.optionLabelTarget;
    if (!targetName) return;
    const form = field.closest("form");
    const target = form?.querySelector(`[name="${CSS.escape(targetName)}"]`);
    if (target) target.value = field.selectedOptions?.[0]?.textContent?.trim() || "";
  }

  function filterCepCitiesForState(stateField) {
    const targetName = stateField.dataset.cityTarget;
    if (!targetName) return;
    const form = stateField.closest("form") || document;
    const citySelect = form.querySelector(`[name="${CSS.escape(targetName)}"]`);
    if (!citySelect) return;
    const state = stateField.value;
    Array.from(citySelect.options).forEach((option) => {
      const visible = !option.value || (state && option.dataset.state === state);
      option.hidden = !visible;
      option.disabled = !visible;
    });
    const selectedOption = citySelect.selectedOptions[0];
    if (selectedOption?.disabled) {
      citySelect.value = "";
      syncLinkedOptionLabel(citySelect);
    }
  }

  function setupCepCityDependencies() {
    document.querySelectorAll("[data-cep-state-select]").forEach(filterCepCitiesForState);
  }

  function copyResidentialAddressToCommercial(lockFields) {
    const fieldMap = {
      cd_cep: "cd_cep_comercial",
      sg_estado: "sg_estado_comercial",
      ds_cidade: "ds_cidade_comercial",
      tp_logradouro: "tp_logradouro_comercial",
      ds_endereco: "ds_endereco_comercial",
      nr_endereco: "nr_endereco_comercial",
      ds_complemento: "ds_complemento_comercial",
      ds_bairro: "ds_bairro_comercial",
    };
    Object.entries(fieldMap).forEach(([sourceName, targetName]) => {
      const source = document.querySelector(`[name="${sourceName}"]`);
      const target = document.querySelector(`[name="${targetName}"]`);
      if (!target) return;
      if (lockFields && source) {
        if (target.tagName === "SELECT" && !Array.from(target.options).some((option) => option.value === source.value)) {
          target.add(new Option(source.selectedOptions?.[0]?.textContent || source.value, source.value));
        }
        target.value = source.value;
      }
      target.disabled = Boolean(lockFields);
    });
  }

  function applyProviderPermissionSuggestions(providerType) {
    const suggestions = {
      MEDICO: ["sn_permite_agenda", "sn_permite_atendimento", "sn_permite_prescricao"],
      ENFERMEIRO: ["sn_permite_agenda", "sn_permite_atendimento", "sn_permite_classificacao"],
      TECNICO_ENFERMAGEM: ["sn_permite_classificacao"],
    };
    const permissionFields = [
      "sn_permite_agenda",
      "sn_permite_atendimento",
      "sn_permite_prescricao",
      "sn_permite_classificacao",
    ];
    if (!providerType || !suggestions[providerType]) return;
    permissionFields.forEach((fieldName) => {
      const field = document.querySelector(`[name="${fieldName}"]`);
      if (field) field.checked = suggestions[providerType].includes(fieldName);
    });
  }

  function setupActionButtons() {
    const queryButton = document.querySelector("[data-query-toggle]");
    const newButton = document.querySelector('[data-action="new"]');
    const continueButton = document.querySelector('[data-action="continue"]');
    const clearButton = document.querySelector('[data-action="clear"]');
    const removeButton = document.querySelector('[data-action="remove"]');
    const previousButton = document.querySelector('[data-action="previous"]');
    const nextButton = document.querySelector('[data-action="next"]');
    const firstButton = document.querySelector('[data-action="first"]');
    const lastButton = document.querySelector('[data-action="last"]');
    const closeButton = document.querySelector('[data-action="close"]');
    const saveButton = document.querySelector('[data-action="save"]');
    const cancelQueryIcon = document.querySelector('[data-query-cancel] [data-nav-icon]');
    const tableForm = getEditableTableForm();
    const isHome = document.body.dataset.tabUrl === "/";

    if (document.querySelector("[data-disable-toolbar-actions='true']")) {
      document.querySelectorAll(".toolbar-actions .toolbar-button").forEach((button) => {
        button.disabled = true;
      });
      return;
    }

    if (isHome) {
      [queryButton, clearButton, newButton, continueButton, removeButton, firstButton, previousButton, nextButton, lastButton, closeButton].forEach((button) => {
        if (button) button.disabled = true;
      });
      return;
    }

    if (queryButton) {
      queryButton.hidden = document.body.dataset.canQuery !== "true";
      queryButton.disabled = document.body.dataset.canQuery !== "true";
    }
    if (saveButton && document.querySelector(".content form[data-has-errors='true']")) saveButton.disabled = false;
    if (newButton) {
      newButton.hidden = !(document.body.dataset.newUrl || tableForm);
      newButton.disabled = !(document.body.dataset.newUrl || tableForm);
    }
    if (continueButton) {
      continueButton.hidden = !document.body.dataset.continueUrl;
      continueButton.disabled = !document.body.dataset.continueUrl;
    }
    if (removeButton) removeButton.disabled = tableForm
      ? !hasSelectedEditableRow(tableForm)
      : !(document.body.dataset.canRemove === "true" && hasLoadedRecord());
    if (removeButton) removeButton.hidden = !(document.body.dataset.canRemove === "true" || tableForm);
    const toggleActiveButton = document.querySelector('[data-action="toggle-active"]');
    if (toggleActiveButton) {
      const rowActiveField = getSelectedRowActiveField(tableForm);
      toggleActiveButton.hidden = !(rowActiveField || document.body.dataset.toggleActiveUrl);
      toggleActiveButton.disabled = !(rowActiveField || (document.body.dataset.toggleActiveUrl && hasLoadedRecord()));
      if (rowActiveField) {
        toggleActiveButton.title = rowActiveField.value === "true" ? "Desativar" : "Ativar";
      }
      toggleActiveButton.querySelector("[data-nav-icon]")?.setAttribute(
        "data-nav-icon",
        toggleActiveButton.title === "Ativar" ? "check" : "ban"
      );
    }
    const changePasswordButton = document.querySelector('[data-action="change-password"]');
    if (changePasswordButton) {
      changePasswordButton.hidden = !document.body.dataset.passwordUrl;
      changePasswordButton.disabled = !document.body.dataset.passwordUrl || !hasLoadedRecord();
    }
    if (previousButton) {
      previousButton.disabled = !document.body.dataset.previousUrl;
    }
    if (nextButton) {
      nextButton.disabled = !document.body.dataset.nextUrl;
    }
    if (firstButton) {
      firstButton.disabled = !document.body.dataset.firstUrl;
    }
    if (lastButton) {
      lastButton.disabled = !document.body.dataset.lastUrl;
    }
    if (closeButton && isHome) closeButton.disabled = true;
    if (cancelQueryIcon) cancelQueryIcon.setAttribute("data-nav-icon", "ban");
    const closeButtonIcon = document.querySelector('[data-action="close"] [data-nav-icon]');
    if (closeButtonIcon && document.body.dataset.closeMode === "back") {
      closeButtonIcon.setAttribute("data-nav-icon", "corner-up-left");
      document.querySelector('[data-action="close"]')?.setAttribute("title", "Voltar");
    }
  }

  function setupNotifications() {
    const now = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    document.querySelectorAll("[data-notification-time]").forEach((element) => {
      element.textContent = now;
    });
    const firstMessage = document.querySelector("[data-server-notification]");
    if (firstMessage) {
      const message = firstMessage.querySelector(".notification-text")?.textContent?.trim();
      const isError = firstMessage.classList.contains("error");
      if (message) {
        persistNotification(message, isError ? "error" : "info");
        showBlockingNotification({
          title: isError ? "Erro" : "Notificação",
          message,
          confirmText: "OK",
          type: isError ? "error" : "info",
          focusTarget: isError ? document.querySelector('[aria-invalid="true"]') : null,
        });
      }
    }
    renderPersistedNotifications();
  }

  function setupSessionMonitor() {
    if (!document.body.dataset.username) return;
    const checkSession = async () => {
      try {
        const response = await fetch("/accounts/sessao/status/", {
          headers: { "Accept": "application/json" },
          credentials: "same-origin",
        });
        if (response.status === 401) {
          let payload = {};
          try {
            payload = await response.json();
          } catch (error) {
            payload = {};
          }
          window.location.replace(payload.login_url || "/accounts/login/");
        }
      } catch (error) {
        // Falha transitória de rede não encerra a sessão local imediatamente.
      }
    };
    window.setInterval(checkSession, 60000);
  }

  function disableBrowserAutocomplete() {
    document.querySelectorAll("form").forEach((form, formIndex) => {
      form.setAttribute("autocomplete", "off");
      form.setAttribute("data-form-type", "other");
      form.dataset.autocompleteSection = form.dataset.autocompleteSection || `celeris-${formIndex}-${Date.now()}`;
    });
    document.querySelectorAll("input, textarea, select").forEach((field, fieldIndex) => {
      const form = field.closest("form");
      const type = (field.getAttribute("type") || "").toLowerCase();
      const shouldPreserveNativeAutocomplete = Boolean(
        field.matches("[data-company-user]")
        || type === "password"
        || field.name === "username"
      );
      if (!shouldPreserveNativeAutocomplete) {
        const section = form?.dataset.autocompleteSection || "celeris";
        field.setAttribute("autocomplete", `section-${section}-${fieldIndex} new-password`);
      }
      field.setAttribute("autocapitalize", "off");
      field.setAttribute("spellcheck", "false");
      field.setAttribute("aria-autocomplete", "none");
      field.setAttribute("data-lpignore", "true");
      field.setAttribute("data-1p-ignore", "true");
    });
  }

  function setupUserLoginSuggestion() {
    const fullNameField = document.querySelector("[data-user-full-name]");
    const loginField = document.querySelector("[data-user-login]");
    const userForm = fullNameField?.closest(".user-form");
    if (!fullNameField || !loginField || !userForm || userForm.dataset.userId) return;
    let timer;
    fullNameField.addEventListener("input", () => {
      if (document.body.classList.contains("screen-query-mode") || loginField.value) return;
      window.clearTimeout(timer);
      timer = window.setTimeout(async () => {
        const params = new URLSearchParams({ nome: fullNameField.value });
        const response = await fetch(`/accounts/usuarios/login-sugerido/?${params.toString()}`);
        const payload = await response.json();
        loginField.value = payload.login || "";
      }, 250);
    });
  }

  function focusFirstEditableField() {
    if (document.body.dataset.startQuery === "true") return;
    const field = document.querySelector('[name="nm_paciente"]:not([disabled]):not([readonly])')
      || document.querySelector(".content form input:not([type='hidden']):not([disabled]):not([readonly]), .content form select:not([disabled]), .content form textarea:not([disabled]):not([readonly])");
    field?.focus();
    field?.select?.();
  }

  function renderTabs() {
    const tabsBar = document.querySelector(".tabs-bar");
    const title = document.body.dataset.tabRootTitle || document.body.dataset.tabTitle || "Início";
    const url = `${window.location.pathname}${window.location.search}`;
    const key = document.body.dataset.tabKey || url;
    if (!tabsBar) return;

    const homeTab = { title: "Início", url: "/" };
    let savedTabs = [];
    try {
      savedTabs = JSON.parse(localStorage.getItem("celeris-tabs") || "[]");
    } catch (error) {
      savedTabs = [];
    }
    const tabs = [
      homeTab,
      ...savedTabs.filter((tab) => (
        tab.key !== homeTab.url
        && tab.url !== homeTab.url
        && (tab.key === key || tab.title !== title)
      )),
    ];
    const currentIndex = tabs.findIndex((tab) => (tab.key || tab.url) === key);

    if (currentIndex >= 0) {
      tabs[currentIndex] = { title, url, key };
    } else {
      if (tabs.length >= 10) {
        const fallbackTab = tabs[tabs.length - 1] || homeTab;
        showBlockingNotification({
          title: "Limite de guias abertas",
          message: "Você atingiu o limite de 10 guias abertas. Feche alguma guia para abrir novas telas.",
          confirmText: "OK",
          type: "info",
        }).then(() => {
          if (key !== (fallbackTab.key || fallbackTab.url)) window.location.href = fallbackTab.url;
        });
        return;
      }
      tabs.push({ title, url, key });
    }

    const limitedTabs = [homeTab, ...tabs.filter((tab) => (tab.key || tab.url) !== homeTab.url)].slice(0, 10);
    localStorage.setItem("celeris-tabs", JSON.stringify(limitedTabs.filter((tab) => (tab.key || tab.url) !== homeTab.url)));

    tabsBar.innerHTML = limitedTabs.map((tab) => {
      const tabKey = tab.key || tab.url;
      const active = tabKey === key || (tab.url === "/" && title === "Início");
      const closeButton = tab.url === homeTab.url ? "" : `<button class="tab-close" data-tab-close data-tab-url="${escapeHTML(tab.url)}" data-tab-key="${escapeHTML(tabKey)}" type="button" title="Fechar guia">&times;</button>`;
      return `<a class="tab${active ? " active" : ""}" href="${escapeHTML(tab.url)}"><span>${escapeHTML(tab.title)}</span>${closeButton}</a>`;
    }).join("");
  }

  function getStoredTabs() {
    try {
      return JSON.parse(localStorage.getItem("celeris-tabs") || "[]");
    } catch (error) {
      return [];
    }
  }

  function setStoredTabs(tabs) {
    localStorage.setItem("celeris-tabs", JSON.stringify(tabs.filter((tab) => (tab.key || tab.url) !== "/")));
  }

  function getCurrentFormStateKey(form = getPrimaryForm()) {
    if (!form || !form.matches(".content form")) return "";
    const key = document.body.dataset.tabKey || window.location.pathname;
    return `celeris-form-state:${key}`;
  }

  function getFormStateFields(form) {
    return Array.from(form.elements).filter((field) => (
      field.name
      && field.type !== "hidden"
      && field.name !== "csrfmiddlewaretoken"
      && field.type !== "password"
      && !field.disabled
    ));
  }

  function persistCurrentFormState(form = getPrimaryForm()) {
    const storageKey = getCurrentFormStateKey(form);
    if (!storageKey) return;
    const fields = getFormStateFields(form).map((field) => ({
      name: field.name,
      type: field.type || field.tagName.toLowerCase(),
      checked: Boolean(field.checked),
      value: field instanceof HTMLSelectElement && field.multiple
        ? Array.from(field.selectedOptions).map((option) => option.value)
        : field.value,
    }));
    localStorage.setItem(storageKey, JSON.stringify({ fields }));
  }

  function clearCurrentFormState(form = getPrimaryForm()) {
    const storageKey = getCurrentFormStateKey(form);
    if (storageKey) localStorage.removeItem(storageKey);
  }

  function restoreCurrentFormState(form = getPrimaryForm()) {
    const storageKey = getCurrentFormStateKey(form);
    if (!storageKey || document.body.dataset.formErrors !== "{}") return;
    let payload = null;
    try {
      payload = JSON.parse(localStorage.getItem(storageKey) || "null");
    } catch (error) {
      payload = null;
    }
    if (!payload?.fields?.length) return;
    if (form.matches("[data-editable-table]")) {
      const requiredCounts = payload.fields.reduce((counts, field) => {
        counts[field.name] = Math.max(
          counts[field.name] || 0,
          payload.fields.filter((item) => item.name === field.name).length
        );
        return counts;
      }, {});
      let safety = 20;
      while (
        safety > 0
        && Object.entries(requiredCounts).some(([name, count]) => (
          form.querySelectorAll(`[name="${CSS.escape(name)}"]`).length < count
        ))
      ) {
        addEditableTableRow(form, false);
        safety -= 1;
      }
    }
    const fieldsByName = payload.fields.reduce((groups, field) => {
      groups[field.name] = groups[field.name] || [];
      groups[field.name].push(field);
      return groups;
    }, {});
    isRestoringFormState = true;
    try {
      Object.entries(fieldsByName).forEach(([name, savedFields]) => {
        const fields = Array.from(form.querySelectorAll(`[name="${CSS.escape(name)}"]`));
        fields.forEach((field, index) => {
          const saved = savedFields[index];
          if (!saved) return;
          if (field instanceof HTMLSelectElement && field.multiple && Array.isArray(saved.value)) {
            Array.from(field.options).forEach((option) => {
              option.selected = saved.value.includes(option.value);
            });
          } else if (field.matches('input[type="checkbox"], input[type="radio"]')) {
            field.checked = saved.checked;
          } else {
            field.value = saved.value ?? "";
          }
          field.dispatchEvent(new Event("change", { bubbles: true }));
        });
      });
    } finally {
      isRestoringFormState = false;
    }
    if (form.method?.toLowerCase() !== "get") {
      form.dataset.dirty = "true";
      const saveButton = document.querySelector('[data-action="save"]');
      if (saveButton) saveButton.disabled = false;
    }
  }

  function storeCurrentListPosition() {
    const storageKey = `celeris-list-scroll:${window.location.pathname}${window.location.search}`;
    const tableCard = document.querySelector("form.table-card[data-editable-table], .table-card");
    sessionStorage.setItem(storageKey, JSON.stringify({
      windowY: window.scrollY,
      tableTop: tableCard?.scrollTop || 0,
      tableLeft: tableCard?.scrollLeft || 0,
    }));
  }

  function setupListContextPreservation() {
    const storageKey = `celeris-list-scroll:${window.location.pathname}${window.location.search}`;
    document.querySelectorAll("[data-preserve-list-context]").forEach((link) => {
      link.addEventListener("click", storeCurrentListPosition);
    });
    document.querySelectorAll(".table-pager-link[href]").forEach((link) => {
      link.addEventListener("click", storeCurrentListPosition);
    });
    const storedPosition = sessionStorage.getItem(storageKey);
    if (storedPosition !== null) {
      window.requestAnimationFrame(() => {
        let payload = {};
        try {
          payload = JSON.parse(storedPosition);
        } catch (error) {
          payload = { windowY: Number(storedPosition) || 0 };
        }
        window.scrollTo(0, Number(payload.windowY) || 0);
        const tableCard = document.querySelector("form.table-card[data-editable-table], .table-card");
        if (tableCard) {
          tableCard.scrollTop = Number(payload.tableTop) || 0;
          tableCard.scrollLeft = Number(payload.tableLeft) || 0;
        }
      });
      sessionStorage.removeItem(storageKey);
    }
  }

  function closeTab(tabUrl, tabKey = tabUrl) {
    const currentKey = document.body.dataset.tabKey || document.body.dataset.tabUrl || "/";
    localStorage.removeItem(`celeris-form-state:${tabKey}`);
    const tabs = getStoredTabs().filter((tab) => (tab.key || tab.url) !== tabKey);
    setStoredTabs(tabs);
    if (tabKey === currentKey) {
      const nextTab = tabs[tabs.length - 1];
      window.location.href = nextTab?.url || "/";
    } else {
      renderTabs();
    }
  }

  function closeCurrentTab() {
    const currentUrl = document.body.dataset.tabUrl || "/";
    const currentKey = document.body.dataset.tabKey || currentUrl;
    if (currentUrl === "/") {
      window.location.href = "/";
      return;
    }
    closeTab(currentUrl, currentKey);
  }

  renderTabs();
  setupListContextPreservation();
  setupSpecialtyManager();
  setupAssignmentManagers();
  setupRoleModuleVisibility();
  setupStandardCheckboxes();
  setupFormSectionAccordion();
  setupSortableTables();
  setupResizableTables();
  setupCepCityDependencies();
  setupInitialEditableRows();
  updateTablePagerVisibility();
  restoreCurrentFormState();
  const warNameField = document.querySelector("[data-war-name]");
  if (warNameField?.value.trim()) {
    warNameField.dataset.manuallyEdited = "true";
  }
  const sameAddressField = document.querySelector("[data-same-address]");
  if (sameAddressField) {
    copyResidentialAddressToCommercial(sameAddressField.checked);
    [
      "cd_cep",
      "sg_estado",
      "ds_cidade",
      "tp_logradouro",
      "ds_endereco",
      "nr_endereco",
      "ds_complemento",
      "ds_bairro",
    ].forEach((fieldName) => {
      const field = document.querySelector(`[name="${fieldName}"]`);
      field?.addEventListener("input", () => {
        if (sameAddressField.checked) copyResidentialAddressToCommercial(true);
      });
      field?.addEventListener("change", () => {
        if (sameAddressField.checked) copyResidentialAddressToCommercial(true);
      });
    });
  }
  const currentDateTime = document.querySelector("[data-current-datetime]");
  if (currentDateTime) {
    const renderDateTime = () => {
      currentDateTime.textContent = new Date().toLocaleString("pt-BR");
    };
    renderDateTime();
    window.setInterval(renderDateTime, 1000);
  }
  setupActionButtons();
  scheduleSidebarAutoCollapse();
  if (document.body.dataset.startQuery === "true" || sessionStorage.getItem("celeris-open-query-after-save") === "true") {
    sessionStorage.removeItem("celeris-open-query-after-save");
    clearFormFields(getPrimaryForm());
    setQueryMode(true);
    const firstField = document.querySelector(".content input:not([type='hidden']), .content select, .content textarea");
    firstField?.focus();
  }
  renderIcons();
  disableBrowserAutocomplete();
  setupUserLoginSuggestion();
  setupServerValidationErrors();
  setupNotifications();
  setupSessionMonitor();
  updateFieldStatus(null);
  focusFirstEditableField();
})();
