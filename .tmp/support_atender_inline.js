
  (() => {
    const usersByOffice = JSON.parse(document.getElementById("support-users-by-office")?.textContent || "{}");
    const completeModal = document.querySelector("[data-complete-modal]");
    const transferModal = document.querySelector("[data-transfer-modal]");
    const performersList = document.querySelector("[data-performers-list]");
    const detailsPanel = document.querySelector("[data-complete-details]");
    let currentOffice = "";

    const closeDialogs = () => document.querySelectorAll("dialog[open]").forEach((dialog) => dialog.close());
    const escapeHtml = (value) => String(value || "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[char]);

    const selectedPerformerIds = (exceptSelect = null) => new Set(
      [...performersList.querySelectorAll('select[name="performers"]')]
        .filter((select) => select !== exceptSelect)
        .map((select) => select.value)
        .filter(Boolean)
    );

    const refreshPerformerOptions = () => {
      const selects = [...performersList.querySelectorAll('select[name="performers"]')];
      selects.forEach((select) => {
        const currentValue = select.value;
        const selectedIds = selectedPerformerIds(select);
        select.innerHTML = '<option value="">Selecione o usuário</option>';
        (usersByOffice[currentOffice] || []).forEach((user) => {
          if (selectedIds.has(String(user.id)) && String(user.id) !== currentValue) return;
          const option = document.createElement("option");
          option.value = user.id;
          option.textContent = user.label;
          if (String(user.id) === currentValue) option.selected = true;
          select.appendChild(option);
        });
      });
    };

    const buildPerformerSelect = () => {
      const wrapper = document.createElement("div");
      wrapper.className = "support-performer-row";
      const label = document.createElement("label");
      label.className = "field-lg";
      const select = document.createElement("select");
      select.name = "performers";
      select.required = true;
      select.addEventListener("change", refreshPerformerOptions);
      const removeButton = document.createElement("button");
      removeButton.className = "icon-button support-performer-remove support-action-danger";
      removeButton.type = "button";
      removeButton.title = "Remover usuário";
      removeButton.innerHTML = '<span class="svg-icon" data-nav-icon="minus"></span>';
      label.appendChild(select);
      wrapper.append(label, removeButton);
      performersList.appendChild(wrapper);
      refreshPerformerOptions();
      window.CelerisRenderIcons?.();
      updatePerformerRemoveButtons();
    };

    const updatePerformerRemoveButtons = () => {
      const rows = [...performersList.querySelectorAll(".support-performer-row")];
      rows.forEach((row) => {
        const remove = row.querySelector("[data-nav-icon='minus']")?.closest("button");
        if (remove) remove.disabled = rows.length <= 1;
      });
    };

    const setupMultiselect = (root) => {
      const toggle = root.querySelector("[data-support-multiselect-toggle]");
      const menu = root.querySelector("[data-support-multiselect-menu]");
      const search = root.querySelector("[data-support-multiselect-search]");
      const items = [...root.querySelectorAll("[data-support-multiselect-item]")];
      const summary = root.querySelector("[data-support-multiselect-summary]");
      const update = () => {
        const selected = items.filter((item) => item.checked).length;
        summary.textContent = selected ? `${selected} selecionado(s)` : "Todos";
      };
      const reset = () => {
        items.forEach((item) => { item.checked = false; });
        search.value = "";
        menu.querySelectorAll("[data-support-multiselect-option]").forEach((option) => { option.hidden = false; });
        menu.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
        update();
      };
      const position = () => {
        if (menu.hidden) return;
        const rect = toggle.getBoundingClientRect();
        const width = Math.max(rect.width, 300);
        const maxHeight = Math.max(180, window.innerHeight - rect.bottom - 12);
        menu.style.position = "fixed";
        menu.style.left = `${Math.min(rect.left, window.innerWidth - width - 8)}px`;
        menu.style.top = `${rect.bottom + 4}px`;
        menu.style.width = `${width}px`;
        menu.style.maxHeight = `${maxHeight}px`;
      };
      toggle.addEventListener("click", () => {
        if (menu.parentElement !== document.body) document.body.appendChild(menu);
        menu.hidden = !menu.hidden;
        toggle.setAttribute("aria-expanded", String(!menu.hidden));
        position();
        if (!menu.hidden) search.focus();
      });
      items.forEach((item) => item.addEventListener("change", update));
      search.addEventListener("input", () => {
        const term = search.value.trim().toLocaleLowerCase("pt-BR");
        menu.querySelectorAll("[data-support-multiselect-option]").forEach((option) => {
          option.hidden = !option.textContent.toLocaleLowerCase("pt-BR").includes(term);
        });
      });
      document.addEventListener("click", (event) => {
        if (!root.contains(event.target) && !menu.contains(event.target)) {
          menu.hidden = true;
          toggle.setAttribute("aria-expanded", "false");
        }
      });
      root.closest("form")?.addEventListener("celeris:reset-multiselects", reset);
      window.addEventListener("resize", position);
      document.querySelector(".content")?.addEventListener("scroll", position);
      update();
    };

    document.querySelectorAll("[data-support-multiselect]").forEach(setupMultiselect);

    document.addEventListener("click", (event) => {
      const sortHeader = event.target.closest("[data-support-sort]");
      if (sortHeader) {
        const form = document.querySelector("[data-primary-form]");
        const keyInput = form?.querySelector("[data-support-sort-key]");
        const directionInput = form?.querySelector("[data-support-sort-direction]");
        const sort = sortHeader.dataset.supportSort;
        if (keyInput && directionInput) {
          directionInput.value = keyInput.value === sort && directionInput.value !== "desc" ? "desc" : "asc";
          keyInput.value = sort;
          form.requestSubmit();
        }
      }

      const completeButton = event.target.closest("[data-open-complete]");
      const transferButton = event.target.closest("[data-open-transfer]");
      if (event.target.closest("[data-close-modal]")) closeDialogs();
      if (event.target.closest("[data-add-performer]")) buildPerformerSelect();
      if (event.target.closest(".support-performer-remove")) {
        const rows = performersList.querySelectorAll(".support-performer-row");
        if (rows.length > 1) event.target.closest(".support-performer-row")?.remove();
        refreshPerformerOptions();
        updatePerformerRemoveButtons();
      }
      if (completeButton) {
        currentOffice = completeButton.dataset.office || "";
        completeModal.querySelector("[data-complete-ticket]").value = completeButton.dataset.ticket;
        detailsPanel.innerHTML = `
          <div><strong>Código</strong><span>${escapeHtml(completeButton.dataset.ticket)}</span></div>
          <div><strong>Solicitante</strong><span>${escapeHtml(completeButton.dataset.requester)}</span></div>
          <div><strong>Data/hora</strong><span>${escapeHtml(completeButton.dataset.createdLabel)}</span></div>
          <div><strong>Setor</strong><span>${escapeHtml(completeButton.dataset.sector)}</span></div>
          <div><strong>Motivo</strong><span>${escapeHtml(completeButton.dataset.motive)}</span></div>
          <div class="span-2"><strong>Título</strong><span>${escapeHtml(completeButton.dataset.title)}</span></div>
          <div class="span-2"><strong>Descrição</strong><span>${escapeHtml(completeButton.dataset.description)}</span></div>
        `;
        const motiveSelect = completeModal.querySelector('[name="motivo_conclusao"]');
        const observationField = completeModal.querySelector('[name="observacao_conclusao"]');
        if (observationField) observationField.value = "";
        Array.from(motiveSelect.options).forEach((option) => {
          const office = option.dataset.office || "";
          const visible = !option.value || !office || office === currentOffice;
          option.hidden = !visible;
          option.disabled = !visible;
        });
        if (motiveSelect.selectedOptions[0]?.disabled) motiveSelect.value = "";
        const created = completeButton.dataset.created ? new Date(completeButton.dataset.created) : new Date();
        created.setMinutes(created.getMinutes() + 20);
        completeModal.querySelector("[data-complete-performed]").value = created.toISOString().slice(0, 16);
        performersList.innerHTML = "";
        buildPerformerSelect();
        completeModal.showModal();
      }
      if (transferButton) {
        transferModal.querySelector("[data-transfer-ticket]").value = transferButton.dataset.ticket;
        transferModal.showModal();
      }
    });

    [completeModal, transferModal].forEach((modal) => {
      modal?.addEventListener("click", (event) => {
        if (event.target === modal) modal.close();
      });
    });
  })();
