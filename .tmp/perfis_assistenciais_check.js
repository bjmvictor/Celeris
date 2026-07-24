(() => {
      const builder = document.querySelector("[data-profile-item-builder]");
      let openProfileItemModal = () => {};
      if (builder) {
        const modal = document.querySelector("[data-profile-item-modal]");
        const modalTitle = builder.querySelector("[data-profile-item-modal-title]");
        const editItem = builder.querySelector("[data-profile-edit-item]");
        const nodeKind = builder.querySelector("[data-profile-node-kind]");
        const itemType = builder.querySelector("[data-profile-item-type]");
        const screenTypeField = builder.querySelector("[data-profile-screen-type]");
        const screenType = builder.querySelector("[data-profile-screen-type-select]");
        const parentField = builder.querySelector("[data-profile-parent-field]");
        const screenOptions = builder.querySelector("[data-profile-screen-options]");
        const iconSelect = builder.querySelector("[data-profile-icon-select]");
        const iconPreview = builder.querySelector("[data-profile-icon-preview] [data-nav-icon]");
        const iconDropdown = builder.querySelector("[data-profile-icon-dropdown]");
        const iconToggle = builder.querySelector("[data-profile-icon-toggle]");
        const scaleSelect = builder.querySelector('[name="cd_escala_clinica"]');
        const scaleBuilder = builder.querySelector(".profile-scale-builder");
        const questionsList = builder.querySelector("[data-scale-question-list]");
        const rangesList = builder.querySelector("[data-scale-range-list]");
        const expression = builder.querySelector("[data-scale-expression]");
        const tokens = builder.querySelector("[data-scale-expression-tokens]");
        const questionsJson = builder.querySelector("[data-scale-questions-json]");
        const rangesJson = builder.querySelector("[data-scale-ranges-json]");
        const slug = (value) => String(value || "")
          .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
          .replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_+|_+$/g, "").toLowerCase();
        const setSectionVisible = (section, visible) => {
          if (!section) return;
          section.hidden = !visible;
          section.querySelectorAll("input, select, textarea, button").forEach((field) => {
            if (!field.matches("[data-scale-add-question], [data-scale-add-range]")) field.disabled = !visible;
          });
        };
        const updateTokens = () => {
          if (!tokens) return;
          tokens.innerHTML = "";
          questionsList.querySelectorAll("[data-scale-question]").forEach((question, index) => {
            const keyInput = question.querySelector("[data-question-key]");
            const key = slug(keyInput.value) || `pergunta_${index + 1}`;
            keyInput.value = key;
            const token = `{{${key}}}`;
            const button = document.createElement("button");
            button.className = "button button-ghost";
            button.type = "button";
            button.draggable = true;
            button.textContent = token;
            button.addEventListener("click", () => {
              const start = expression.selectionStart ?? expression.value.length;
              expression.setRangeText(token, start, expression.selectionEnd ?? start, "end");
              expression.focus();
            });
            button.addEventListener("dragstart", (event) => {
              event.dataTransfer.setData("text/plain", token);
              event.dataTransfer.effectAllowed = "copy";
            });
            tokens.appendChild(button);
          });
        };
        const addOption = (question, data = {}) => {
          const list = question.querySelector("[data-question-options]");
          const option = document.createElement("div");
          option.className = "scale-option-row";
          option.dataset.scaleOption = "true";
          option.innerHTML = `
            <input data-option-value placeholder="Valor" value="${data.valor || ""}">
            <input data-option-description placeholder="Descrição exibida" value="${data.descricao || ""}">
            <input data-option-points type="number" step="0.01" placeholder="Pontos" value="${data.pontos ?? ""}">
            <button class="icon-button" type="button" data-remove-option title="Remover opção">×</button>`;
          list.appendChild(option);
        };
        const addQuestion = (data = {}) => {
          const index = questionsList.querySelectorAll("[data-scale-question]").length + 1;
          const question = document.createElement("article");
          question.className = "scale-question-card";
          question.dataset.scaleQuestion = "true";
          question.innerHTML = `
            <header>
              <strong>Pergunta ${index}</strong>
              <button class="icon-button" type="button" data-remove-question title="Remover pergunta">×</button>
            </header>
            <div class="form-grid">
              <label class="field-md">Chave <input data-question-key value="${data.chave || `pergunta_${index}`}"></label>
              <label class="field-xl">Pergunta <input data-question-text value="${data.texto || ""}" placeholder="Texto apresentado ao prestador"></label>
            </div>
            <div class="scale-option-list" data-question-options></div>
            <button class="button button-secondary" type="button" data-add-option><span class="svg-icon" data-nav-icon="plus"></span> Opção</button>`;
          questionsList.appendChild(question);
          ((data.opcoes && data.opcoes.length) ? data.opcoes : [{}]).forEach((option) => addOption(question, option));
          updateTokens();
        };
        const addRange = (data = {}) => {
          const range = document.createElement("div");
          range.className = "scale-range-row";
          range.dataset.scaleRange = "true";
          range.innerHTML = `
            <select data-range-operator>
              <option value="INTERVALO">Intervalo</option><option value=">=">Maior ou igual</option>
              <option value=">">Maior</option><option value="<=">Menor ou igual</option>
              <option value="<">Menor</option><option value="=">Igual</option>
            </select>
            <input data-range-value type="number" step="0.01" placeholder="Valor inicial" value="${data.valor ?? data.min ?? ""}">
            <input data-range-final type="number" step="0.01" placeholder="Valor final" value="${data.valor_final ?? data.max ?? ""}">
            <input data-range-description placeholder="Texto exibido" value="${data.descricao || ""}">
            <span class="color-hex-control"><input data-range-color type="color" value="${data.cor || "#22c55e"}"><input data-range-color-hex value="${data.cor || "#22c55e"}" maxlength="7"></span>
            <label class="provider-checkbox"><input data-range-bold type="checkbox" ${data.negrito ? "checked" : ""}><span>Negrito</span></label>
            <button class="icon-button" type="button" data-remove-range title="Remover faixa">×</button>`;
          range.querySelector("[data-range-operator]").value = data.operador || "INTERVALO";
          rangesList.appendChild(range);
          const syncRange = () => {
            range.querySelector("[data-range-final]").hidden = range.querySelector("[data-range-operator]").value !== "INTERVALO";
          };
          range.querySelector("[data-range-operator]").addEventListener("change", syncRange);
          const color = range.querySelector("[data-range-color]");
          const hex = range.querySelector("[data-range-color-hex]");
          color.addEventListener("input", () => { hex.value = color.value.toUpperCase(); });
          hex.addEventListener("input", () => {
            if (/^#[0-9a-f]{6}$/i.test(hex.value)) color.value = hex.value;
          });
          syncRange();
        };
        const syncBuilder = () => {
          const isScreen = nodeKind.value === "TELA";
          setSectionVisible(parentField, nodeKind.value !== "MENU");
          setSectionVisible(screenTypeField, isScreen);
          setSectionVisible(screenOptions, isScreen);
          itemType.value = isScreen ? screenType.value : "GRUPO";
          builder.querySelectorAll("[data-profile-type]").forEach((section) => {
            setSectionVisible(section, isScreen && section.dataset.profileType === itemType.value);
          });
          if (scaleBuilder && itemType.value === "ESCALA") {
            setSectionVisible(scaleBuilder, !scaleSelect.value);
          }
        };
        const resetScaleBuilder = () => {
          questionsList.innerHTML = "";
          rangesList.innerHTML = "";
          addQuestion();
          addRange();
        };
        const updateIconPreview = () => {
          if (!iconPreview || !iconSelect) return;
          iconPreview.setAttribute("data-nav-icon", iconSelect.value || "file-text");
          window.CelerisRenderIcons?.();
        };
        const setField = (name, value) => {
          const field = builder.elements[name];
          if (!field) return;
          if (field.type === "checkbox") field.checked = Boolean(value);
          else field.value = value ?? "";
        };
        openProfileItemModal = async (itemId = "", parentId = "") => {
          builder.reset();
          editItem.value = itemId;
          nodeKind.value = parentId ? "SUBMENU" : "MENU";
          screenType.selectedIndex = 0;
          resetScaleBuilder();
          modalTitle.textContent = itemId ? "Configurar item da estrutura" : "Adicionar item na estrutura do PEP";
          if (parentId) setField("cd_item_pai", parentId);
          if (itemId) {
            const response = await fetch(document.querySelector("[data-profile-tree]").dataset.profileTreeUrl, {
              credentials: "same-origin",
              headers: {Accept: "application/json"},
            });
            const data = await response.json();
            const item = data.items.find((value) => String(value.id) === String(itemId));
            if (!item) return;
            nodeKind.value = item.type === "GRUPO" ? (item.parent_id ? "SUBMENU" : "MENU") : "TELA";
            screenType.value = item.type === "GRUPO" ? screenType.options[0].value : item.type;
            setField("nm_item", item.name);
            setField("cd_item_tecnico", item.technical_key);
            setField("nr_ordem", item.order);
            setField("ds_icone", item.icon || "file-text");
            setField("cd_item_pai", item.parent_id || "");
            setField("ds_acao", item.action);
            setField("ds_url", item.url);
            setField("cd_modelo_documento", item.document_model_id || "");
            setField("cd_escala_clinica", item.configuration.escala || "");
            setField("sn_privado", item.private);
            setField("sn_imprimivel", item.printable);
            setField("sn_permite_criar", item.can_create);
            setField("sn_permite_abandonar", item.can_abandon);
            setField("sn_permite_cancelar", item.can_cancel);
            setField("sn_somente_historico", item.history_only);
          }
          syncBuilder();
          updateIconPreview();
          modal.hidden = false;
          modal.scrollIntoView({ block: "nearest", behavior: "smooth" });
          builder.querySelector('[name="nm_item"]').focus();
        };
        nodeKind.addEventListener("change", syncBuilder);
        screenType.addEventListener("change", syncBuilder);
        iconToggle.addEventListener("click", () => {
          iconDropdown.hidden = !iconDropdown.hidden;
        });
        iconDropdown.addEventListener("click", (event) => {
          const option = event.target.closest("[data-profile-icon-option]");
          if (!option) return;
          iconSelect.value = option.dataset.profileIconOption || "file-text";
          iconDropdown.hidden = true;
          updateIconPreview();
        });
        document.addEventListener("click", (event) => {
          if (!iconDropdown || iconDropdown.hidden) return;
          if (!builder.contains(event.target) || (!iconDropdown.contains(event.target) && !iconToggle.contains(event.target))) {
            iconDropdown.hidden = true;
          }
        });
        scaleSelect.addEventListener("change", syncBuilder);
        builder.querySelector("[data-scale-add-question]").addEventListener("click", () => addQuestion());
        builder.querySelector("[data-scale-add-range]").addEventListener("click", () => addRange());
        questionsList.addEventListener("click", (event) => {
          const question = event.target.closest("[data-scale-question]");
          if (event.target.closest("[data-add-option]")) addOption(question);
          if (event.target.closest("[data-remove-option]")) event.target.closest("[data-scale-option]").remove();
          if (event.target.closest("[data-remove-question]")) {
            question.remove();
            updateTokens();
          }
        });
        questionsList.addEventListener("input", updateTokens);
        rangesList.addEventListener("click", (event) => {
          if (event.target.closest("[data-remove-range]")) event.target.closest("[data-scale-range]").remove();
        });
        expression.addEventListener("dragover", (event) => event.preventDefault());
        expression.addEventListener("drop", (event) => {
          event.preventDefault();
          const token = event.dataTransfer.getData("text/plain");
          const start = expression.selectionStart ?? expression.value.length;
          expression.setRangeText(token, start, expression.selectionEnd ?? start, "end");
        });
        builder.addEventListener("submit", () => {
          questionsJson.value = JSON.stringify([...questionsList.querySelectorAll("[data-scale-question]")].map((question, index) => ({
            chave: slug(question.querySelector("[data-question-key]").value) || `pergunta_${index + 1}`,
            texto: question.querySelector("[data-question-text]").value.trim(),
            opcoes: [...question.querySelectorAll("[data-scale-option]")].map((option, optionIndex) => ({
              valor: slug(option.querySelector("[data-option-value]").value) || `opcao_${optionIndex + 1}`,
              descricao: option.querySelector("[data-option-description]").value.trim(),
              pontos: Number(option.querySelector("[data-option-points]").value || 0),
            })),
          })));
          rangesJson.value = JSON.stringify([...rangesList.querySelectorAll("[data-scale-range]")].map((range) => ({
            operador: range.querySelector("[data-range-operator]").value,
            valor: Number(range.querySelector("[data-range-value]").value || 0),
            valor_final: Number(range.querySelector("[data-range-final]").value || 0),
            descricao: range.querySelector("[data-range-description]").value.trim(),
            cor: range.querySelector("[data-range-color]").value,
            negrito: range.querySelector("[data-range-bold]").checked,
          })));
        });
        builder.querySelector("[data-profile-item-close]").addEventListener("click", () => {
          modal.hidden = true;
        });
        document.querySelector("[data-profile-item-open]").addEventListener("click", () => openProfileItemModal());
        resetScaleBuilder();
        syncBuilder();
        updateIconPreview();
      }
      const tree = document.querySelector("[data-profile-tree]");
      const profileContextMenu = document.querySelector("[data-profile-context-menu]");
      const profileContextId = profileContextMenu.querySelector("[data-profile-context-id]");
      document.querySelectorAll("[data-profile-list-item]").forEach((profileLink) => {
        profileLink.addEventListener("contextmenu", (event) => {
          event.preventDefault();
          profileContextId.value = profileLink.dataset.profileId;
          profileContextMenu.hidden = false;
          profileContextMenu.style.position = "fixed";
          profileContextMenu.style.left = `${Math.min(event.clientX, window.innerWidth - 180)}px`;
          profileContextMenu.style.top = `${Math.min(event.clientY, window.innerHeight - 60)}px`;
        });
      });
      document.addEventListener("click", (event) => {
        if (profileContextMenu && !profileContextMenu.contains(event.target)) profileContextMenu.hidden = true;
      });
      if (!tree) return;
      document.querySelectorAll("[data-profile-tree-toggle]").forEach((toggle) => {
        toggle.addEventListener("click", () => {
          tree.hidden = !tree.hidden;
        });
      });
      tree.querySelectorAll("[data-profile-item-settings]").forEach((button) => {
        button.addEventListener("click", () => {
          openProfileItemModal(button.closest("[data-profile-item]").dataset.profileItem);
        });
      });
      tree.querySelectorAll("[data-profile-item-add-child]").forEach((button) => {
        button.addEventListener("click", () => {
          openProfileItemModal("", button.closest("[data-profile-item]").dataset.profileItem);
        });
      });
      let dragged = null;
      const csrf = document.querySelector("[name='csrfmiddlewaretoken']").value || "";
      const persist = () => {
        const items = [...tree.querySelectorAll("[data-profile-item]")].map((item, index) => ({
          id: Number(item.dataset.profileItem),
          parent_id: item.dataset.parent ? Number(item.dataset.parent) : null,
          order: index,
        }));
        fetch(tree.dataset.profileTreeUrl, {
          method: "PATCH",
          credentials: "same-origin",
          headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
          body: JSON.stringify({items}),
        });
      };
      tree.addEventListener("dragstart", (event) => {
        dragged = event.target.closest("[data-profile-item]");
        if (!dragged) return;
        event.dataTransfer.effectAllowed = "move";
        dragged.classList.add("dragging");
      });
      tree.addEventListener("dragover", (event) => {
        const target = event.target.closest("[data-profile-item]");
        if (
          !dragged
          || !target
          || target === dragged
          || target.dataset.parent !== dragged.dataset.parent
        ) return;
        event.preventDefault();
        const rect = target.getBoundingClientRect();
        tree.insertBefore(dragged, event.clientY < rect.top + rect.height / 2 ? target : target.nextSibling);
      });
      tree.addEventListener("dragend", () => {
        dragged.classList.remove("dragging");
        if (dragged) persist();
        dragged = null;
      });
    })();