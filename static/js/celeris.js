(function () {
  const root = document.documentElement;
  const shell = document.querySelector(".app-shell");

  const icons = {
    activity: '<path d="M22 12h-4l-3 8-6-16-3 8H2"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    coins: '<circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h1.5a1.5 1.5 0 0 1 0 3H7V6Z"/><path d="M7 9h2a1.5 1.5 0 0 1 0 3H7V9Z"/>',
    monitor: '<rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 22h8"/><path d="M12 18v4"/>',
    table: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>',
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
    play: '<path d="m6 3 14 9-14 9V3Z"/>',
    save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/>',
    trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>',
    "arrow-left": '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    "corner-up-left": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 6 6v5"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
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
    setActionStatus(enabled ? "CONSULTAR" : "EDITAR");
    const queryButton = document.querySelector("[data-query-toggle]");
    const cancelButton = document.querySelector("[data-query-cancel]");
    if (queryButton) {
      queryButton.dataset.queryMode = enabled ? "execute" : "open";
      queryButton.title = enabled ? "Executar consulta" : "Abrir consulta";
      queryButton.querySelector("[data-nav-icon]")?.setAttribute("data-nav-icon", enabled ? "play" : "search");
    }
    if (cancelButton) cancelButton.hidden = !enabled;
    document.querySelectorAll("[data-consultable], [data-primary-key]").forEach((field) => {
      if (field.closest("[data-editable-table]") && field.dataset.primaryKey === "true") {
        field.setAttribute("readonly", "readonly");
        return;
      }
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
      if (field.type === "hidden" || field.type === "checkbox") {
        if (field.type === "checkbox") field.checked = false;
        return;
      }
      field.value = "";
    });
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = true;
  }

  const savedTheme = localStorage.getItem("celeris-theme");
  if (savedTheme === "dark") root.classList.add("dark");

  if (localStorage.getItem("celeris-sidebar") === "collapsed") {
    shell?.classList.add("sidebar-collapsed");
  }

  let sidebarFlyout = null;
  let sidebarFlyoutTrigger = null;
  let activeLookupField = null;
  let activeFloatingSelect = null;
  let sidebarAutoCollapseTimer = null;

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
    firstInvalid?.focus();
    return Boolean(firstInvalid);
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
        extra.innerHTML = "";
        resolve(result);
      };
      const confirmHandler = () => {
        if (onConfirm && onConfirm() === false) return;
        finish(true);
      };
      const cancelHandler = () => finish(false);
      confirmButton.addEventListener("click", confirmHandler);
      cancelButton.addEventListener("click", cancelHandler);
      window.requestAnimationFrame(() => {
        const firstField = extra.querySelector("select, input, textarea");
        (firstField || confirmButton).focus();
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
    setActionStatus("EDITAR");
  }

  function addEditableTableRow(form) {
    const template = form.querySelector("template[data-table-new-row]");
    const tbody = form.querySelector("tbody");
    if (!template || !tbody) return false;
    const fragment = template.content.cloneNode(true);
    const row = fragment.querySelector("tr");
    tbody.querySelector(".empty-cell")?.closest("tr")?.remove();
    tbody.appendChild(fragment);
    markFormDirty(form);
    row?.querySelector("input:not([readonly]):not([disabled]), select:not([disabled]), textarea:not([readonly]):not([disabled])")?.focus();
    return true;
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
    const nextCell = nextRow?.children[cellIndex];
    const nextField = nextCell?.querySelector("input, select, textarea");
    if (!nextField) return false;
    nextField.focus();
    nextField.select?.();
    return true;
  }

  async function handleCloseAction() {
    const form = getPrimaryForm();
    if (form?.dataset.dirty === "true") {
      const shouldSave = await showBlockingNotification({
        title: "Dados alterados",
        message: "Existem dados digitados. Deseja salvar antes de sair?",
        confirmText: "Confirmar",
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
      window.location.href = document.body.dataset.tabKey || "/";
      return;
    }
    closeCurrentTab();
  }

  document.addEventListener("click", async function (event) {
    const themeButton = event.target.closest("[data-theme-toggle]");
    if (themeButton) {
      root.classList.toggle("dark");
      localStorage.setItem("celeris-theme", root.classList.contains("dark") ? "dark" : "light");
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
            confirmText: "Confirmar",
            cancelText: "Cancelar",
          });
          if (shouldSave) {
            sessionStorage.setItem("celeris-open-query-after-save", "true");
            await submitPrimaryForm(form);
            return;
          }
          return;
        }
        clearFormFields(form);
        if (form?.matches("[data-editable-table]") && !form.querySelector("tbody tr[data-editable-row]:not([hidden])")) {
          addEditableTableRow(form);
          form.dataset.dirty = "false";
        }
        setQueryMode(true);
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
        if (form?.matches("[data-editable-table]")) {
          const queryValue = Array.from(form.querySelectorAll("input:not([type='hidden']), select, textarea"))
            .filter((field) => !field.readOnly && !field.disabled && field.value.trim())
            .map((field) => field.value.trim())[0] || "";
          const params = queryValue ? `?q=${encodeURIComponent(queryValue)}` : "";
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
      setQueryMode(false);
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
        await submitPrimaryForm(form);
      }
      return;
    }

    const newAction = event.target.closest('[data-action="new"]');
    if (newAction && !newAction.disabled) {
      const tableForm = getEditableTableForm();
      if (tableForm && addEditableTableRow(tableForm)) return;
      const targetUrl = document.body.dataset.newUrl;
      if (targetUrl) window.location.href = targetUrl;
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
    if (activeFloatingSelect && !event.target.closest("[data-floating-select]")) {
      closeFloatingSelect();
    }

    const editableCell = event.target.closest("form[data-editable-table] td");
    if (editableCell) {
      editableCell.closest("tbody")?.querySelectorAll("tr.selected").forEach((row) => row.classList.remove("selected"));
      editableCell.closest("tr[data-editable-row]")?.classList.add("selected");
    }

    const notificationsPanel = document.querySelector("[data-notifications-panel]");
    if (notificationsPanel && !notificationsPanel.hidden && !event.target.closest("[data-notifications-panel]")) {
      notificationsPanel.hidden = true;
    }
  });

  document.addEventListener("submit", function (event) {
    if (event.target.matches("[data-clear-tabs]")) {
      localStorage.removeItem("celeris-tabs");
    }
    if (event.target.matches(".content form")) markInvalidFields(event.target);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeLookup();
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
    if (event.key === "Enter" && event.target.matches(".content input, .content select, .content textarea")) {
      const field = event.target;
      event.preventDefault();
      focusNextField(field);
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
      if (currentSection) currentSection.open = false;
      nextSection.open = true;
    }
    nextField = nextField || fields[0];
    if (!nextField) return;
    window.requestAnimationFrame(() => focusField(nextField));
  }

  function closeFloatingSelect() {
    activeFloatingSelect?.remove();
    activeFloatingSelect = null;
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
    panel.innerHTML = options.map((option, index) => `
      <button type="button" data-select-index="${index}" class="${option.value === field.value ? "active" : ""}">
        ${escapeHTML(option.text || option.value || "—")}
      </button>
    `).join("");
    document.body.appendChild(panel);
    activeFloatingSelect = panel;
    positionFloatingSelect(panel, field);
    const selectOption = (button) => {
      const option = options[Number(button.dataset.selectIndex)];
      if (!option) return;
      field.value = option.value;
      field.dispatchEvent(new Event("change", { bubbles: true }));
      closeFloatingSelect();
      focusNextField(field);
    };
    panel.addEventListener("mousedown", (event) => event.preventDefault());
    panel.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (button) selectOption(button);
    });
    panel.addEventListener("keydown", (event) => {
      const buttons = Array.from(panel.querySelectorAll("button"));
      const current = document.activeElement.closest?.("button");
      const currentIndex = Math.max(buttons.indexOf(current), 0);
      if (event.key === "ArrowDown") {
        event.preventDefault();
        buttons[Math.min(currentIndex + 1, buttons.length - 1)]?.focus();
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        buttons[Math.max(currentIndex - 1, 0)]?.focus();
      } else if (event.key === "Enter") {
        event.preventDefault();
        if (current) selectOption(current);
      } else if (event.key === "Escape") {
        closeFloatingSelect();
        field.focus();
      }
    });
    window.requestAnimationFrame(() => {
      const activeButton = panel.querySelector("button.active") || panel.querySelector("button");
      activeButton?.focus();
    });
  }

  function focusField(field) {
    field.focus();
    if (field instanceof HTMLInputElement) field.select?.();
    if (field instanceof HTMLSelectElement) {
      openFloatingSelect(field);
    }
  }

  window.addEventListener("resize", () => {
    closeSidebarFlyout();
    closeFloatingSelect();
  });
  window.addEventListener("scroll", () => {
    closeSidebarFlyout();
    closeFloatingSelect();
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

    const table = field.dataset.fieldTable || field.closest("[data-table]")?.dataset.table || "";
    const labelText = field.closest("label")?.childNodes?.[0]?.textContent?.trim() || "";
    const fieldName = field.dataset.fieldName || field.name || field.id || labelText || "campo";
    const normalizedField = normalizeFieldName(fieldName);
    const normalizedTable = table ? normalizeFieldName(table) : "";
    status.textContent = normalizedTable ? `${normalizedTable}.${normalizedField}` : normalizedField;
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
    const field = event.target.closest("input, select, textarea");
    if (field && !document.activeElement.matches?.("input, select, textarea")) {
      updateFieldStatus(null);
    }
  });

  document.addEventListener("input", function (event) {
    const field = event.target.closest("input, textarea");
    if (!field) return;
    if (field.dataset.mask === "cpf") {
      field.value = formatCPF(field.value);
    } else if (field.dataset.mask === "celular") {
      field.value = formatCellphone(field.value);
    }
    if (!field.closest("[data-preserve-input]")) {
      normalizeInputValue(field);
    }
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = false;
    setActionStatus("EDITAR");
    field.closest("form")?.setAttribute("data-dirty", "true");
  });

  document.addEventListener("change", function (event) {
    if (!event.target.closest("input, select, textarea")) return;
    if (event.target.matches("[data-state-select]")) {
      loadCitiesForState(event.target.value);
    }
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = false;
    setActionStatus("EDITAR");
    event.target.closest("form")?.setAttribute("data-dirty", "true");
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

  document.addEventListener("blur", async function (event) {
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
    });
  }, true);

  document.addEventListener("input", function (event) {
    const field = event.target.closest("[data-unique-patient]");
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

  function setupActionButtons() {
    const queryButton = document.querySelector("[data-query-toggle]");
    const newButton = document.querySelector('[data-action="new"]');
    const continueButton = document.querySelector('[data-action="continue"]');
    const removeButton = document.querySelector('[data-action="remove"]');
    const previousButton = document.querySelector('[data-action="previous"]');
    const nextButton = document.querySelector('[data-action="next"]');
    const closeButton = document.querySelector('[data-action="close"]');
    const cancelQueryIcon = document.querySelector('[data-query-cancel] [data-nav-icon]');
    const tableForm = getEditableTableForm();
    const isHome = document.body.dataset.tabUrl === "/";

    if (isHome) {
      [queryButton, newButton, continueButton, removeButton, previousButton, nextButton, closeButton].forEach((button) => {
        if (button) button.disabled = true;
      });
      return;
    }

    if (queryButton) queryButton.disabled = document.body.dataset.canQuery !== "true";
    if (newButton) newButton.disabled = !(document.body.dataset.newUrl || tableForm);
    if (continueButton) continueButton.disabled = !document.body.dataset.continueUrl;
    if (removeButton) removeButton.disabled = !(document.body.dataset.canRemove === "true" || tableForm);
    if (previousButton) previousButton.disabled = document.body.dataset.hasPrevious !== "true";
    if (nextButton) nextButton.disabled = document.body.dataset.hasNext !== "true";
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
        });
      }
    }
    renderPersistedNotifications();
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
    const url = document.body.dataset.tabUrl || "/";
    const key = document.body.dataset.tabKey || url;
    if (!tabsBar) return;

    const homeTab = { title: "Início", url: "/" };
    let savedTabs = [];
    try {
      savedTabs = JSON.parse(localStorage.getItem("celeris-tabs") || "[]");
    } catch (error) {
      savedTabs = [];
    }
    const tabs = [homeTab, ...savedTabs.filter((tab) => tab.key !== homeTab.url && tab.url !== homeTab.url)];
    const currentIndex = tabs.findIndex((tab) => (tab.key || tab.url) === key);

    if (currentIndex >= 0) {
      tabs[currentIndex] = { title, url, key };
    } else {
      tabs.push({ title, url, key });
    }

    const limitedTabs = [homeTab, ...tabs.filter((tab) => (tab.key || tab.url) !== homeTab.url).slice(-7)];
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

  function closeTab(tabUrl, tabKey = tabUrl) {
    const currentKey = document.body.dataset.tabKey || document.body.dataset.tabUrl || "/";
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
  setupActionButtons();
  scheduleSidebarAutoCollapse();
  if (document.body.dataset.startQuery === "true" || sessionStorage.getItem("celeris-open-query-after-save") === "true") {
    sessionStorage.removeItem("celeris-open-query-after-save");
    setQueryMode(true);
    const firstField = document.querySelector(".content input:not([type='hidden']), .content select, .content textarea");
    firstField?.focus();
  }
  renderIcons();
  setupNotifications();
  updateFieldStatus(null);
  focusFirstEditableField();
})();
