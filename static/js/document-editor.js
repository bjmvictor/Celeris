(() => {
  const form = document.querySelector("[data-document-editor-form]");
  if (!form || typeof grapesjs === "undefined") return;

  const readJson = (id, fallback) => {
    const element = document.getElementById(id);
    if (!element) return fallback;
    try {
      return JSON.parse(element.textContent);
    } catch {
      return fallback;
    }
  };
  const signatureToggle = form.querySelector('[name="sn_exibe_assinatura"][type="checkbox"]');
  const signatureOptions = form.querySelector("[data-document-signature-options]");
  const syncSignatureOptions = () => {
    if (signatureOptions) signatureOptions.hidden = !signatureToggle?.checked;
  };
  signatureToggle?.addEventListener("change", syncSignatureOptions);
  syncSignatureOptions();

  const createEditor = (kind) => {
    const elementType = form.dataset.documentElement || "DOCUMENTO";
    const limitedElement = ["CABECALHO", "RODAPE"].includes(elementType);
    const editor = grapesjs.init({
      container: `#editor-${kind}`,
      height: limitedElement ? (elementType === "CABECALHO" ? "300px" : "240px") : "680px",
      width: "auto",
      storageManager: false,
      noticeOnUnload: false,
      deviceManager: { devices: [] },
      i18n: {
        locale: "pt",
        localeFallback: "pt",
        messages: {
          pt: {
            styleManager: { empty: "Selecione um elemento para editar seus estilos" },
            traitManager: { empty: "Selecione um elemento para editar suas propriedades", label: "Configurações" },
          },
        },
      },
      blockManager: {
        blocks: [
          { id: "text", label: "Texto", category: "Conteúdo", content: '<div style="padding:10px">Digite o texto</div>' },
          { id: "heading", label: "Título", category: "Conteúdo", content: "<h2>Título</h2>" },
          { id: "image", label: "Imagem", category: "Conteúdo", select: true, content: { type: "image" } },
          { id: "line", label: "Linha", category: "Estrutura", content: '<hr style="border:0;border-top:1px solid #222">' },
          { id: "columns", label: "2 colunas", category: "Estrutura", content: '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px"><div>Coluna 1</div><div>Coluna 2</div></div>' },
          { id: "columns-3", label: "3 colunas", category: "Estrutura", content: '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px"><div>Coluna 1</div><div>Coluna 2</div><div>Coluna 3</div></div>' },
          { id: "inline-row", label: "Linha flexível", category: "Estrutura", content: '<div style="display:flex;align-items:center;gap:6px;min-height:32px"><span>Rótulo:</span><span>Valor</span></div>' },
          { id: "page-break", label: "Quebra", category: "Impressão", content: '<div style="break-after:page;border-top:1px dashed #999;padding:6px;color:#777">Quebra de página</div>' },
          { id: "label-patient", label: "Paciente + valor", category: "Campos", content: '<div style="display:flex;align-items:center;gap:5px"><strong>Paciente:</strong><span data-variable="paciente.nome">{{ paciente.nome }}</span></div>' },
          { id: "patient", label: "Paciente", category: "Campos", content: '<span style="display:inline" data-variable="paciente.nome">{{ paciente.nome }}</span>' },
          { id: "record", label: "Prontuário", category: "Campos", content: '<span style="display:inline" data-variable="paciente.codigo">{{ paciente.codigo }}</span>' },
          { id: "attendance", label: "Atendimento", category: "Campos", content: '<span style="display:inline" data-variable="atendimento.codigo">{{ atendimento.codigo }}</span>' },
          { id: "provider", label: "Prestador", category: "Campos", content: '<span style="display:inline" data-variable="prestador.nome">{{ prestador.nome }}</span>' },
        ],
      },
      styleManager: {
        sectors: [
          { name: "Tipografia", open: true, buildProps: ["font-family", "font-size", "font-weight", "color", "text-align", "line-height", "letter-spacing"] },
          { name: "Dimensões", open: false, buildProps: ["width", "height", "padding", "margin"] },
          { name: "Posição", open: false, buildProps: ["display", "position", "top", "right", "bottom", "left"] },
          { name: "Decoração", open: false, buildProps: ["background-color", "border", "border-radius", "box-shadow"] },
        ],
      },
    });
    readJson("reusable-document-fields", []).forEach((field) => {
      const content = field.ds_html_impressao;
      if (!content) return;
      editor.BlockManager.add(`reusable-field-${field.cd_modelo_documento}`, {
        label: field.nm_modelo,
        category: "Campos reutilizáveis",
        content,
      });
    });
    const project = readJson(`initial-project-${kind}`, {});
    const html = readJson(`initial-html-${kind}`, "");
    const css = readJson(`initial-css-${kind}`, "");
    if (project && Object.keys(project).length) editor.loadProjectData(project);
    else {
      const initialContent = limitedElement
        ? `<section style="width:210mm;min-height:${elementType === "CABECALHO" ? "35mm" : "22mm"};max-height:${elementType === "CABECALHO" ? "55mm" : "35mm"};margin:auto;padding:6mm;background:#fff;color:#111;overflow:hidden">Monte aqui o ${elementType === "CABECALHO" ? "cabeçalho" : "rodapé"}.</section>`
        : '<main style="width:210mm;min-height:297mm;margin:auto;padding:18mm;background:#fff;color:#111">Monte aqui o relatório que será impresso.</main>';
      editor.setComponents(html || initialContent);
      editor.setStyle(css || "");
    }
    return editor;
  };

  const editors = { impressao: createEditor("impressao") };
  const builder = document.querySelector("[data-document-form-builder]");
  const fieldList = builder?.querySelector("[data-form-field-list]");
  const fieldEmpty = builder?.querySelector("[data-form-field-empty]");
  const initialScreenProject = readJson("initial-project-tela", {});
  const initialScreenHtml = readJson("initial-html-tela", "");
  let formFields = Array.isArray(initialScreenProject.formFields) ? initialScreenProject.formFields : [];
  const gridConfig = {
    columns: Math.max(1, Number(initialScreenProject.grid?.columns || 2)),
    rows: Math.max(1, Number(initialScreenProject.grid?.rows || 4)),
    fontSize: Math.max(7, Number(initialScreenProject.grid?.fontSize || 14)),
    fontFamily: initialScreenProject.grid?.fontFamily || "Arial, sans-serif",
  };
  const reusableFields = readJson("reusable-document-fields", []);
  const customVariables = readJson("custom-document-variables", []);
  const printElements = readJson("reusable-print-elements", []);
  const testContexts = readJson("document-test-contexts", []);
  const testContextSelect = document.querySelector("[data-document-test-context]");
  const customVariableNameInput = document.querySelector("[data-custom-variable-name]");
  const customVariableExpressionInput = document.querySelector("[data-custom-variable-expression]");
  const customVariableHelpModal = document.querySelector("[data-custom-variable-help-modal]");
  const systemModelCopyModal = document.querySelector("[data-system-model-copy-modal]");
  const documentClearModal = document.querySelector("[data-document-clear-modal]");
  const undoButton = document.querySelector('[data-action="undo"]');
  const redoButton = document.querySelector('[data-action="redo"]');
  const historyIndicator = document.querySelector("[data-editor-history-indicator]");
  const undoStack = [];
  const redoStack = [];
  let historyCurrent = "";
  let restoringHistory = false;
  let historyIndicatorTimer = 0;
  let draftSyncTimer = 0;
  let draftSyncPending = false;
  let draftRestored = false;
  let internalEditorNavigation = false;
  const draftUrl = form.dataset.editorDraftUrl || "";
  const draftGuideKey = form.dataset.editorGuideKey || "editor-documentos";
  const activeEditorTab = () => (
    document.querySelector("[data-editor-tab].active")?.dataset.editorTab
    || (form.dataset.documentElement === "CAMPO" ? "tela" : "impressao")
  );
  if (customVariableNameInput) customVariableNameInput.value = initialScreenProject.customVariable?.name || "";
  if (customVariableExpressionInput) customVariableExpressionInput.value = initialScreenProject.customVariable?.expression || "";
  document.querySelector("[data-custom-variable-help-open]")?.addEventListener("click", () => {
    customVariableHelpModal.hidden = false;
  });
  customVariableHelpModal?.querySelector("[data-custom-variable-help-close]")?.addEventListener("click", () => {
    customVariableHelpModal.hidden = true;
  });
  customVariableHelpModal?.querySelectorAll("[data-variable-help-topic]").forEach((button) => {
    button.addEventListener("click", () => {
      customVariableHelpModal.querySelectorAll("[data-variable-help-topic]").forEach((item) => {
        item.classList.toggle("active", item === button);
      });
      customVariableHelpModal.querySelectorAll("[data-variable-help-panel]").forEach((panel) => {
        panel.hidden = panel.dataset.variableHelpPanel !== button.dataset.variableHelpTopic;
      });
    });
  });
  customVariableHelpModal?.addEventListener("click", (event) => {
    if (event.target === customVariableHelpModal) customVariableHelpModal.hidden = true;
  });
  form.addEventListener("submit", (event) => {
    if (
      form.dataset.systemProtected !== "true"
      || form.dataset.canOverwriteSystem === "true"
      || form.dataset.copySubmit === "true"
    ) return;
    event.preventDefault();
    systemModelCopyModal.hidden = false;
  }, true);
  systemModelCopyModal?.querySelector("[data-system-model-copy-cancel]")?.addEventListener("click", () => {
    systemModelCopyModal.hidden = true;
  });
  systemModelCopyModal?.querySelector("[data-system-model-copy-confirm]")?.addEventListener("click", () => {
    form.elements.salvar_como_empresa.value = "1";
    form.elements.pasta_selecionada.value = systemModelCopyModal.querySelector("[data-system-model-copy-folder]")?.value || "";
    form.dataset.copySubmit = "true";
    systemModelCopyModal.hidden = true;
    form.requestSubmit();
  });
  const customVariableTestButton = document.querySelector("[data-custom-variable-test]");
  const customVariableTestResult = document.querySelector("[data-custom-variable-test-result]");
  customVariableTestButton?.addEventListener("click", async () => {
    const expression = customVariableExpressionInput?.value.trim() || "";
    if (!expression) {
      customVariableTestResult.hidden = false;
      customVariableTestResult.className = "document-variable-test-result error";
      customVariableTestResult.textContent = "Informe uma expressão antes de executar.";
      return;
    }
    customVariableTestButton.disabled = true;
    try {
      const payload = new FormData();
      payload.append("expressao", expression);
      payload.append("atendimento", testContextSelect?.value || "");
      payload.append("csrfmiddlewaretoken", form.querySelector("[name='csrfmiddlewaretoken']")?.value || "");
      const response = await fetch(customVariableTestButton.dataset.testUrl, {
        method: "POST",
        body: payload,
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      });
      const result = await response.json();
      customVariableTestResult.hidden = false;
      customVariableTestResult.className = `document-variable-test-result ${result.ok ? "success" : "error"}`;
      customVariableTestResult.textContent = result.ok
        ? `Resultado: ${String(result.result ?? "")}`
        : result.error || "Não foi possível executar a expressão.";
    } catch {
      customVariableTestResult.hidden = false;
      customVariableTestResult.className = "document-variable-test-result error";
      customVariableTestResult.textContent = "Falha ao executar a expressão.";
    } finally {
      customVariableTestButton.disabled = false;
    }
  });

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[character]));
  const formatRichText = (value) => {
    const template = document.createElement("template");
    template.innerHTML = String(value || "")
      .replace(/<left>/gi, '<span style="display:block;text-align:left">')
      .replace(/<\/left>/gi, "</span>")
      .replace(/<center>/gi, '<span style="display:block;text-align:center">')
      .replace(/<\/center>/gi, "</span>")
      .replace(/<right>/gi, '<span style="display:block;text-align:right">')
      .replace(/<\/right>/gi, "</span>");
    template.content.querySelectorAll("script, iframe, object, embed, link, meta").forEach((element) => element.remove());
    template.content.querySelectorAll("*").forEach((element) => {
      [...element.attributes].forEach((attribute) => {
        const name = attribute.name.toLowerCase();
        if (name.startsWith("on")) element.removeAttribute(attribute.name);
        if (["href", "src"].includes(name) && /^\s*javascript:/i.test(attribute.value)) {
          element.removeAttribute(attribute.name);
        }
        if (name === "style" && /(expression\s*\(|javascript\s*:)/i.test(attribute.value)) {
          element.removeAttribute(attribute.name);
        }
      });
    });
    const textNodes = [];
    const walker = document.createTreeWalker(template.content, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) textNodes.push(walker.currentNode);
    textNodes.forEach((node) => {
      if (node.parentElement?.closest("pre, code")) return;
      const variables = [];
      const protectedText = String(node.textContent || "").replace(/{{\s*[^}]+\s*}}/g, (token) => {
        variables.push(token);
        return `\uE000${variables.length - 1}\uE001`;
      });
      let formatted = escapeHtml(protectedText)
        .replace(/\*([^*\n]+)\*/g, "<strong>$1</strong>")
        .replace(/_([^_\n]+)_/g, "<u>$1</u>")
        .replace(/(^|[\s(>])\/([^/\n]+)\/(?=$|[\s.,;!?<)])/g, "$1<em>$2</em>")
        .replace(/\n/g, "<br>");
      variables.forEach((token, index) => {
        formatted = formatted.replace(`\uE000${index}\uE001`, escapeHtml(token));
      });
      const fragment = document.createElement("template");
      fragment.innerHTML = formatted;
      node.replaceWith(fragment.content);
    });
    return template.innerHTML;
  };
  const normalizeName = (value) => String(value || "")
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/^campo_/, "").replace(/[^a-zA-Z0-9_]+/g, "_")
    .replace(/^_+|_+$/g, "").toLowerCase();

  const splitStructuredOptions = (value) => {
    const items = [];
    let current = "";
    let bracketDepth = 0;
    let quote = "";
    for (const character of String(value || "")) {
      if (quote) {
        current += character;
        if (character === quote) quote = "";
        continue;
      }
      if (character === '"' || character === "'") {
        quote = character;
        current += character;
      } else if (character === "[") {
        bracketDepth += 1;
        current += character;
      } else if (character === "]") {
        bracketDepth = Math.max(0, bracketDepth - 1);
        current += character;
      } else if (character === "," && bracketDepth === 0) {
        if (current.trim()) items.push(current.trim());
        current = "";
      } else {
        current += character;
      }
    }
    if (current.trim()) items.push(current.trim());
    return items;
  };

  const parseEmbeddedField = (option) => {
    const text = String(option || "").trim();
    const literal = text.match(/^(["'])(.*)\1$/);
    if (literal) return { type: "literal", text: literal[2] };
    const match = text.match(/^(.*?)\[([a-zA-Z0-9_]+)(?:\s*[;,]\s*([^\]]+))?\]$/);
    if (!match) return { type: "field", label: text, name: normalizeName(text), placeholder: "" };
    return {
      type: "field",
      label: match[1].trim(),
      name: normalizeName(match[2]),
      placeholder: String(match[3] || "").trim(),
    };
  };

  if (!formFields.length && initialScreenHtml) {
    const parsed = new DOMParser().parseFromString(initialScreenHtml, "text/html");
    formFields = [...parsed.querySelectorAll("[data-document-field][name]")].map((field, index) => ({
      id: `legacy-${index}`,
      name: normalizeName(field.name),
      label: field.closest("label")?.childNodes?.[0]?.textContent?.trim() || field.placeholder || `Campo ${index + 1}`,
      type: field.tagName === "TEXTAREA" ? "textarea" : (field.tagName === "SELECT" ? "select" : field.type || "text"),
      placeholder: field.placeholder || "",
      required: field.required,
      options: field.tagName === "SELECT" ? [...field.options].map((option) => option.textContent).filter(Boolean).join(", ") : "",
    }));
  }
  formFields = formFields.map((field, index) => ({
    id: field.id || `field-${index}`,
    name: normalizeName(field.name || `campo_${index + 1}`),
    label: field.label || `Campo ${index + 1}`,
    type: field.type || "text",
    placeholder: field.placeholder || "",
    prefix: field.prefix || "",
    suffix: field.suffix || "",
    required: Boolean(field.required),
    readonly: Boolean(field.readonly),
    options: field.options || "",
    content: field.content || "",
    displayStyle: field.displayStyle || "text",
    sourceTable: field.sourceTable || "",
    sourceValueField: field.sourceValueField || "cd_valor",
    sourceDisplayField: field.sourceDisplayField || "ds_valor",
    binding: field.binding || "",
    fontSize: Math.max(7, Number(field.fontSize || gridConfig.fontSize)),
    fontFamily: field.fontFamily || gridConfig.fontFamily,
    fontSizeCustom: field.fontSizeCustom === true || Boolean(field.fontSize && Number(field.fontSize) !== gridConfig.fontSize),
    fontFamilyCustom: field.fontFamilyCustom === true || Boolean(field.fontFamily && field.fontFamily !== gridConfig.fontFamily),
    textColor: field.textColor || "#111111",
    imageUrl: field.imageUrl || "",
    imageWidth: Math.max(1, Number(field.imageWidth || 240)),
    imageHeight: Math.max(1, Number(field.imageHeight || 120)),
    lockAspectRatio: field.lockAspectRatio !== false,
    imageAspectRatio: Math.max(0.01, Number(field.imageAspectRatio || 2)),
    lineColor: field.lineColor || "#111111",
    lineWidth: Math.max(1, Number(field.lineWidth || 1)),
    lineStyle: field.lineStyle || "solid",
    marginTop: Math.max(0, Number(field.marginTop || 0)),
    marginBottom: Math.max(0, Number(field.marginBottom || 0)),
    col: Math.max(1, Number(field.col || ((index % gridConfig.columns) + 1))),
    row: Math.max(1, Number(field.row || (Math.floor(index / gridConfig.columns) + 1))),
    colSpan: Math.max(1, Number(field.colSpan || 1)),
    rowSpan: Math.max(1, Number(field.rowSpan || 1)),
    reusableId: field.reusableId || null,
  }));
  const initialPrintProject = readJson("initial-project-impressao", {});
  const initialPrintHtml = readJson("initial-html-impressao", "");
  const printBuilder = document.querySelector("[data-document-print-builder]");
  const printElementList = printBuilder?.querySelector("[data-print-element-list]");
  const printColumnsInput = printBuilder?.querySelector("[data-print-grid-columns]");
  const printRowsInput = printBuilder?.querySelector("[data-print-grid-rows]");
  const printFontSizeInput = printBuilder?.querySelector("[data-print-grid-font-size]");
  const printFontFamilyInput = printBuilder?.querySelector("[data-print-grid-font-family]");
  const printSettingsModal = document.querySelector("[data-print-settings-modal]");
  let activePrintElement = null;
  const printElementFromField = (field) => ({
    id: `print-${field.id}`,
    type: field.type === "image"
      ? "image"
      : field.type === "static-text"
      ? "text"
      : field.type === "static-variable"
      ? "variable"
      : field.type === "line"
      ? "line"
      : "field",
    label: field.label,
    content: field.type === "static-text"
      ? field.content
      : field.type === "image" || field.type === "line" || field.type === "static-variable"
      ? ""
      : field.type === "multiple-fields"
      ? splitStructuredOptions(field.options).map((option) => {
          const parsed = parseEmbeddedField(option);
          if (parsed.type === "literal") return parsed.text;
          const value = `{{ campo.${parsed.name} }}`;
          return parsed.label ? `<strong>${escapeHtml(parsed.label)}:</strong> ${value}` : value;
        }).join(" ")
      : `${field.prefix || ""}{{ ${field.binding || `campo.${field.name}`} }}${field.suffix || ""}`,
    sourceField: field.type === "static-variable" ? field.binding : (field.binding || `campo.${field.name}`),
    fontSize: field.fontSizeCustom ? field.fontSize : "",
    fontFamily: field.fontFamilyCustom ? field.fontFamily : "",
    fontSizeCustom: Boolean(field.fontSizeCustom),
    fontFamilyCustom: Boolean(field.fontFamilyCustom),
    textColor: field.textColor || "#111111",
    hideLabel: false,
    showBottomBorder: true,
    margin: "10px 0 0",
    padding: "",
    imageUrl: field.imageUrl || "",
    imageWidth: field.imageWidth || 240,
    imageHeight: field.imageHeight || 120,
    lineColor: field.lineColor || "#111111",
    lineWidth: field.lineWidth || 1,
    lineStyle: field.lineStyle || "solid",
    marginTop: Math.max(0, Number(field.marginTop || 0)),
    marginBottom: Math.max(0, Number(field.marginBottom || 0)),
    col: field.col,
    row: field.row,
    colSpan: field.colSpan,
    rowSpan: field.rowSpan,
  });
  let printLayout = initialPrintProject.printLayout || {
    grid: {
      columns: gridConfig.columns,
      rows: Math.max(gridConfig.rows, 1),
      fontSize: 11,
      fontFamily: "Arial, sans-serif",
    },
    elements: formFields.map(printElementFromField),
  };
  if (!initialPrintProject.printLayout && !formFields.length && initialPrintHtml) {
    printLayout = {
      grid: { columns: 1, rows: 1, fontSize: 11, fontFamily: "Arial, sans-serif" },
      elements: [{
        id: "existing-print-content",
        type: "html",
        label: "Conteúdo existente",
        content: initialPrintHtml,
        col: 1,
        row: 1,
        colSpan: 1,
        rowSpan: 1,
      }],
    };
  }
  printLayout.grid = {
    columns: Math.max(1, Number(printLayout.grid?.columns || gridConfig.columns || 1)),
    rows: Math.max(1, Number(printLayout.grid?.rows || gridConfig.rows || 4)),
    fontSize: Math.max(7, Number(printLayout.grid?.fontSize || 11)),
    fontFamily: printLayout.grid?.fontFamily || "Arial, sans-serif",
  };
  printLayout.elements = (printLayout.elements || []).map((element, index) => ({
    id: element.id || `print-element-${index}`,
    type: element.type || "text",
    label: element.label ?? (element.type === "variable" ? "" : "Elemento"),
    content: element.content || "",
    sourceField: element.sourceField || "",
    hideLabel: Boolean(element.hideLabel),
    labelColor: element.labelColor || "#111111",
    textColor: element.textColor || "#111111",
    textBold: Boolean(element.textBold),
    textAlign: element.textAlign || "left",
    verticalAlign: element.verticalAlign || "start",
    fontSize: element.fontSize ? Math.max(7, Number(element.fontSize)) : "",
    fontFamily: element.fontFamily || "",
    fontSizeCustom: element.fontSizeCustom === true || Boolean(element.fontSize && Number(element.fontSize) !== printLayout.grid.fontSize),
    fontFamilyCustom: element.fontFamilyCustom === true || Boolean(element.fontFamily && element.fontFamily !== printLayout.grid.fontFamily),
    imageUrl: element.imageUrl || "",
    imageWidth: Math.max(1, Number(element.imageWidth || 240)),
    imageHeight: Math.max(1, Number(element.imageHeight || 120)),
    lineColor: element.lineColor || "#111111",
    lineWidth: Math.max(1, Number(element.lineWidth || 1)),
    lineStyle: element.lineStyle || "solid",
    showBottomBorder: element.showBottomBorder !== false,
    marginTop: Math.max(0, Number(element.marginTop || 0)),
    marginBottom: Math.max(0, Number(element.marginBottom || 0)),
    margin: element.margin || "",
    padding: element.padding || "",
    col: Math.max(1, Number(element.col || 1)),
    row: Math.max(1, Number(element.row || index + 1)),
    colSpan: Math.max(1, Number(element.colSpan || 1)),
    rowSpan: Math.max(1, Number(element.rowSpan || 1)),
  }));
  printLayout.elements.forEach((element) => {
    element.col = Math.min(printLayout.grid.columns, element.col);
    element.row = Math.min(printLayout.grid.rows, element.row);
    element.colSpan = Math.min(element.colSpan, printLayout.grid.columns - element.col + 1);
    element.rowSpan = Math.min(element.rowSpan, printLayout.grid.rows - element.row + 1);
  });
  const effectivePrintColSpan = (element) => element.colSpan;
  const printLineJunctions = () => {
    const horizontal = printLayout.elements.filter((element) => element.type === "line");
    const vertical = printLayout.elements.filter((element) => element.type === "vline");
    const occupying = (row, col) => printLayout.elements.filter((element) => (
      row >= element.row
      && row < element.row + element.rowSpan
      && col >= element.col
      && col < element.col + element.colSpan
    ));
    const junctions = [];
    for (let row = 1; row <= printLayout.grid.rows; row += 1) {
      for (let col = 1; col <= printLayout.grid.columns; col += 1) {
        const occupants = occupying(row, col);
        const verticalHere = vertical.find((line) => occupants.includes(line));
        if (occupants.some((element) => element !== verticalHere)) continue;
        const leftLine = horizontal.find((line) => row >= line.row && row < line.row + line.rowSpan && line.col + line.colSpan === col);
        const rightLine = horizontal.find((line) => row >= line.row && row < line.row + line.rowSpan && line.col === col + 1);
        const topLine = verticalHere || vertical.find((line) => col >= line.col && col < line.col + line.colSpan && line.row + line.rowSpan === row);
        const bottomLine = verticalHere || vertical.find((line) => col >= line.col && col < line.col + line.colSpan && line.row === row + 1);
        const top = Boolean(topLine && (!verticalHere || row > verticalHere.row));
        const bottom = Boolean(bottomLine && (!verticalHere || row < verticalHere.row + verticalHere.rowSpan - 1));
        if ((leftLine || rightLine) && (top || bottom)) {
          junctions.push({
            row,
            col,
            left: leftLine,
            right: rightLine,
            top: top ? topLine : null,
            bottom: bottom ? bottomLine : null,
          });
        }
      }
    }
    return junctions;
  };
  const lineJunctionHtml = (junction, positioned = false, customPosition = "") => {
    const position = customPosition || (positioned ? `grid-column:${junction.col};grid-row:${junction.row};` : "");
    const layer = positioned ? "z-index:2;background:#fff;" : "";
    const armStyle = (line, direction) => {
      if (!line) return "";
      const color = escapeHtml(line.lineColor || "#111111");
      const style = escapeHtml(line.lineStyle || "solid");
      const width = Math.max(style === "double" ? 3 : 1, Number(line.lineWidth || 1));
      const placement = {
        left: "left:0;right:50%;top:50%;",
        right: "left:50%;right:0;top:50%;",
        top: "top:0;bottom:50%;left:50%;",
        bottom: "top:50%;bottom:0;left:50%;",
      }[direction];
      const border = ["left", "right"].includes(direction)
        ? `border-top:${width}px ${style} ${color}`
        : `border-left:${width}px ${style} ${color}`;
      return `<span style="position:absolute;${placement}${border}"></span>`;
    };
    return `<div class="document-line-junction" aria-label="Junção automática" style="${position}${layer}position:relative;min-width:0;min-height:${positioned ? 0 : 24}px;pointer-events:none">`
      + armStyle(junction.left, "left")
      + armStyle(junction.right, "right")
      + armStyle(junction.top, "top")
      + armStyle(junction.bottom, "bottom")
      + "</div>";
  };
  const printGridColumns = () => Array.from({ length: printLayout.grid.columns }, (_, index) => {
    const column = index + 1;
    const occupants = printLayout.elements.filter((element) => (
      !["line", "pagebreak"].includes(element.type)
      && column >= element.col
      && column < element.col + element.colSpan
    ));
    const imageOnly = occupants.length > 0 && occupants.every((element) => (
      element.type === "image" && element.colSpan === 1
    ));
    const verticalOnly = occupants.length > 0 && occupants.every((element) => element.type === "vline");
    if (!occupants.length || verticalOnly) return "4px";
    return imageOnly ? "max-content" : "minmax(0,1fr)";
  }).join(" ");

  const captureEditorState = () => JSON.stringify({
    gridConfig,
    formFields,
    printLayout,
    activeTab: activeEditorTab(),
    customVariableName: customVariableNameInput?.value || "",
    customVariableExpression: customVariableExpressionInput?.value || "",
  });
  const updateHistoryButtons = () => {
    if (undoButton) undoButton.disabled = undoStack.length === 0;
    if (redoButton) redoButton.disabled = redoStack.length === 0;
  };
  const showHistoryIndicator = (message) => {
    if (!historyIndicator) return;
    window.clearTimeout(historyIndicatorTimer);
    historyIndicator.textContent = message;
    historyIndicator.hidden = false;
    historyIndicatorTimer = window.setTimeout(() => {
      historyIndicator.hidden = true;
    }, 1800);
  };
  const registerHistoryState = () => {
    if (restoringHistory) return;
    const nextState = captureEditorState();
    if (!historyCurrent) {
      historyCurrent = nextState;
      updateHistoryButtons();
      return;
    }
    if (nextState === historyCurrent) return;
    const previousState = JSON.parse(historyCurrent);
    previousState.activeTab = activeEditorTab();
    undoStack.push(JSON.stringify(previousState));
    if (undoStack.length > 80) undoStack.shift();
    historyCurrent = nextState;
    redoStack.length = 0;
    updateHistoryButtons();
  };
  const setEditorDirty = () => {
    form.dataset.dirty = "true";
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton && document.body.dataset.canSave === "true") saveButton.disabled = false;
    scheduleDraftSync();
  };
  const markEditorDirty = () => {
    registerHistoryState();
    setEditorDirty();
  };
  const draftEndpoint = () => {
    if (!draftUrl) return "";
    const url = new URL(draftUrl, window.location.origin);
    url.searchParams.set("modelo", form.dataset.documentModelId || "");
    url.searchParams.set("guia", draftGuideKey);
    return url.toString();
  };
  const csrfToken = () => form.querySelector("[name='csrfmiddlewaretoken']")?.value || "";
  const captureDraftState = () => ({
    editorState: JSON.parse(captureEditorState()),
    undoStack: [...undoStack],
    redoStack: [...redoStack],
    historyCurrent,
    fields: [...form.elements]
      .filter((field) => field.name && !["csrfmiddlewaretoken", "return_to"].includes(field.name))
      .map((field) => ({
        name: field.name,
        type: field.type,
        checked: Boolean(field.checked),
        value: field instanceof HTMLSelectElement && field.multiple
          ? [...field.selectedOptions].map((option) => option.value)
          : field.value,
      })),
  });
  const syncEditorDraft = ({ keepalive = false } = {}) => {
    const endpoint = draftEndpoint();
    if (!endpoint || restoringHistory) return Promise.resolve(false);
    window.clearTimeout(draftSyncTimer);
    draftSyncPending = true;
    return fetch(endpoint, {
      method: "POST",
      credentials: "same-origin",
      keepalive,
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify({ state: captureDraftState() }),
    }).then((response) => {
      if (!response.ok) throw new Error("Falha ao salvar rascunho");
      draftSyncPending = false;
      return true;
    }).catch(() => {
      draftSyncPending = true;
      return false;
    });
  };
  const scheduleDraftSync = () => {
    if (!draftUrl || restoringHistory) return;
    draftSyncPending = true;
    window.clearTimeout(draftSyncTimer);
    draftSyncTimer = window.setTimeout(() => syncEditorDraft(), 650);
  };
  const deleteEditorDraft = () => {
    const endpoint = draftEndpoint();
    if (!endpoint) return Promise.resolve();
    draftSyncPending = false;
    return fetch(endpoint, {
      method: "DELETE",
      credentials: "same-origin",
      keepalive: true,
      headers: { "X-CSRFToken": csrfToken() },
    }).catch(() => {});
  };
  const restoreFormFieldsFromDraft = (fields) => {
    (fields || []).forEach((saved) => {
      const candidates = [...form.elements].filter((field) => field.name === saved.name);
      candidates.forEach((field) => {
        if (field.type === "checkbox" || field.type === "radio") field.checked = Boolean(saved.checked);
        else if (field instanceof HTMLSelectElement && field.multiple) {
          const selected = Array.isArray(saved.value) ? saved.value.map(String) : [];
          [...field.options].forEach((option) => { option.selected = selected.includes(option.value); });
        } else if (!field.readOnly) field.value = saved.value ?? "";
      });
    });
  };
  const restoreEditorDraft = async () => {
    const endpoint = draftEndpoint();
    if (!endpoint) return;
    try {
      const response = await fetch(endpoint, { credentials: "same-origin" });
      const payload = response.ok ? await response.json() : null;
      const draft = payload?.state;
      if (!draft?.editorState) return;
      restoringHistory = true;
      const state = draft.editorState;
      gridConfig.columns = state.gridConfig?.columns || gridConfig.columns;
      gridConfig.rows = state.gridConfig?.rows || gridConfig.rows;
      gridConfig.fontSize = state.gridConfig?.fontSize || gridConfig.fontSize;
      gridConfig.fontFamily = state.gridConfig?.fontFamily || gridConfig.fontFamily;
      formFields = Array.isArray(state.formFields) ? state.formFields : formFields;
      printLayout = state.printLayout || printLayout;
      if (customVariableNameInput) customVariableNameInput.value = state.customVariableName || "";
      if (customVariableExpressionInput) customVariableExpressionInput.value = state.customVariableExpression || "";
      restoreFormFieldsFromDraft(draft.fields);
      undoStack.splice(0, undoStack.length, ...(draft.undoStack || []));
      redoStack.splice(0, redoStack.length, ...(draft.redoStack || []));
      activateEditorTab(state.activeTab || "tela");
      updateGridInputs();
      renderFieldBuilder();
      renderPrintBuilder();
      historyCurrent = draft.historyCurrent || captureEditorState();
      form.dataset.dirty = "true";
      restoringHistory = false;
      draftSyncPending = false;
      draftRestored = true;
      updateHistoryButtons();
      showHistoryIndicator("Rascunho restaurado");
    } catch {
      restoringHistory = false;
    }
  };
  const firstFreePosition = () => {
    for (let row = 1; row <= gridConfig.rows; row += 1) {
      for (let col = 1; col <= gridConfig.columns; col += 1) {
        if (!formFields.some((field) => field.row === row && field.col === col)) return { row, col };
      }
    }
    gridConfig.rows += 1;
    return { row: gridConfig.rows, col: 1 };
  };
  const firstFreePrintPosition = () => {
    for (let row = 1; row <= printLayout.grid.rows; row += 1) {
      for (let col = 1; col <= printLayout.grid.columns; col += 1) {
        if (!printLayout.elements.some((element) => element.row === row && element.col === col)) return { row, col };
      }
    }
    printLayout.grid.rows += 1;
    return { row: printLayout.grid.rows, col: 1 };
  };
  const settingsModal = document.querySelector("[data-field-settings-modal]");
  const imageFileInput = settingsModal?.querySelector("[data-field-image-file]");
  const fieldSettingsHelp = settingsModal?.querySelector("[data-field-settings-help]");
  const screenVariablePalette = settingsModal?.querySelector("[data-screen-variable-palette]");
  const screenVariableList = settingsModal?.querySelector("[data-screen-variable-list]");
  const screenVariableSearch = settingsModal?.querySelector("[data-screen-variable-search]");
  const screenContentInput = settingsModal?.querySelector("[data-screen-content-input]");
  const screenBindingSelect = settingsModal?.querySelector('[data-settings-property="binding"]');
  let screenVariableOptionsProvider = () => [];
  let settingsField = null;
  const settingsInputs = [...(settingsModal?.querySelectorAll("[data-settings-property]") || [])];
  const insertScreenVariable = (variable) => {
    if (!screenContentInput || !variable) return;
    const token = `{{ ${variable} }}`;
    const start = screenContentInput.selectionStart ?? screenContentInput.value.length;
    const end = screenContentInput.selectionEnd ?? start;
    screenContentInput.setRangeText(token, start, end, "end");
    screenContentInput.focus();
    screenContentInput.dispatchEvent(new Event("input", { bubbles: true }));
  };
  const renderScreenVariablePalette = () => {
    if (!screenVariableList) return;
    screenVariableList.replaceChildren();
    screenVariableOptionsProvider().forEach(([value, label]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.draggable = true;
      button.dataset.screenVariable = value;
      button.innerHTML = `<strong>${escapeHtml(label)}</strong><code>{{ ${escapeHtml(value)} }}</code>`;
      button.addEventListener("click", () => insertScreenVariable(value));
      button.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/document-variable", value);
        event.dataTransfer.effectAllowed = "copy";
      });
      screenVariableList.appendChild(button);
    });
    screenVariableSearch?.dispatchEvent(new Event("input"));
  };
  const syncScreenSettingsHeight = () => {
    if (!screenVariablePalette || screenVariablePalette.hidden || settingsModal.hidden) return;
    const card = settingsModal.querySelector(":scope > .card");
    if (!card) return;
    screenVariablePalette.style.height = `${Math.min(card.offsetHeight, window.innerHeight * 0.92)}px`;
  };
  const renderScreenBindingOptions = (selectedValue = "") => {
    if (!screenBindingSelect) return;
    const labels = {
      paciente: "Paciente",
      atendimento: "Atendimento",
      documento: "Documento",
      prestador: "Prestador",
      empresa: "Empresa",
      variavel: "Variáveis personalizadas",
      campo: "Campos do formulário",
      outras: "Outras variáveis",
    };
    const groups = new Map();
    screenVariableOptionsProvider().forEach(([value, label]) => {
      const prefix = String(value).split(".")[0];
      const group = labels[prefix] ? prefix : "outras";
      if (!groups.has(group)) groups.set(group, []);
      groups.get(group).push([value, label]);
    });
    screenBindingSelect.replaceChildren(new Option("", ""));
    groups.forEach((options, group) => {
      const optgroup = document.createElement("optgroup");
      optgroup.label = labels[group];
      options.forEach(([value, label]) => optgroup.appendChild(new Option(label, value)));
      screenBindingSelect.appendChild(optgroup);
    });
    screenBindingSelect.value = selectedValue;
  };
  const syncHexColorControls = (container) => {
    container?.querySelectorAll("[data-color-hex-for]").forEach((hexInput) => {
      const property = hexInput.dataset.colorHexFor;
      const colorInput = container.querySelector(
        `[data-settings-property="${property}"], [data-print-property="${property}"]`,
      );
      if (colorInput) hexInput.value = String(colorInput.value || "#111111").toUpperCase();
    });
  };
  document.querySelectorAll("[data-color-hex-for]").forEach((hexInput) => {
    const container = hexInput.closest("[data-field-settings-modal], [data-print-settings-modal]");
    const property = hexInput.dataset.colorHexFor;
    const colorInput = container?.querySelector(
      `[data-settings-property="${property}"], [data-print-property="${property}"]`,
    );
    colorInput?.addEventListener("input", () => {
      hexInput.value = colorInput.value.toUpperCase();
    });
    hexInput.addEventListener("input", () => {
      const value = hexInput.value.trim();
      if (/^#[0-9a-f]{6}$/i.test(value) && colorInput) colorInput.value = value;
    });
    hexInput.addEventListener("blur", () => {
      if (colorInput) hexInput.value = colorInput.value.toUpperCase();
    });
  });
  const updateVisibleFieldSettings = () => {
    const selectedType = settingsModal?.querySelector('[data-settings-property="type"]')?.value || "text";
    settingsModal?.querySelectorAll("[data-setting-types]").forEach((container) => {
      const visible = container.dataset.settingTypes.split(",").includes(selectedType);
      container.hidden = !visible;
      container.querySelectorAll("input, select, textarea").forEach((input) => {
        input.disabled = !visible;
      });
    });
    if (screenVariablePalette) screenVariablePalette.hidden = selectedType !== "static-text";
    if (fieldSettingsHelp && !fieldSettingsHelp.hidden) {
      const descriptions = {
        text: "Texto curto em uma linha. Prefixo e sufixo podem complementar o valor sem serem gravados no campo.",
        textarea: "Texto longo redimensionável. A largura respeita as colunas ocupadas e a altura pode ser ampliada pelo prestador.",
        date: "Campo de data com validação nativa do navegador.",
        time: "Campo de horário com validação nativa do navegador.",
        number: "Campo numérico. Pode usar prefixo e sufixo, como R$ ou °C.",
        checkbox: "Opção Sim/Não exibida como checkbox.",
        select: "Lista fixa. Separe cada opção por vírgula.",
        "exclusive-checkboxes": "Cria checkboxes exclusivos na mesma linha. Separe as opções por vírgula. Use HIPOT.[hipot] ou HIPOT.[hipot; Pressão arterial]. O ponto e vírgula separa o nome técnico do placeholder. O complemento é habilitado somente quando HIPOT. estiver marcado e pode ser recuperado por {{ hipot }}.",
        "multiple-fields": "Cria vários campos na mesma área. Use Campo 1[campo_1], \"+\", [campo_2]. Itens entre aspas são textos fixos; campos sem texto antes dos colchetes não exibem título.",
        auxiliary: "Lista preenchida por tabela auxiliar. Escolha a coluna armazenada como valor e a coluna apresentada ao usuário.",
        "static-text": "Texto informativo com HTML seguro e variáveis. Use <left>...</left>, <center>...</center> ou <right>...</right> para alinhamento; *texto* para negrito, _texto_ para sublinhado e /texto/ para itálico.",
        "static-variable": "Valor informativo preenchido automaticamente por uma variável do paciente, atendimento, prestador, empresa ou documento.",
        line: "Linha visual para separar áreas do formulário visto pelo prestador.",
        image: "Imagem por URL ou arquivo. Defina largura, altura e se a proporção deve permanecer travada.",
      };
      fieldSettingsHelp.textContent = descriptions[selectedType] || "Configure o campo e sua posição na grade.";
    }
    requestAnimationFrame(syncScreenSettingsHeight);
  };
  const openFieldSettings = (field) => {
    settingsField = field;
    if (fieldSettingsHelp) fieldSettingsHelp.hidden = true;
    settingsInputs.forEach((input) => {
      const value = field[input.dataset.settingsProperty];
      if (input.type === "checkbox") input.checked = Boolean(value);
      else input.value = value ?? "";
    });
    if (imageFileInput) imageFileInput.value = "";
    syncHexColorControls(settingsModal);
    renderScreenBindingOptions(field.binding || "");
    updateVisibleFieldSettings();
    const title = settingsModal.querySelector("[data-field-settings-title]");
    if (title) {
      const noun = ["static-text", "static-variable", "line", "image"].includes(field.type) ? "elemento" : "campo";
      title.textContent = `Configuração do ${noun} (${field.id})`;
    }
    settingsModal.hidden = false;
    renderScreenVariablePalette();
    requestAnimationFrame(syncScreenSettingsHeight);
  };
  const closeFieldSettings = () => {
    if (fieldSettingsHelp) fieldSettingsHelp.hidden = true;
    settingsModal.hidden = true;
    if (screenVariablePalette) {
      screenVariablePalette.hidden = true;
      screenVariablePalette.style.height = "";
    }
    settingsField = null;
  };
  settingsModal?.querySelector("[data-field-settings-close]")?.addEventListener("click", closeFieldSettings);
  imageFileInput?.addEventListener("change", () => {
    const file = imageFileInput.files?.[0];
    if (!file || !settingsField) return;
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      const result = String(reader.result || "");
      settingsModal.querySelector('[data-settings-property="imageUrl"]').value = result;
      const image = new Image();
      image.addEventListener("load", () => {
        const widthInput = settingsModal.querySelector('[data-settings-property="imageWidth"]');
        const heightInput = settingsModal.querySelector('[data-settings-property="imageHeight"]');
        const maxWidth = 600;
        const scale = Math.min(1, maxWidth / image.naturalWidth);
        widthInput.value = String(Math.max(1, Math.round(image.naturalWidth * scale)));
        heightInput.value = String(Math.max(1, Math.round(image.naturalHeight * scale)));
        settingsField.imageAspectRatio = image.naturalWidth / image.naturalHeight;
      });
      image.src = result;
    });
    reader.readAsDataURL(file);
  });
  settingsModal?.querySelector('[data-settings-property="type"]')?.addEventListener("change", updateVisibleFieldSettings);
  screenVariableSearch?.addEventListener("input", () => {
    const term = screenVariableSearch.value.trim().toLocaleLowerCase("pt-BR");
    screenVariableList?.querySelectorAll("button").forEach((button) => {
      button.hidden = Boolean(term) && !button.textContent.toLocaleLowerCase("pt-BR").includes(term);
    });
  });
  screenContentInput?.addEventListener("dragover", (event) => {
    if (event.dataTransfer.types.includes("text/document-variable")) event.preventDefault();
  });
  screenContentInput?.addEventListener("drop", (event) => {
    const variable = event.dataTransfer.getData("text/document-variable");
    if (!variable) return;
    event.preventDefault();
    insertScreenVariable(variable);
  });
  settingsModal?.querySelector("[data-field-settings-help-toggle]")?.addEventListener("click", () => {
    fieldSettingsHelp.hidden = !fieldSettingsHelp.hidden;
    updateVisibleFieldSettings();
  });
  const imageWidthInput = settingsModal?.querySelector('[data-settings-property="imageWidth"]');
  const imageHeightInput = settingsModal?.querySelector('[data-settings-property="imageHeight"]');
  imageWidthInput?.addEventListener("input", () => {
    if (!settingsModal.querySelector('[data-settings-property="lockAspectRatio"]')?.checked) return;
    const ratio = settingsField?.imageAspectRatio || (Number(imageWidthInput.value) / Number(imageHeightInput.value || 1)) || 1;
    imageHeightInput.value = String(Math.max(1, Math.round(Number(imageWidthInput.value || 1) / ratio)));
  });
  imageHeightInput?.addEventListener("input", () => {
    if (!settingsModal.querySelector('[data-settings-property="lockAspectRatio"]')?.checked) return;
    const ratio = settingsField?.imageAspectRatio || (Number(imageWidthInput.value || 1) / Number(imageHeightInput.value)) || 1;
    imageWidthInput.value = String(Math.max(1, Math.round(Number(imageHeightInput.value || 1) * ratio)));
  });
  settingsModal?.querySelector("[data-field-settings-save]")?.addEventListener("click", () => {
    if (!settingsField) return;
    const updates = {};
    settingsInputs.forEach((input) => {
      const property = input.dataset.settingsProperty;
      let value = input.type === "checkbox" ? input.checked : input.value;
      if (property === "name") value = normalizeName(value);
      if (["colSpan", "rowSpan", "imageWidth", "imageHeight", "lineWidth"].includes(property)) value = Math.max(1, Number(value || 1));
      if (["marginTop", "marginBottom"].includes(property)) value = Math.max(0, Number(value || 0));
      updates[property] = value;
    });
    updates.fontSize = Math.max(7, Math.min(72, Number(updates.fontSize || gridConfig.fontSize)));
    updates.fontFamily = updates.fontFamily || gridConfig.fontFamily;
    updates.fontSizeCustom = updates.fontSize !== gridConfig.fontSize;
    updates.fontFamilyCustom = updates.fontFamily !== gridConfig.fontFamily;
    updates.colSpan = Math.min(updates.colSpan, gridConfig.columns - settingsField.col + 1);
    updates.rowSpan = Math.min(updates.rowSpan, gridConfig.rows - settingsField.row + 1);
    const candidate = { ...settingsField, ...updates };
    const spanInput = settingsModal.querySelector('[data-settings-property="colSpan"]');
    spanInput?.setCustomValidity("");
    if (formFields.some((other) => other.id !== settingsField.id && fieldsOverlap(candidate, other))) {
      spanInput?.setCustomValidity("O tamanho informado ocupa células que já pertencem a outro campo.");
      spanInput?.reportValidity();
      return;
    }
    Object.assign(settingsField, updates);
    if (settingsField.type === "image" && settingsField.imageHeight) {
      settingsField.imageAspectRatio = settingsField.imageWidth / settingsField.imageHeight;
    }
    closeFieldSettings();
    markEditorDirty();
    renderFieldBuilder();
  });

  const updateGridInputs = () => {
    const columns = builder?.querySelector("[data-grid-columns]");
    const rows = builder?.querySelector("[data-grid-rows]");
    const fontSize = builder?.querySelector("[data-grid-font-size]");
    const fontFamily = builder?.querySelector("[data-grid-font-family]");
    if (columns) columns.value = String(gridConfig.columns);
    if (rows) rows.value = String(gridConfig.rows);
    if (fontSize) fontSize.value = String(gridConfig.fontSize);
    if (fontFamily) fontFamily.value = gridConfig.fontFamily;
  };
  const insertGridRow = (atRow) => {
    if (gridConfig.rows >= 30) return;
    gridConfig.rows += 1;
    formFields.forEach((field) => {
      if (field.row >= atRow) field.row += 1;
    });
    updateGridInputs();
    markEditorDirty();
    renderFieldBuilder();
  };
  const insertGridColumn = (atColumn) => {
    if (gridConfig.columns >= 12) return;
    gridConfig.columns += 1;
    formFields.forEach((field) => {
      const lastColumn = field.col + field.colSpan - 1;
      if (field.col < atColumn && atColumn <= lastColumn) field.colSpan += 1;
      else if (field.col >= atColumn) field.col += 1;
    });
    updateGridInputs();
    markEditorDirty();
    renderFieldBuilder();
  };
  const cellIsOccupied = (row, col) => formFields.some((field) => (
    row >= field.row
    && row < field.row + field.rowSpan
    && col >= field.col
    && col < field.col + field.colSpan
  ));
  const freeFormColumnSpan = (row, col) => {
    let span = 0;
    while (col + span <= gridConfig.columns && !cellIsOccupied(row, col + span)) {
      span += 1;
    }
    return Math.max(1, span);
  };
  const addReusableAt = (reusableId, row, col) => {
    const reusable = reusableFields.find((item) => String(item.cd_modelo_documento) === String(reusableId));
    const reusableSchema = reusable?.ds_projeto_tela?.formFields || [];
    const minimumRow = Math.min(...reusableSchema.map((field) => Number(field.row || 1)), 1);
    const minimumCol = Math.min(...reusableSchema.map((field) => Number(field.col || 1)), 1);
    reusableSchema.forEach((field, index) => {
      const targetRow = row + Number(field.row || 1) - minimumRow;
      const targetCol = col + Number(field.col || 1) - minimumCol;
      gridConfig.rows = Math.min(30, Math.max(gridConfig.rows, targetRow + Number(field.rowSpan || 1) - 1));
      gridConfig.columns = Math.min(12, Math.max(gridConfig.columns, targetCol + Number(field.colSpan || 1) - 1));
      addField({
        ...field,
        id: crypto.randomUUID?.() || `field-${Date.now()}-${Math.random()}`,
        reusableId: reusable.cd_modelo_documento,
        ...(cellIsOccupied(targetRow, targetCol) && index > 0 ? firstFreePosition() : { row: targetRow, col: targetCol }),
      });
    });
  };
  const addCustomVariableAt = (reusableId, scope, row, col) => {
    const reusable = reusableFields.find((item) => String(item.cd_modelo_documento) === String(reusableId));
    const configuration = reusable?.ds_projeto_tela?.customVariable || {};
    const variableName = normalizeName(configuration.name || reusable?.nm_modelo || "variavel");
    if (scope === "print") {
      addPrintElement("variable", { row, col });
      const element = printLayout.elements.at(-1);
      element.label = reusable?.nm_modelo || variableName;
      element.sourceField = `variavel.${variableName}`;
    } else {
      addField({
        row,
        col,
        label: reusable?.nm_modelo || variableName,
        name: variableName,
        binding: `variavel.${variableName}`,
        readonly: true,
      });
    }
  };
  const gridContextMenu = document.querySelector("[data-grid-context-menu]");
  const gridDeleteModal = document.querySelector("[data-grid-delete-modal]");
  const gridDeleteTitle = gridDeleteModal?.querySelector("[data-grid-delete-title]");
  const gridDeleteMessage = gridDeleteModal?.querySelector("[data-grid-delete-message]");
  let pendingGridDelete = null;
  let gridContextPosition = null;
  let pendingDuplicate = null;
  let duplicateGhost = null;
  const cancelPendingDuplicate = () => {
    pendingDuplicate = null;
    duplicateGhost?.remove();
    duplicateGhost = null;
  };
  const duplicateFitsAt = (scope, duplicate, row, col) => {
    const { grid, elements } = gridState(scope);
    const candidate = { ...duplicate, row, col };
    return row >= 1
      && col >= 1
      && row + duplicate.rowSpan - 1 <= grid.rows
      && col + duplicate.colSpan - 1 <= grid.columns
      && !elements.some((element) => fieldsOverlap(candidate, element));
  };
  const startPendingDuplicate = (scope, elementId, clientX, clientY) => {
    const source = gridState(scope).elements.find((element) => element.id === elementId);
    if (!source) return;
    cancelPendingDuplicate();
    const duplicate = structuredClone(source);
    duplicate.id = crypto.randomUUID?.() || `duplicate-${Date.now()}`;
    if (scope === "form") duplicate.name = normalizeName(`${source.name || "campo"}_copia_${Date.now()}`);
    pendingDuplicate = { scope, duplicate };
    duplicateGhost = document.createElement("div");
    duplicateGhost.className = "document-duplicate-ghost";
    duplicateGhost.textContent = `Posicione a cópia de ${source.label || source.name || "elemento"}`;
    duplicateGhost.style.left = `${clientX + 12}px`;
    duplicateGhost.style.top = `${clientY + 12}px`;
    document.body.appendChild(duplicateGhost);
    showHistoryIndicator("Clique em uma área livre para posicionar a cópia");
  };
  const positionMenuInViewport = (menu, event, offset = 4) => {
    if (!menu || !event) return;
    menu.hidden = false;
    menu.style.position = "fixed";
    menu.style.visibility = "hidden";
    menu.style.left = "0";
    menu.style.top = "0";
    const rect = menu.getBoundingClientRect();
    const padding = 8;
    const left = Math.max(
      padding,
      Math.min(event.clientX + offset, window.innerWidth - rect.width - padding),
    );
    const top = Math.max(
      padding,
      Math.min(event.clientY + offset, window.innerHeight - rect.height - padding),
    );
    menu.style.left = `${left}px`;
    menu.style.top = `${top}px`;
    menu.style.visibility = "visible";
  };
  const fieldTouchesTrack = (field, kind, index) => (
    kind === "row"
      ? index >= field.row && index < field.row + field.rowSpan
      : index >= field.col && index < field.col + field.colSpan
  );
  const fieldsOverlap = (first, second) => !(
    first.row + first.rowSpan <= second.row
    || second.row + second.rowSpan <= first.row
    || first.col + first.colSpan <= second.col
    || second.col + second.colSpan <= first.col
  );
  const gridState = (scope) => (
    scope === "print"
      ? { grid: printLayout.grid, elements: printLayout.elements, maxRows: 60 }
      : { grid: gridConfig, elements: formFields, maxRows: 30 }
  );
  const renderGridScope = (scope) => {
    if (scope === "print") renderPrintBuilder();
    else {
      updateGridInputs();
      renderFieldBuilder();
    }
  };
  const placeElementsWithoutOverlap = (grid, elements, maxRows) => {
    const placed = [];
    elements.forEach((element) => {
      element.colSpan = Math.max(1, Math.min(element.colSpan, grid.columns));
      element.rowSpan = Math.max(1, Math.min(element.rowSpan, grid.rows));
      element.col = Math.max(1, Math.min(element.col, grid.columns - element.colSpan + 1));
      element.row = Math.max(1, Math.min(element.row, grid.rows - element.rowSpan + 1));
      const fits = (row, col) => {
        const candidate = { ...element, row, col };
        return row + element.rowSpan - 1 <= grid.rows
          && col + element.colSpan - 1 <= grid.columns
          && !placed.some((other) => fieldsOverlap(candidate, other));
      };
      if (!fits(element.row, element.col)) {
        let position = null;
        for (let row = 1; row <= grid.rows && !position; row += 1) {
          for (let col = 1; col <= grid.columns; col += 1) {
            if (fits(row, col)) {
              position = { row, col };
              break;
            }
          }
        }
        if (!position && grid.rows < maxRows) {
          grid.rows += 1;
          position = { row: grid.rows, col: 1 };
        }
        if (position) Object.assign(element, position);
      }
      placed.push(element);
    });
  };
  const moveElementArea = (scope, elementId, row, col) => {
    const { grid, elements } = gridState(scope);
    const element = elements.find((item) => item.id === elementId);
    if (!element) return false;
    const destination = { ...element, row, col };
    if (
      row < 1
      || col < 1
      || row + element.rowSpan - 1 > grid.rows
      || col + element.colSpan - 1 > grid.columns
    ) return false;
    const displaced = elements.filter((item) => item.id !== element.id && fieldsOverlap(destination, item));
    if (displaced.some((item) => (
      item.row < row
      || item.col < col
      || item.row + item.rowSpan > row + element.rowSpan
      || item.col + item.colSpan > col + element.colSpan
    ))) return false;
    const rowOffset = element.row - row;
    const colOffset = element.col - col;
    const replacements = displaced.map((item) => ({
      item,
      row: item.row + rowOffset,
      col: item.col + colOffset,
    }));
    const stationary = elements.filter((item) => item.id !== element.id && !displaced.includes(item));
    if (replacements.some(({ item, row: nextRow, col: nextCol }) => {
      const candidate = { ...item, row: nextRow, col: nextCol };
      return nextRow < 1
        || nextCol < 1
        || nextRow + item.rowSpan - 1 > grid.rows
        || nextCol + item.colSpan - 1 > grid.columns
        || stationary.some((other) => fieldsOverlap(candidate, other));
    })) return false;
    replacements.forEach(({ item, row: nextRow, col: nextCol }) => {
      item.row = nextRow;
      item.col = nextCol;
    });
    element.row = row;
    element.col = col;
    return true;
  };
  const remapTrackIndex = (index, from, to) => {
    if (index === from) return to;
    if (from < to && index > from && index <= to) return index - 1;
    if (from > to && index >= to && index < from) return index + 1;
    return index;
  };
  const reorderGridTrack = (scope, kind, from, to) => {
    if (from === to) return;
    const { elements } = gridState(scope);
    const property = kind === "row" ? "row" : "col";
    const previous = elements.map((element) => ({ element, value: element[property] }));
    elements.forEach((element) => {
      element[property] = remapTrackIndex(element[property], from, to);
    });
    const hasOverlap = elements.some((element, index) => (
      elements.slice(index + 1).some((other) => fieldsOverlap(element, other))
    ));
    if (hasOverlap) {
      previous.forEach(({ element, value }) => { element[property] = value; });
      return;
    }
    markEditorDirty();
    renderGridScope(scope);
  };
  const handleGridDrop = (event, scope, row, col) => {
    const reusableId = event.dataTransfer.getData("text/document-library-reusable");
    const reusableType = event.dataTransfer.getData("text/document-library-element-type");
    if (reusableId) {
      if (reusableType === "VARIAVEL") addCustomVariableAt(reusableId, scope, row, col);
      else if (scope === "form") addReusableAt(reusableId, row, col);
      else {
        const reusable = reusableFields.find((item) => String(item.cd_modelo_documento) === String(reusableId));
        const elements = reusable?.ds_projeto_impressao?.printLayout?.elements || [];
        const minimumRow = Math.min(...elements.map((element) => Number(element.row || 1)), 1);
        const minimumCol = Math.min(...elements.map((element) => Number(element.col || 1)), 1);
        elements.forEach((element) => {
          const targetRow = row + Number(element.row || 1) - minimumRow;
          const targetCol = col + Number(element.col || 1) - minimumCol;
          printLayout.grid.rows = Math.min(60, Math.max(
            printLayout.grid.rows,
            targetRow + Number(element.rowSpan || 1) - 1,
          ));
          printLayout.grid.columns = Math.min(12, Math.max(
            printLayout.grid.columns,
            targetCol + Number(element.colSpan || 1) - 1,
          ));
          printLayout.elements.push({
            ...element,
            id: crypto.randomUUID?.() || `print-${Date.now()}-${Math.random()}`,
            row: targetRow,
            col: targetCol,
          });
        });
        renderPrintBuilder();
      }
      markEditorDirty();
      return true;
    }
    const trackKind = event.dataTransfer.getData("text/document-grid-track");
    const trackScope = event.dataTransfer.getData("text/document-grid-scope");
    if (trackKind && trackScope === scope) {
      const from = Number(event.dataTransfer.getData("text/document-grid-index"));
      reorderGridTrack(scope, trackKind, from, trackKind === "row" ? row : col);
      return true;
    }
    const mime = scope === "print" ? "text/print-element" : "text/document-field";
    const elementId = event.dataTransfer.getData(mime);
    const rowOffset = Math.max(0, Number(event.dataTransfer.getData("text/document-drag-row-offset") || 0));
    const colOffset = Math.max(0, Number(event.dataTransfer.getData("text/document-drag-col-offset") || 0));
    if (!elementId || !moveElementArea(scope, elementId, row - rowOffset, col - colOffset)) return false;
    markEditorDirty();
    renderGridScope(scope);
    return true;
  };
  const gridPositionFromPointer = (container, event, fallbackRow, fallbackCol) => {
    const cell = [...container.querySelectorAll(".document-grid-cell")].find((candidate) => {
      const rect = candidate.getBoundingClientRect();
      return event.clientX >= rect.left
        && event.clientX <= rect.right
        && event.clientY >= rect.top
        && event.clientY <= rect.bottom;
    });
    return {
      row: Number(cell?.dataset.gridRow || fallbackRow),
      col: Number(cell?.dataset.gridCol || fallbackCol),
    };
  };
  const expandedFieldCandidate = (field, direction) => {
    const candidate = { ...field };
    if (direction === "left") {
      candidate.col -= 1;
      candidate.colSpan += 1;
    } else if (direction === "right") {
      candidate.colSpan += 1;
    } else if (direction === "top") {
      candidate.row -= 1;
      candidate.rowSpan += 1;
    } else {
      candidate.rowSpan += 1;
    }
    return candidate;
  };
  const canExpandField = (field, direction) => {
    const atBoundary = (
      (direction === "left" && field.col === 1)
      || (direction === "right" && field.col + field.colSpan - 1 === gridConfig.columns)
      || (direction === "top" && field.row === 1)
      || (direction === "bottom" && field.row + field.rowSpan - 1 === gridConfig.rows)
    );
    if (atBoundary) {
      return ["left", "right"].includes(direction) ? gridConfig.columns < 12 : gridConfig.rows < 30;
    }
    const candidate = expandedFieldCandidate(field, direction);
    return !formFields.some((other) => other.id !== field.id && fieldsOverlap(candidate, other));
  };
  const expandField = (field, direction) => {
    if (!canExpandField(field, direction)) return;
    if (direction === "left" && field.col === 1) {
      gridConfig.columns += 1;
      formFields.forEach((item) => { item.col += 1; });
      field.col = 1;
      field.colSpan += 1;
    } else if (direction === "right" && field.col + field.colSpan - 1 === gridConfig.columns) {
      gridConfig.columns += 1;
      field.colSpan += 1;
    } else if (direction === "top" && field.row === 1) {
      gridConfig.rows += 1;
      formFields.forEach((item) => { item.row += 1; });
      field.row = 1;
      field.rowSpan += 1;
    } else if (direction === "bottom" && field.row + field.rowSpan - 1 === gridConfig.rows) {
      gridConfig.rows += 1;
      field.rowSpan += 1;
    } else {
      Object.assign(field, expandedFieldCandidate(field, direction));
    }
    updateGridInputs();
    markEditorDirty();
    renderFieldBuilder();
  };
  const shrinkField = (field, direction) => {
    if (["left", "right"].includes(direction) && field.colSpan <= 1) return;
    if (["top", "bottom"].includes(direction) && field.rowSpan <= 1) return;
    if (direction === "left") {
      field.col += 1;
      field.colSpan -= 1;
    } else if (direction === "right") {
      field.colSpan -= 1;
    } else if (direction === "top") {
      field.row += 1;
      field.rowSpan -= 1;
    } else {
      field.rowSpan -= 1;
    }
    markEditorDirty();
    renderFieldBuilder();
  };
  const reflowGridFields = () => placeElementsWithoutOverlap(gridConfig, formFields, 30);
  const deleteGridTrack = (scope, kind, index, mode) => {
    const state = gridState(scope);
    if (mode === "delete-fields") {
      const retained = state.elements.filter((element) => !fieldTouchesTrack(element, kind, index));
      if (scope === "print") printLayout.elements = retained;
      else formFields = retained;
      state.elements = retained;
    }
    const sizeProperty = kind === "row" ? "rows" : "columns";
    const positionProperty = kind === "row" ? "row" : "col";
    const spanProperty = kind === "row" ? "rowSpan" : "colSpan";
    state.grid[sizeProperty] = Math.max(1, state.grid[sizeProperty] - 1);
    state.elements.forEach((element) => {
      if (element[positionProperty] > index) element[positionProperty] -= 1;
      else if (
        element[positionProperty] <= index
        && element[positionProperty] + element[spanProperty] - 1 >= index
        && element[spanProperty] > 1
      ) element[spanProperty] -= 1;
      else if (element[positionProperty] === index) {
        element[positionProperty] = Math.min(index, state.grid[sizeProperty]);
      }
    });
  };
  const applyGridDelete = (mode) => {
    if (!pendingGridDelete) return;
    const { kind, index, scope, targetSize } = pendingGridDelete;
    if (targetSize) {
      const state = gridState(scope);
      const sizeProperty = kind === "row" ? "rows" : "columns";
      while (state.grid[sizeProperty] > targetSize) {
        deleteGridTrack(scope, kind, state.grid[sizeProperty], mode);
      }
    } else {
      deleteGridTrack(scope, kind, index, mode);
    }
    if (mode === "adjust") {
      const state = gridState(scope);
      placeElementsWithoutOverlap(state.grid, state.elements, state.maxRows);
    }
    pendingGridDelete = null;
    if (gridDeleteModal) gridDeleteModal.hidden = true;
    markEditorDirty();
    renderGridScope(scope);
  };
  const requestGridDelete = (kind, index, scope = "form") => {
    const grid = scope === "print" ? printLayout.grid : gridConfig;
    const elements = scope === "print" ? printLayout.elements : formFields;
    if ((kind === "row" && grid.rows <= 1) || (kind === "column" && grid.columns <= 1)) return;
    pendingGridDelete = { kind, index, scope };
    const affected = elements.filter((field) => fieldTouchesTrack(field, kind, index));
    if (!affected.length) {
      applyGridDelete("adjust");
      return;
    }
    const label = kind === "row" ? "linha" : "coluna";
    gridDeleteTitle.textContent = `Excluir ${label}`;
    gridDeleteMessage.textContent = `${affected.length} campo(s) ocupam esta ${label}. Exclua-os ou reajuste-os na grade restante.`;
    gridDeleteModal.hidden = false;
  };
  const requestGridResize = (kind, targetSize, scope = "form") => {
    const state = gridState(scope);
    const sizeProperty = kind === "row" ? "rows" : "columns";
    const currentSize = state.grid[sizeProperty];
    if (targetSize >= currentSize) {
      state.grid[sizeProperty] = targetSize;
      markEditorDirty();
      renderGridScope(scope);
      return;
    }
    const affected = state.elements.filter((element) => (
      Array.from({ length: currentSize - targetSize }, (_, offset) => currentSize - offset)
        .some((index) => fieldTouchesTrack(element, kind, index))
    ));
    pendingGridDelete = { kind, index: currentSize, scope, targetSize };
    if (!affected.length) {
      applyGridDelete("adjust");
      return;
    }
    const label = kind === "row" ? "linhas" : "colunas";
    gridDeleteTitle.textContent = `Reduzir ${label}`;
    gridDeleteMessage.textContent = `${affected.length} campo(s) ocupam as ${label} finais que serão removidas. Exclua-os ou reajuste-os na grade restante.`;
    gridDeleteModal.hidden = false;
  };
  const openGridContextMenu = (event, row, col, scope = "form", elementId = "") => {
    event.preventDefault();
    event.stopPropagation();
    gridContextMenu.querySelectorAll(".document-context-submenu.open").forEach((submenu) => submenu.classList.remove("open"));
    gridContextPosition = { row, col, scope, elementId };
    const removeButton = gridContextMenu.querySelector("[data-grid-remove-element]");
    const duplicateButton = gridContextMenu.querySelector("[data-grid-duplicate-element]");
    if (removeButton) removeButton.hidden = !elementId;
    if (duplicateButton) duplicateButton.hidden = !elementId;
    positionMenuInViewport(gridContextMenu, event);
  };
  gridContextMenu?.querySelectorAll(".document-context-submenu").forEach((submenu) => {
    const trigger = submenu.querySelector(":scope > button");
    const panel = submenu.querySelector(":scope > div");
    if (!trigger || !panel) return;
    submenu.addEventListener("pointerenter", () => {
      submenu.parentElement?.querySelectorAll(":scope > .document-context-submenu.open").forEach((other) => {
        if (other !== submenu) other.classList.remove("open");
      });
      submenu.classList.add("open");
      panel.style.visibility = "hidden";
      panel.style.display = "block";
      const triggerRect = trigger.getBoundingClientRect();
      const panelRect = panel.getBoundingClientRect();
      const padding = 8;
      const fitsRight = triggerRect.right + panelRect.width + padding <= window.innerWidth;
      panel.style.left = `${Math.max(padding, fitsRight ? triggerRect.right + 2 : triggerRect.left - panelRect.width - 2)}px`;
      panel.style.top = `${Math.max(padding, Math.min(triggerRect.top, window.innerHeight - panelRect.height - padding))}px`;
      panel.style.visibility = "visible";
    });
    submenu.addEventListener("pointerleave", () => {
      submenu.classList.remove("open");
      panel.style.removeProperty("display");
      panel.style.removeProperty("visibility");
    });
  });
  gridContextMenu?.addEventListener("click", (event) => {
    if (event.target.closest("[data-grid-duplicate-element]") && gridContextPosition?.elementId) {
      startPendingDuplicate(
        gridContextPosition.scope,
        gridContextPosition.elementId,
        event.clientX,
        event.clientY,
      );
      gridContextMenu.hidden = true;
      return;
    }
    if (event.target.closest("[data-grid-remove-element]") && gridContextPosition?.elementId) {
      if (gridContextPosition.scope === "print") {
        printLayout.elements = printLayout.elements.filter((element) => element.id !== gridContextPosition.elementId);
        renderPrintBuilder();
      } else {
        formFields = formFields.filter((field) => field.id !== gridContextPosition.elementId);
        renderFieldBuilder();
      }
      markEditorDirty();
      gridContextMenu.hidden = true;
      return;
    }
    const insertDirection = event.target.closest("[data-grid-insert-row]")?.dataset.gridInsertRow;
    if (insertDirection && gridContextPosition) {
      const contextState = gridState(gridContextPosition.scope);
      const contextElement = contextState.elements.find((item) => item.id === gridContextPosition.elementId);
      const contextStart = contextElement?.row || gridContextPosition.row;
      const contextEnd = contextElement
        ? contextElement.row + contextElement.rowSpan
        : gridContextPosition.row + 1;
      const row = insertDirection === "after" ? contextEnd : contextStart;
      if (gridContextPosition.scope === "print") insertPrintRow(row);
      else insertGridRow(row);
      gridContextMenu.hidden = true;
      return;
    }
  const insertColumnDirection = event.target.closest("[data-grid-insert-column]")?.dataset.gridInsertColumn;
    if (insertColumnDirection && gridContextPosition) {
      const contextState = gridState(gridContextPosition.scope);
      const contextElement = contextState.elements.find((item) => item.id === gridContextPosition.elementId);
      const contextStart = contextElement?.col || gridContextPosition.col;
      const contextEnd = contextElement
        ? contextElement.col + contextElement.colSpan
        : gridContextPosition.col + 1;
      const column = insertColumnDirection === "after" ? contextEnd : contextStart;
      if (gridContextPosition.scope === "print") insertPrintColumn(column);
      else insertGridColumn(column);
      gridContextMenu.hidden = true;
      return;
    }
    const kind = event.target.closest("[data-grid-delete-kind]")?.dataset.gridDeleteKind;
    if (!kind || !gridContextPosition) return;
    gridContextMenu.hidden = true;
    requestGridDelete(
      kind,
      kind === "row" ? gridContextPosition.row : gridContextPosition.col,
      gridContextPosition.scope,
    );
  });
  gridDeleteModal?.querySelector("[data-grid-delete-cancel]")?.addEventListener("click", () => {
    const scope = pendingGridDelete?.scope;
    pendingGridDelete = null;
    gridDeleteModal.hidden = true;
    if (scope) renderGridScope(scope);
  });
  gridDeleteModal?.querySelector("[data-grid-delete-adjust]")?.addEventListener("click", () => applyGridDelete("adjust"));
  gridDeleteModal?.querySelector("[data-grid-delete-fields]")?.addEventListener("click", () => applyGridDelete("delete-fields"));
  document.addEventListener("pointermove", (event) => {
    if (!pendingDuplicate || !duplicateGhost) return;
    duplicateGhost.style.left = `${Math.min(window.innerWidth - duplicateGhost.offsetWidth - 8, event.clientX + 12)}px`;
    duplicateGhost.style.top = `${Math.min(window.innerHeight - duplicateGhost.offsetHeight - 8, event.clientY + 12)}px`;
    const container = event.target.closest?.(".document-position-grid");
    const expectedContainer = pendingDuplicate.scope === "print" ? printElementList : fieldList;
    if (!container || container !== expectedContainer) {
      duplicateGhost.classList.add("invalid");
      return;
    }
    const position = gridPositionFromPointer(container, event, 1, 1);
    duplicateGhost.classList.toggle(
      "invalid",
      !duplicateFitsAt(pendingDuplicate.scope, pendingDuplicate.duplicate, position.row, position.col),
    );
  });
  document.addEventListener("click", (event) => {
    if (!pendingDuplicate) return;
    const container = event.target.closest?.(".document-position-grid");
    const expectedContainer = pendingDuplicate.scope === "print" ? printElementList : fieldList;
    if (!container || container !== expectedContainer) return;
    event.preventDefault();
    event.stopPropagation();
    const position = gridPositionFromPointer(container, event, 1, 1);
    if (!duplicateFitsAt(pendingDuplicate.scope, pendingDuplicate.duplicate, position.row, position.col)) {
      duplicateGhost?.classList.add("invalid");
      showHistoryIndicator("A cópia não cabe nessa posição");
      return;
    }
    const { elements } = gridState(pendingDuplicate.scope);
    Object.assign(pendingDuplicate.duplicate, position);
    elements.push(pendingDuplicate.duplicate);
    const scope = pendingDuplicate.scope;
    cancelPendingDuplicate();
    markEditorDirty();
    renderGridScope(scope);
    showHistoryIndicator("Elemento duplicado");
  }, true);
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !pendingDuplicate) return;
    cancelPendingDuplicate();
    showHistoryIndicator("Duplicação cancelada");
  });

  const closeVisibleCellMenu = (menu) => {
    if (!menu) return;
    menu.hidden = true;
    menu.style.removeProperty("position");
    menu.style.removeProperty("z-index");
    menu.style.removeProperty("visibility");
    menu.style.removeProperty("left");
    menu.style.removeProperty("right");
    menu.style.removeProperty("top");
    if (menu._cellMenuOwner?.isConnected) menu._cellMenuOwner.appendChild(menu);
    delete menu.dataset.cellMenuPortal;
  };
  const closeAllVisibleCellMenus = () => {
    document.querySelectorAll("[data-cell-menu-portal]").forEach(closeVisibleCellMenu);
  };
  const openVisibleCellMenu = (menu, event, scope) => {
    if (!menu || !event) return;
    closeAllVisibleCellMenus();
    menu._cellMenuOwner = menu.parentElement;
    menu.dataset.cellMenuPortal = scope;
    document.body.appendChild(menu);
    menu.hidden = false;
    menu.style.position = "fixed";
    menu.style.zIndex = "480";
    menu.style.visibility = "hidden";
    const menuRect = menu.getBoundingClientRect();
    const viewportPadding = 8;
    let left = event.clientX + 6;
    let top = event.clientY + 6;
    if (left + menuRect.width > window.innerWidth - viewportPadding) {
      left = event.clientX - menuRect.width - 6;
    }
    if (left < viewportPadding) left = viewportPadding;
    if (top + menuRect.height > window.innerHeight - viewportPadding) {
      top = event.clientY - menuRect.height - 6;
    }
    if (top < viewportPadding) {
      top = Math.max(viewportPadding, window.innerHeight - menuRect.height - viewportPadding);
    }
    menu.style.left = `${left}px`;
    menu.style.right = "auto";
    menu.style.top = `${top}px`;
    menu.style.visibility = "visible";
  };

  const renderFieldBuilder = () => {
    document.querySelectorAll('[data-cell-menu-portal="form"]').forEach((menu) => menu.remove());
    fieldList.innerHTML = "";
    fieldList.style.gridTemplateColumns = `repeat(${gridConfig.columns}, minmax(110px, 1fr))`;
    fieldList.style.gridTemplateRows = `repeat(${gridConfig.rows}, minmax(92px, auto))`;
    for (let row = 1; row <= gridConfig.rows; row += 1) {
      for (let col = 1; col <= gridConfig.columns; col += 1) {
        const cell = document.createElement("div");
        cell.className = "document-grid-cell";
        cell.style.gridColumn = String(col);
        cell.style.gridRow = String(row);
        cell.dataset.gridCol = String(col);
        cell.dataset.gridRow = String(row);
        const reusableOptions = reusableFields.filter((item) => item.ds_projeto_tela?.formFields?.length).map((item) => (
          `<button type="button" data-cell-create-reusable="${item.cd_modelo_documento}">${escapeHtml(item.nm_modelo)}</button>`
        )).join("");
        cell.innerHTML = cellIsOccupied(row, col) ? "" : `
          <div class="document-cell-actions">
            <button class="cell-direction cell-direction-top" type="button" data-cell-row-before title="↑ Adicionar linha acima">+</button>
            <button class="cell-direction cell-direction-bottom" type="button" data-cell-row-after title="↓ Adicionar linha abaixo">+</button>
            <button class="cell-direction cell-direction-left" type="button" data-cell-column-before title="← Adicionar coluna à esquerda">+</button>
            <button class="cell-direction cell-direction-right" type="button" data-cell-column-after title="Adicionar coluna à direita →">+</button>
            <div class="document-cell-create">
              <button type="button" data-cell-create-toggle title="Adicionar elemento"><span>+ Campo</span></button>
              <button type="button" data-cell-create-toggle aria-label="Outros elementos">▾</button>
              <div class="document-cell-create-menu" data-cell-create-menu hidden>
                <button type="button" data-cell-create-field>Campo</button>
                <button type="button" data-cell-create-display="static-text">Texto</button>
                <button type="button" data-cell-create-display="static-variable">Variável</button>
                <button type="button" data-cell-create-display="line">Linha</button>
                <button type="button" data-cell-create-image>Imagem</button>
                ${reusableOptions ? `
                  <button class="document-cell-fields-toggle" type="button" data-form-fields-toggle>Campos reutilizáveis <span>›</span></button>
                  <div class="document-cell-fields-menu" data-form-fields-menu hidden>${reusableOptions}</div>
                ` : ""}
              </div>
            </div>
          </div>
        `;
        const formCreateMenu = cell.querySelector("[data-cell-create-menu]");
        const formFieldsMenu = cell.querySelector("[data-form-fields-menu]");
        formCreateMenu?.addEventListener("click", (event) => {
          const action = event.target.closest("button");
          if (!action) return;
          event.preventDefault();
          event.stopPropagation();
          if (action.matches("[data-cell-create-field]")) {
            addField({ row, col });
          } else if (action.matches("[data-cell-create-display]")) {
            const type = action.dataset.cellCreateDisplay;
            addField({
              name: `elemento_${formFields.length + 1}`,
              label: type === "static-text" ? "Texto" : (type === "static-variable" ? "Variável" : "Linha"),
              type,
              row,
              col,
              colSpan: type === "line" ? freeFormColumnSpan(row, col) : 1,
            });
          } else if (action.matches("[data-cell-create-image]")) {
            addField({
              name: `imagem_${formFields.length + 1}`,
              label: "Imagem",
              type: "image",
              row,
              col,
            });
          } else if (action.matches("[data-form-fields-toggle]")) {
            if (formFieldsMenu.hidden) openVisibleCellMenu(formFieldsMenu, event, "form");
            else closeVisibleCellMenu(formFieldsMenu);
          }
        });
        formFieldsMenu?.addEventListener("click", (event) => {
          const action = event.target.closest("[data-cell-create-reusable]");
          if (!action) return;
          event.preventDefault();
          event.stopPropagation();
          addReusableAt(action.dataset.cellCreateReusable, row, col);
        });
        if (col === 1) {
          cell.insertAdjacentHTML("beforeend", '<button class="document-track-handle document-row-handle" type="button" draggable="true" title="Arrastar linha" aria-label="Reordenar linha">⋮</button>');
        }
        if (row === 1 || row === gridConfig.rows) {
          const edgeClass = row === 1 ? "document-column-handle-top" : "document-column-handle-bottom";
          cell.insertAdjacentHTML("beforeend", `<button class="document-track-handle document-column-handle ${edgeClass}" type="button" draggable="true" title="Arrastar coluna" aria-label="Reordenar coluna">⋯</button>`);
        }
        cell.querySelectorAll(".document-track-handle").forEach((handle) => {
          handle.addEventListener("dragstart", (event) => {
            event.stopPropagation();
            const kind = handle.classList.contains("document-row-handle") ? "row" : "column";
            event.dataTransfer.setData("text/document-grid-track", kind);
            event.dataTransfer.setData("text/document-grid-scope", "form");
            event.dataTransfer.setData("text/document-grid-index", String(kind === "row" ? row : col));
            event.dataTransfer.effectAllowed = "move";
          });
        });
        cell.addEventListener("dragover", (event) => {
          event.preventDefault();
          cell.classList.add("drag-over");
        });
        cell.addEventListener("dragleave", () => cell.classList.remove("drag-over"));
        cell.addEventListener("contextmenu", (event) => openGridContextMenu(event, row, col));
        cell.addEventListener("drop", (event) => {
          event.preventDefault();
          cell.classList.remove("drag-over");
          handleGridDrop(event, "form", row, col);
        });
        cell.addEventListener("click", (event) => {
          const action = event.target.closest("button");
          if (!action) return;
          event.preventDefault();
          event.stopPropagation();
          if (action.matches("[data-cell-row-before]")) insertGridRow(row);
          else if (action.matches("[data-cell-row-after]")) insertGridRow(row + 1);
          else if (action.matches("[data-cell-column-before]")) insertGridColumn(col);
          else if (action.matches("[data-cell-column-after]")) insertGridColumn(col + 1);
          else if (action.matches("[data-cell-create-toggle]")) {
            if (formCreateMenu.hidden) openVisibleCellMenu(formCreateMenu, event, "form");
            else closeVisibleCellMenu(formCreateMenu);
          } else if (action.matches("[data-form-fields-toggle]")) {
            if (formFieldsMenu.hidden) openVisibleCellMenu(formFieldsMenu, event, "form");
            else closeVisibleCellMenu(formFieldsMenu);
          }
        });
        fieldList.appendChild(cell);
      }
    }
    formFields.forEach((field, index) => {
      const card = document.createElement("article");
      card.className = "document-form-field-card";
      card.draggable = true;
      card.style.gridColumn = `${field.col} / span ${Math.min(field.colSpan, gridConfig.columns - field.col + 1)}`;
      card.style.gridRow = `${field.row} / span ${Math.min(field.rowSpan, gridConfig.rows - field.row + 1)}`;
      card.dataset.fieldIndex = String(index);
      card.innerHTML = `
        <div class="document-field-expand-actions">
          ${canExpandField(field, "top") ? '<button class="field-expand-top" type="button" data-field-expand="top" title="Expandir campo para cima">⌃</button>' : ""}
          ${canExpandField(field, "bottom") ? '<button class="field-expand-bottom" type="button" data-field-expand="bottom" title="Expandir campo para baixo">⌄</button>' : ""}
          ${canExpandField(field, "left") ? '<button class="field-expand-left" type="button" data-field-expand="left" title="Expandir campo para a esquerda">‹</button>' : ""}
          ${canExpandField(field, "right") ? '<button class="field-expand-right" type="button" data-field-expand="right" title="Expandir campo para a direita">›</button>' : ""}
          ${field.rowSpan > 1 ? '<button class="field-shrink-top" type="button" data-field-shrink="top" title="Diminuir pela parte superior">⌄</button><button class="field-shrink-bottom" type="button" data-field-shrink="bottom" title="Diminuir pela parte inferior">⌃</button>' : ""}
          ${field.colSpan > 1 ? '<button class="field-shrink-left" type="button" data-field-shrink="left" title="Diminuir pela esquerda">›</button><button class="field-shrink-right" type="button" data-field-shrink="right" title="Diminuir pela direita">‹</button>' : ""}
        </div>
        <div class="document-field-card-heading">
          <span class="document-field-kind-icon" aria-hidden="true">${field.type === "image" ? "□" : (field.type === "line" ? "_" : (field.type === "static-variable" ? "V" : "T"))}</span>
          <strong>${escapeHtml(field.label || field.name)}</strong>
          ${field.readonly ? "<small>Somente leitura</small>" : ""}
        </div>
        <span>${escapeHtml(field.type === "image" ? `${field.imageWidth} × ${field.imageHeight}px` : (field.binding || field.sourceTable || field.type))}</span>
        <div class="document-field-card-actions">
          <button type="button" data-field-settings title="Configurar">⚙</button>
          <button type="button" data-field-remove title="Remover">×</button>
        </div>
      `;
      card.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/document-field", field.id);
        const rect = card.getBoundingClientRect();
        event.dataTransfer.setData("text/document-drag-col-offset", String(Math.min(
          field.colSpan - 1,
          Math.max(0, Math.floor(((event.clientX - rect.left) / Math.max(rect.width, 1)) * field.colSpan)),
        )));
        event.dataTransfer.setData("text/document-drag-row-offset", String(Math.min(
          field.rowSpan - 1,
          Math.max(0, Math.floor(((event.clientY - rect.top) / Math.max(rect.height, 1)) * field.rowSpan)),
        )));
        event.dataTransfer.effectAllowed = "move";
        card.classList.add("dragging");
      });
      card.addEventListener("dragend", () => card.classList.remove("dragging"));
      card.addEventListener("dragover", (event) => {
        event.preventDefault();
        card.classList.add("drag-over");
      });
      card.addEventListener("dragleave", () => card.classList.remove("drag-over"));
      card.addEventListener("drop", (event) => {
        event.preventDefault();
        event.stopPropagation();
        card.classList.remove("drag-over");
        const position = gridPositionFromPointer(fieldList, event, field.row, field.col);
        handleGridDrop(event, "form", position.row, position.col);
      });
      card.addEventListener("contextmenu", (event) => openGridContextMenu(event, field.row, field.col, "form", field.id));
      card.querySelectorAll("[data-field-expand]").forEach((button) => {
        button.addEventListener("click", () => expandField(field, button.dataset.fieldExpand));
      });
      card.querySelectorAll("[data-field-shrink]").forEach((button) => {
        button.addEventListener("click", () => shrinkField(field, button.dataset.fieldShrink));
      });
      card.querySelector("[data-field-settings]").addEventListener("click", () => openFieldSettings(field));
      card.querySelector("[data-field-remove]").addEventListener("click", () => {
        formFields.splice(index, 1);
        markEditorDirty();
        renderFieldBuilder();
      });
      fieldList.appendChild(card);
    });
    fieldEmpty.hidden = formFields.length > 0;
  };

  const buildScreenHtml = () => {
    const fields = [...formFields].sort((left, right) => (
      left.row - right.row || left.col - right.col || String(left.id).localeCompare(String(right.id))
    )).map((field) => {
      const name = normalizeName(field.name || field.label);
      const required = field.required ? " required" : "";
      const placeholder = field.placeholder ? ` placeholder="${escapeHtml(field.placeholder)}"` : "";
      const readonly = field.readonly ? ' disabled tabindex="-1" aria-disabled="true"' : "";
      const bindingValue = field.binding ? `{{ ${field.binding} }}` : "";
      const positionStyle = `grid-column:${field.col} / span ${field.colSpan};grid-row:${field.row} / span ${field.rowSpan}`;
      const fieldFontSize = Math.max(7, Number(field.fontSize || gridConfig.fontSize));
      const fieldFontFamily = escapeHtml(field.fontFamily || gridConfig.fontFamily);
      const fieldTextColor = escapeHtml(field.textColor || "#111111");
      const fieldStyle = `${positionStyle};--field-font-size:${fieldFontSize}px;font-size:${fieldFontSize + 1}px;font-family:${fieldFontFamily};color:${fieldTextColor}`;
      const position = `style="${fieldStyle}"`;
      const textStyle = `font-size:${fieldFontSize}px;font-family:${fieldFontFamily};color:${fieldTextColor}`;
      if (field.type === "static-text") {
        const content = formatRichText(field.content);
        const styledPosition = `style="${positionStyle};${textStyle}"`;
        if (field.displayStyle === "title") return `<h2 class="generated-screen-title" ${styledPosition}>${content}</h2>`;
        if (field.displayStyle === "help") return `<aside class="generated-screen-help" ${styledPosition}>${content}</aside>`;
        return `<div class="generated-screen-${field.displayStyle === "description" ? "description" : "text"}" ${styledPosition}>${content}</div>`;
      }
      if (field.type === "static-variable") {
        const label = String(field.label || "").trim();
        return `<div class="generated-screen-variable" style="${positionStyle};${textStyle}">${label ? `<strong>${escapeHtml(label)}:</strong> ` : ""}${escapeHtml(bindingValue)}</div>`;
      }
      if (field.type === "line") {
        const lineWidth = Math.max(field.lineStyle === "double" ? 3 : 1, Number(field.lineWidth || 1));
        return `<div class="generated-screen-line" style="${positionStyle};margin-top:${Number(field.marginTop || 0)}px;margin-bottom:${Number(field.marginBottom || 0)}px"><hr style="margin:0;border:0;border-top:${lineWidth}px ${escapeHtml(field.lineStyle)} ${escapeHtml(field.lineColor)}"></div>`;
      }
      if (field.type === "image") {
        return `<div class="generated-image-field" ${position}><img src="${escapeHtml(field.imageUrl)}" alt="${escapeHtml(field.label || "Imagem")}" style="width:${field.imageWidth}px;height:${field.imageHeight}px;object-fit:contain"></div>`;
      }
      if (field.type === "textarea") {
        return `<label ${position}>${escapeHtml(field.label)}<textarea data-document-field="true" name="campo_${name}" rows="5"${placeholder}${required}${readonly}>${escapeHtml(bindingValue)}</textarea></label>`;
      }
      if (field.type === "select") {
        const options = String(field.options || "").split(",").map((option) => option.trim()).filter(Boolean)
          .map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join("");
        return `<label ${position}>${escapeHtml(field.label)}<select data-document-field="true" name="campo_${name}"${required}${readonly}><option value=""></option>${options}</select></label>`;
      }
      if (field.type === "auxiliary") {
        const source = `data-option-source="auxiliary" data-source-table="${escapeHtml(field.sourceTable)}" data-source-value-field="${escapeHtml(field.sourceValueField || "cd_valor")}" data-source-display-field="${escapeHtml(field.sourceDisplayField || "ds_valor")}"`;
        return `<label ${position}>${escapeHtml(field.label)}<select data-document-field="true" name="campo_${name}" ${source}${required}${readonly}><option value=""></option></select></label>`;
      }
      if (field.type === "exclusive-checkboxes") {
        const choices = splitStructuredOptions(field.options)
          .map((option) => {
            const parsed = parseEmbeddedField(option);
            const label = parsed.label || option.replace(/\[.*$/, "").trim();
            const detailName = parsed.name && option.includes("[") ? parsed.name : "";
            const detailPlaceholder = parsed.placeholder || "";
            const detail = detailName
              ? `<input class="generated-exclusive-detail" data-document-field="true" data-exclusive-detail="${escapeHtml(label)}" name="campo_${escapeHtml(detailName)}" type="text" disabled tabindex="-1" placeholder="${escapeHtml(detailPlaceholder)}">`
              : "";
            return `<label class="generated-exclusive-option"><input data-document-field="true" data-exclusive-choice="campo_${escapeHtml(name)}" name="campo_${escapeHtml(name)}" type="checkbox" value="${escapeHtml(label)}"${readonly}><span>${escapeHtml(label)}</span>${detail}</label>`;
          }).join("");
        return `<fieldset class="generated-exclusive-checkboxes" style="${fieldStyle}" data-exclusive-group="campo_${escapeHtml(name)}" data-exclusive-required="${field.required ? "true" : "false"}" data-exclusive-readonly="${field.readonly ? "true" : "false"}"><legend>${escapeHtml(field.label)}</legend><div>${choices}</div></fieldset>`;
      }
      if (field.type === "multiple-fields") {
        const controls = splitStructuredOptions(field.options).map((option) => {
          const parsed = parseEmbeddedField(option);
          if (parsed.type === "literal") {
            return `<span class="generated-multiple-literal">${escapeHtml(parsed.text)}</span>`;
          }
          return `<label class="generated-multiple-item">${parsed.label ? `<span>${escapeHtml(parsed.label)}</span>` : ""}<input data-document-field="true" name="campo_${escapeHtml(parsed.name)}" type="text" placeholder="${escapeHtml(parsed.placeholder)}"${required}${readonly}></label>`;
        }).join("");
        return `<fieldset class="generated-multiple-fields" style="${fieldStyle}"><legend>${escapeHtml(field.label)}</legend><div>${controls}</div></fieldset>`;
      }
      if (field.type === "checkbox") {
        return `<fieldset class="generated-boolean-field" style="${fieldStyle}"><legend>${escapeHtml(field.label)}</legend><label class="provider-checkbox"><input data-document-field="true" name="campo_${name}" type="checkbox"${required}${readonly}><span>Sim</span></label></fieldset>`;
      }
      const control = `<input data-document-field="true" name="campo_${name}" type="${escapeHtml(field.type || "text")}" value="${escapeHtml(bindingValue)}"${placeholder}${required}${readonly}>`;
      if (["text", "number"].includes(field.type) && (field.prefix || field.suffix)) {
        return `<label ${position}>${escapeHtml(field.label)}<span class="generated-field-affix">${field.prefix ? `<span>${escapeHtml(field.prefix)}</span>` : ""}${control}${field.suffix ? `<span>${escapeHtml(field.suffix)}</span>` : ""}</span></label>`;
      }
      return `<label ${position}>${escapeHtml(field.label)}${control}</label>`;
    }).join("");
    return `<section class="generated-clinical-form" style="grid-template-columns:repeat(${gridConfig.columns},minmax(0,1fr));grid-template-rows:repeat(${gridConfig.rows},minmax(0,auto))">${fields}</section>`;
  };
  const buildPrintLayoutHtml = () => {
    const safeRichHtml = (value) => {
      const template = document.createElement("template");
      template.innerHTML = String(value || "")
        .replace(/<left>/gi, '<div style="text-align:left">')
        .replace(/<\/left>/gi, "</div>")
        .replace(/<center>/gi, '<div style="text-align:center">')
        .replace(/<\/center>/gi, "</div>")
        .replace(/<right>/gi, '<div style="text-align:right">')
        .replace(/<\/right>/gi, "</div>");
      template.content.querySelectorAll("script, iframe, object, embed, link, meta").forEach((element) => element.remove());
      template.content.querySelectorAll("*").forEach((element) => {
        [...element.attributes].forEach((attribute) => {
          if (attribute.name.toLowerCase().startsWith("on")) element.removeAttribute(attribute.name);
          if (["href", "src"].includes(attribute.name.toLowerCase()) && /^\s*javascript:/i.test(attribute.value)) {
            element.removeAttribute(attribute.name);
          }
        });
      });
      const textNodes = [];
      const walker = document.createTreeWalker(template.content, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) textNodes.push(walker.currentNode);
      textNodes.forEach((node) => {
        if (node.parentElement?.closest("pre, code")) return;
        const variables = [];
        const protectedText = String(node.textContent || "").replace(/{{\s*[^}]+\s*}}/g, (token) => {
          variables.push(token);
          return `\uE000${variables.length - 1}\uE001`;
        });
        const escaped = escapeHtml(protectedText);
        let formatted = escaped
          .replace(/\*([^*\n]+)\*/g, "<strong>$1</strong>")
          .replace(/_([^_\n]+)_/g, "<u>$1</u>")
          .replace(/(^|[\s(>])\/([^/\n]+)\/(?=$|[\s.,;!?<)])/g, "$1<em>$2</em>");
        variables.forEach((token, index) => {
          formatted = formatted.replace(`\uE000${index}\uE001`, escapeHtml(token));
        });
        if (formatted === escaped) return;
        const fragment = document.createElement("template");
        fragment.innerHTML = formatted;
        node.replaceWith(fragment.content);
      });
      return template.innerHTML;
    };
  const renderPrintElement = (element, position = "", compactColumn = false) => {
      const boxSpacing = `${element.margin ? `;margin:${escapeHtml(element.margin)}` : ""}${element.padding ? `;padding:${escapeHtml(element.padding)}` : ""}`;
      const typography = ["field", "variable", "text", "html"].includes(element.type)
        ? `${element.fontSize ? `;font-size:${Number(element.fontSize)}px` : ""}${element.fontFamily ? `;font-family:${escapeHtml(element.fontFamily)}` : ""}`
        : "";
      const verticalAlignment = ["center", "end"].includes(element.verticalAlign) ? element.verticalAlign : "start";
      const compactVerticalStyle = compactColumn
        ? (verticalAlignment === "end" ? ";margin-top:auto" : (verticalAlignment === "center" ? ";margin-top:auto;margin-bottom:auto" : ""))
        : `;align-self:${verticalAlignment}`;
      const positionStyle = `${position}${boxSpacing}${typography}${compactVerticalStyle}`;
      if (element.type === "image") {
        return `<div style="${positionStyle};position:relative;width:${element.imageWidth}px;max-width:100%;height:${element.imageHeight}px;overflow:visible"><img src="${escapeHtml(element.imageUrl)}" alt="${escapeHtml(element.label)}" style="display:block;width:${element.imageWidth}px;height:${element.imageHeight}px;max-width:100%;object-fit:contain"></div>`;
      }
      if (element.type === "line") {
        const lineWidth = Math.max(element.lineStyle === "double" ? 3 : 1, Number(element.lineWidth || 1));
        const overlapsRow = (vertical) => (
          element.row < vertical.row + vertical.rowSpan
          && vertical.row < element.row + element.rowSpan
        );
        const hasLeftVertical = printLayout.elements.some((vertical) => (
          vertical.type === "vline"
          && vertical.col + vertical.colSpan === element.col
          && overlapsRow(vertical)
        ));
        const hasRightVertical = printLayout.elements.some((vertical) => (
          vertical.type === "vline"
          && element.col + element.colSpan === vertical.col
          && overlapsRow(vertical)
        ));
        const horizontalExtension = 6;
        return `<div style="${positionStyle};margin-top:${Number(element.marginTop || 0)}px;margin-right:${hasRightVertical ? -horizontalExtension : 0}px;margin-bottom:${Number(element.marginBottom || 0)}px;margin-left:${hasLeftVertical ? -horizontalExtension : 0}px;overflow:visible"><hr style="margin:0;border:0;border-top:${lineWidth}px ${escapeHtml(element.lineStyle)} ${escapeHtml(element.lineColor)}"></div>`;
      }
      if (element.type === "vline") {
        const lineWidth = Math.max(element.lineStyle === "double" ? 3 : 1, Number(element.lineWidth || 1));
        const minimumHeight = Math.max(24, Number(element.rowSpan || 1) * 24);
        return `<div style="${positionStyle};justify-self:center;width:0;min-height:${minimumHeight}px;height:100%;border-left:${lineWidth}px ${escapeHtml(element.lineStyle)} ${escapeHtml(element.lineColor)}"></div>`;
      }
      if (element.type === "junction") {
        return lineJunctionHtml(element.junction, false, position);
      }
      if (element.type === "pagebreak") {
        return `<div style="${positionStyle};height:0;min-height:0;break-after:page;page-break-after:always"></div>`;
      }
      if (element.type === "variable") {
        if (!element.sourceField) {
          return `<div style="${positionStyle};min-width:0"></div>`;
        }
        const variable = element.sourceField ? `{{ ${element.sourceField} }}` : "";
        const label = String(element.label || "").trim();
        const labelHtml = label
          ? `<strong style="color:${escapeHtml(element.labelColor)}">${escapeHtml(label)}:</strong> `
          : "";
        return `<div style="${positionStyle};${compactColumn ? "width:100%;" : ""}min-width:0;text-align:${escapeHtml(element.textAlign)};overflow-wrap:anywhere">${labelHtml}<span style="color:${escapeHtml(element.textColor)};font-weight:${element.textBold ? "700" : "400"}">${variable}</span></div>`;
      }
      const content = ["html", "text"].includes(element.type)
        ? safeRichHtml(element.content)
        : escapeHtml(element.content || "").replace(/\n/g, "<br>");
      const label = element.type === "field" && !element.hideLabel && element.label
        ? `<strong>${escapeHtml(element.label)}:</strong> `
        : "";
      const minimumHeight = element.type === "field" ? (element.rowSpan > 1 ? 68 : 38) : 0;
      const fieldBorder = element.type === "field" && element.showBottomBorder !== false
        ? ";border-bottom:1px solid #d1d5db"
        : "";
      return `<div style="${positionStyle};width:100%;min-width:0;min-height:${minimumHeight}px${fieldBorder};overflow-wrap:anywhere">${label}${content}</div>`;
    };
    const useIndependentColumns = !printLayout.elements.some((element) => (
      ["line", "vline"].includes(element.type)
    ));
    let fields = "";
    let layoutStyle = "";
    if (useIndependentColumns) {
      const junctions = printLineJunctions();
      const structural = printLayout.elements
        .filter((element) => element.type === "pagebreak")
        .sort((first, second) => first.row - second.row);
      const regular = printLayout.elements.filter((element) => !structural.includes(element)).concat(
        junctions
          .filter((junction) => !structural.some((element) => element.row === junction.row))
          .map((junction, index) => ({
            id: `junction-${junction.row}-${junction.col}-${index}`,
            type: "junction",
            row: junction.row,
            col: junction.col,
            rowSpan: 1,
            colSpan: 1,
            junction,
          })),
      );
      const renderColumnBand = (elements) => {
        if (!elements.length) return "";
        const ordered = [...elements].sort((first, second) => (
          first.col - second.col || first.row - second.row || first.id.localeCompare(second.id)
        ));
        const groups = [];
        ordered.forEach((element) => {
          const start = element.col;
          const end = element.col + element.colSpan - 1;
          const touching = groups.filter((group) => start <= group.end && end >= group.start);
          if (!touching.length) {
            groups.push({ start, end, elements: [element] });
            return;
          }
          const target = touching[0];
          target.start = Math.min(target.start, start);
          target.end = Math.max(target.end, end);
          target.elements.push(element);
          touching.slice(1).forEach((group) => {
            target.start = Math.min(target.start, group.start);
            target.end = Math.max(target.end, group.end);
            target.elements.push(...group.elements);
            groups.splice(groups.indexOf(group), 1);
          });
        });
        const columns = groups.sort((first, second) => first.start - second.start).map((group) => {
          const minimumRow = Math.min(...group.elements.map((element) => element.row));
          const maximumRow = Math.max(...group.elements.map((element) => element.row + element.rowSpan - 1));
          const span = group.end - group.start + 1;
          const content = group.elements.map((element) => {
            const relativeColumn = element.col - group.start + 1;
            const relativeRow = element.row - minimumRow + 1;
            const position = `grid-column:${relativeColumn} / span ${element.colSpan};grid-row:${relativeRow} / span ${element.rowSpan}`;
            return renderPrintElement(element, position);
          }).join("");
          return `<div style="grid-column:${group.start} / span ${span};grid-row:1;display:grid;grid-template-columns:repeat(${span},minmax(0,1fr));grid-template-rows:repeat(${maximumRow - minimumRow + 1},minmax(0,auto));column-gap:6px;row-gap:0;min-width:0">${content}</div>`;
        }).join("");
        return `<div style="display:grid;grid-template-columns:${printGridColumns()};align-items:stretch;column-gap:4px;min-width:0">${columns}</div>`;
      };
      const sections = [];
      let firstRow = 1;
      structural.forEach((separator) => {
        sections.push(renderColumnBand(regular.filter((element) => (
          element.row >= firstRow && element.row < separator.row
        ))));
        sections.push(
          `<div style="display:grid;grid-template-columns:${printGridColumns()};grid-template-rows:minmax(0,auto);column-gap:4px;min-width:0">`
          + `<div style="grid-column:${separator.col} / span ${separator.colSpan};min-width:0">`
          + `${renderPrintElement(separator, "width:100%")}</div>`
          + junctions
            .filter((junction) => junction.row === separator.row)
            .map((junction) => lineJunctionHtml({ ...junction, row: 1 }, true))
            .join("")
          + "</div>",
        );
        firstRow = separator.row + separator.rowSpan;
      });
      sections.push(renderColumnBand(regular.filter((element) => element.row >= firstRow)));
      fields = sections.join("");
      layoutStyle = "display:block";
    } else {
      const pageBreaks = printLayout.elements
        .filter((element) => element.type === "pagebreak")
        .sort((left, right) => left.row - right.row);
      const regularElements = printLayout.elements.filter((element) => element.type !== "pagebreak");
      const junctions = printLineJunctions();
      const renderGridPage = (startRow, endRow) => {
        const pageElements = regularElements.filter((element) => (
          element.row >= startRow && element.row < endRow
        ));
        const pageJunctions = junctions.filter((junction) => (
          junction.row >= startRow && junction.row < endRow
        ));
        if (!pageElements.length && !pageJunctions.length) return "";
        const rowCount = Math.max(1, endRow - startRow);
        const content = pageElements.map((element) => {
          const relativeRow = element.row - startRow + 1;
          const position = `grid-column:${element.col} / span ${effectivePrintColSpan(element)};grid-row:${relativeRow} / span ${element.rowSpan}`;
          return renderPrintElement(element, position);
        }).join("");
        const junctionContent = pageJunctions.map((junction) => (
          lineJunctionHtml({ ...junction, row: junction.row - startRow + 1 }, true)
        )).join("");
        return `<div style="display:grid;grid-template-columns:${printGridColumns()};grid-template-rows:repeat(${rowCount},minmax(0,auto));align-content:start;column-gap:4px;row-gap:0">${content}${junctionContent}</div>`;
      };
      const sections = [];
      let startRow = 1;
      pageBreaks.forEach((pageBreak) => {
        sections.push(renderGridPage(startRow, pageBreak.row));
        sections.push(renderPrintElement(pageBreak, "width:100%"));
        startRow = pageBreak.row + pageBreak.rowSpan;
      });
      sections.push(renderGridPage(startRow, printLayout.grid.rows + 1));
      fields = sections.join("");
      layoutStyle = "display:block";
    }
    const signatureEnabled = signatureToggle?.checked !== false;
    const signatureAlignment = {
      ESQUERDA: "left",
      DIREITA: "right",
    }[form.elements.tp_alinhamento_assinatura?.value] || "center";
    const signatureBlockMargin = {
      left: "16px auto 0 0",
      right: "16px 0 0 auto",
      center: "16px auto 0",
    }[signatureAlignment];
    const signatureCouncil = form.elements.sn_exibe_conselho_assinatura?.checked
      ? " - {{ prestador.conselho }} {{ prestador.numero_conselho }} {{ prestador.uf_conselho }}"
      : "";
    const signature = `<section data-celeris-signature="true" style="display:grid;width:max-content;min-width:92mm;max-width:100%;margin:${signatureBlockMargin};break-inside:avoid;text-align:${signatureAlignment}"><div style="width:100%;height:34px;border-bottom:1px solid #111;margin:0 0 6px"></div><strong>{{ prestador.nome }}${signatureCouncil}</strong></section>`;
    const signatureHtml = form.dataset.documentElement === "DOCUMENTO" && signatureEnabled ? signature : "";
    const floatingImageHeight = printLayout.elements
      .filter((element) => element.type === "image" && element.rowSpan > 1)
      .reduce((height, element) => Math.max(height, element.imageHeight), 0);
    return `<main data-celeris-grid-print="true" style="width:100%;max-width:none;min-height:0;margin:0;padding:2px;background:#fff;color:#111;font-size:${printLayout.grid.fontSize}px;font-family:${escapeHtml(printLayout.grid.fontFamily)};line-height:1.15;box-sizing:border-box"><section style="${layoutStyle};min-height:${useIndependentColumns ? 0 : floatingImageHeight}px">${fields}</section>${signatureHtml}</main>`;
  };
  const printSourceSelect = printSettingsModal?.querySelector('[data-print-property="sourceField"]');
  const printSourceGroup = printSettingsModal?.querySelector("[data-print-source-group]");
  const printCodeInput = printSettingsModal?.querySelector("[data-print-code-input]");
  const printCodeHighlight = printSettingsModal?.querySelector("[data-print-code-highlight]");
  const printImageFileInput = printSettingsModal?.querySelector("[data-print-image-file]");
  const printVariableList = printSettingsModal?.querySelector("[data-print-variable-list]");
  const printVariablePalette = printSettingsModal?.querySelector(".document-variable-palette");
  const printSettingsHelp = printSettingsModal?.querySelector("[data-print-settings-help]");
  if (printVariablePalette && printVariablePalette.parentElement !== printSettingsModal) {
    printSettingsModal.appendChild(printVariablePalette);
  }
  let variableLabelIsAutomatic = false;
  let previousAutomaticVariableLabel = "";
  const syncPrintSettingsHeight = () => {
    if (!printVariablePalette || printVariablePalette.hidden || printSettingsModal.hidden) return;
    const card = printSettingsModal.querySelector(":scope > .card");
    if (!card) return;
    printVariablePalette.style.height = `${Math.min(card.offsetHeight, window.innerHeight * 0.92)}px`;
  };
  const standardPrintFields = [
    ["paciente.nome", "Nome do paciente"],
    ["paciente.codigo", "Prontuário"],
    ["paciente.nascimento", "Data de nascimento"],
    ["paciente.mae", "Nome da mãe"],
    ["paciente.pai", "Nome do pai"],
    ["paciente.cpf", "CPF do paciente"],
    ["paciente.rg", "RG do paciente"],
    ["paciente.cns", "CNS do paciente"],
    ["paciente.sexo", "Sexo do paciente"],
    ["paciente.genero", "Identidade de gênero"],
    ["paciente.estado_civil", "Estado civil"],
    ["paciente.telefone", "Telefone"],
    ["paciente.celular", "Celular"],
    ["paciente.email", "E-mail"],
    ["paciente.endereco", "Endereço"],
    ["paciente.numero", "Número do endereço"],
    ["paciente.bairro", "Bairro"],
    ["paciente.cidade", "Cidade"],
    ["paciente.uf", "UF"],
    ["paciente.cep", "CEP"],
    ["atendimento.codigo", "Código do atendimento"],
    ["atendimento.data_hora", "Data e hora do atendimento"],
    ["atendimento.status", "Status do atendimento"],
    ["atendimento.especialidade", "Especialidade"],
    ["atendimento.tipo", "Tipo de atendimento"],
    ["atendimento.origem", "Origem do atendimento"],
    ["atendimento.convenio", "Convênio"],
    ["atendimento.plano", "Plano"],
    ["atendimento.subplano", "Subplano"],
    ["atendimento.setor", "Setor atual"],
    ["atendimento.cid", "CID"],
    ["atendimento.usuario_criacao", "Usuário que gerou o atendimento"],
    ["prestador.nome", "Prestador responsável"],
    ["prestador.conselho", "Conselho do prestador"],
    ["prestador.numero_conselho", "Número do conselho"],
    ["prestador.uf_conselho", "UF do conselho"],
    ["empresa.nome", "Empresa"],
    ["documento.codigo", "Código do documento"],
    ["documento.titulo", "Título do documento"],
    ["documento.status", "Status do documento"],
    ["documento.data_hora_criacao", "Data/hora de criação do documento"],
    ["documento.data_hora_atual", "Data/hora atual de emissão"],
    ["documento.usuario_criacao", "Usuário que criou o documento"],
    ["documento.pagina", "Número da página"],
    ...customVariables.map((item) => {
      const configuration = item.ds_projeto_tela?.customVariable || {};
      const name = normalizeName(configuration.name || item.nm_modelo);
      return [`variavel.${name}`, item.nm_modelo];
    }),
  ];
  screenVariableOptionsProvider = () => [
    ...standardPrintFields,
    ...formFields.map((field) => [`campo.${field.name}`, field.label]),
  ];
  const printFieldLabels = new Map([
    ...standardPrintFields,
    ...formFields.map((field) => [`campo.${field.name}`, field.label]),
  ]);
  const printSourceOptions = [
    ...standardPrintFields.map(([value, label]) => ({ value, label })),
    ...formFields.map((field) => ({ value: `campo.${field.name}`, label: field.label })),
  ];
  const sourceGroupFor = (value) => {
    if (!value) return "paciente";
    if (value.startsWith("paciente.")) return "paciente";
    if (value.startsWith("atendimento.")) return "atendimento";
    if (value.startsWith("documento.")) return "documento";
    if (value.startsWith("campo.")) return "campos";
    return "outras";
  };
  const renderPrintSourceOptions = (group, selectedValue = "") => {
    if (!printSourceSelect) return;
    printSourceSelect.replaceChildren(new Option("", ""));
    printSourceOptions
      .filter((option) => sourceGroupFor(option.value) === group)
      .forEach((option) => printSourceSelect.appendChild(new Option(option.label, option.value)));
    printSourceSelect.value = selectedValue;
  };
  renderPrintSourceOptions(printSourceGroup?.value || "paciente");
  const insertPrintVariable = (variable) => {
    if (!printCodeInput) return;
    const token = `{{ ${variable} }}`;
    const start = printCodeInput.selectionStart ?? printCodeInput.value.length;
    const end = printCodeInput.selectionEnd ?? start;
    printCodeInput.setRangeText(token, start, end, "end");
    printCodeInput.focus();
    printCodeInput.dispatchEvent(new Event("input", { bubbles: true }));
  };
  if (printVariableList) {
    const variables = [
      ...standardPrintFields,
      ...formFields.map((field) => [`campo.${field.name}`, field.label]),
    ];
    variables.forEach(([value, label]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.draggable = true;
      button.dataset.printVariable = value;
      button.innerHTML = `<strong>${escapeHtml(label)}</strong><code>{{ ${escapeHtml(value)} }}</code>`;
      button.addEventListener("click", () => insertPrintVariable(value));
      button.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/document-variable", value);
        event.dataTransfer.effectAllowed = "copy";
      });
      printVariableList.appendChild(button);
    });
  }
  const printVariableSearch = printSettingsModal?.querySelector("[data-print-variable-search]");
  printVariableSearch?.addEventListener("input", () => {
    const term = printVariableSearch.value.trim().toLocaleLowerCase("pt-BR");
    printVariableList?.querySelectorAll("button").forEach((button) => {
      button.hidden = Boolean(term) && !button.textContent.toLocaleLowerCase("pt-BR").includes(term);
    });
  });
  printCodeInput?.addEventListener("dragover", (event) => {
    if (event.dataTransfer.types.includes("text/document-variable")) event.preventDefault();
  });
  printCodeInput?.addEventListener("drop", (event) => {
    const variable = event.dataTransfer.getData("text/document-variable");
    if (!variable) return;
    event.preventDefault();
    insertPrintVariable(variable);
  });
  const updateVisiblePrintSettings = () => {
    const type = activePrintElement?.type || "text";
    printSettingsModal?.querySelectorAll("[data-print-types]").forEach((container) => {
      const visible = container.dataset.printTypes.split(",").includes(type);
      container.hidden = !visible;
      container.querySelectorAll("input, select, textarea").forEach((input) => { input.disabled = !visible; });
    });
    if (printVariablePalette) printVariablePalette.hidden = !["field", "text", "html"].includes(type);
    if (printSettingsHelp && !printSettingsHelp.hidden) {
      const descriptions = {
        text: "Aceita HTML e estilos inline. Atalhos: *texto* para negrito, _texto_ para sublinhado, /texto/ para itálico, <center>...</center para centralizar o texto, <left>...</left> para alinhar à esquerda e <right>...</right> para alinhar à direita. Variáveis podem ficar dentro desses atalhos.",
        html: "Conteúdo HTML reutilizável. Scripts e atributos inseguros são removidos automaticamente.",
        field: "Exibe um campo preenchido no formulário. O label pode ser exibido ou ocultado.",
        variable: "Selecione primeiro o grupo e depois a variável. O label padrão acompanha a variável até ser alterado manualmente. Configure cores, negrito e alinhamento.",
        image: "A imagem reserva somente sua largura e altura configuradas. Quando ocupa várias linhas, não aumenta o espaçamento entre as linhas de texto vizinhas.",
        line: "Linha separadora sem margem ou padding padrão. Defina cor, espessura e margens somente quando necessário.",
        vline: "Linha vertical. Ao se aproximar de linhas horizontais, a grade cria junções automáticas não editáveis.",
        pagebreak: "Força o conteúdo seguinte a iniciar em uma nova página.",
      };
      printSettingsHelp.textContent = descriptions[type] || "Configure o elemento e sua posição no layout de impressão.";
    }
  };
  const renderCodeHighlight = () => {
    if (!printCodeInput || !printCodeHighlight) return;
    const tokens = String(printCodeInput.value || "").split(/(<[^>]*>|{{\s*[^}]+\s*}})/g);
    printCodeHighlight.innerHTML = tokens.map((token) => {
      const escaped = escapeHtml(token);
      if (/^<[^>]*>$/.test(token)) return `<span class="code-html-tag">${escaped}</span>`;
      if (/^{{\s*[^}]+\s*}}$/.test(token)) return `<span class="code-template-variable">${escaped}</span>`;
      return escaped;
    }).join("");
    printCodeHighlight.scrollTop = printCodeInput.scrollTop;
    printCodeHighlight.scrollLeft = printCodeInput.scrollLeft;
  };
  const openPrintSettings = (element) => {
    activePrintElement = element;
    if (printSettingsHelp) printSettingsHelp.hidden = true;
    const sourceGroup = sourceGroupFor(element.sourceField || "");
    if (printSourceGroup) printSourceGroup.value = sourceGroup;
    renderPrintSourceOptions(sourceGroup, element.sourceField || "");
    printSettingsModal.querySelectorAll("[data-print-property]").forEach((input) => {
      if (input.type === "checkbox") input.checked = Boolean(element[input.dataset.printProperty]);
      else if (input.dataset.printProperty === "fontSize") input.value = element.fontSize || printLayout.grid.fontSize;
      else if (input.dataset.printProperty === "fontFamily") input.value = element.fontFamily || printLayout.grid.fontFamily;
      else input.value = element[input.dataset.printProperty] ?? "";
    });
    if (printImageFileInput) printImageFileInput.value = "";
    syncHexColorControls(printSettingsModal);
    if (element.type === "variable") {
      previousAutomaticVariableLabel = printFieldLabels.get(element.sourceField) || "";
      variableLabelIsAutomatic = !element.label || element.label === previousAutomaticVariableLabel;
    } else {
      previousAutomaticVariableLabel = "";
      variableLabelIsAutomatic = false;
    }
    updateVisiblePrintSettings();
    const title = printSettingsModal.querySelector("[data-print-settings-title]");
    if (title) title.textContent = `Configuração do elemento impresso (${element.id})`;
    renderCodeHighlight();
    printSettingsModal.hidden = false;
    requestAnimationFrame(syncPrintSettingsHeight);
  };
  printSettingsModal?.querySelector("[data-print-settings-help-toggle]")?.addEventListener("click", () => {
    printSettingsHelp.hidden = !printSettingsHelp.hidden;
    updateVisiblePrintSettings();
    requestAnimationFrame(syncPrintSettingsHeight);
  });
  const insertPrintRow = (atRow) => {
    if (printLayout.grid.rows >= 60) return false;
    printLayout.grid.rows = Math.min(60, printLayout.grid.rows + 1);
    printLayout.elements.forEach((element) => {
      if (element.row >= atRow) element.row += 1;
    });
    markEditorDirty();
    renderPrintBuilder();
    return true;
  };
  const insertPrintColumn = (atColumn) => {
    if (printLayout.grid.columns >= 12) return;
    printLayout.grid.columns += 1;
    printLayout.elements.forEach((element) => {
      const lastColumn = element.col + element.colSpan - 1;
      if (element.col < atColumn && atColumn <= lastColumn) element.colSpan += 1;
      else if (element.col >= atColumn) element.col += 1;
    });
    markEditorDirty();
    renderPrintBuilder();
  };
  const printCellOccupied = (row, col) => printLayout.elements.some((element) => (
    row >= element.row
    && row < element.row + element.rowSpan
    && col >= element.col
    && col < element.col + element.colSpan
  ));
  const freePrintColumnSpan = (row, col) => {
    let span = 0;
    while (col + span <= printLayout.grid.columns && !printCellOccupied(row, col + span)) {
      span += 1;
    }
    return Math.max(1, span);
  };
  const freePrintRowSpan = (row, col) => {
    let span = 0;
    while (row + span <= printLayout.grid.rows && !printCellOccupied(row + span, col)) {
      span += 1;
    }
    return Math.max(1, span);
  };
  const addPrintField = (field, row, col) => {
    printLayout.elements.push({
      ...printElementFromField(field),
      id: crypto.randomUUID?.() || `print-${Date.now()}`,
      row,
      col,
    });
    markEditorDirty();
    renderPrintBuilder();
  };
  const canExpandPrintElement = (element, direction) => {
    const atBoundary = (
      (direction === "left" && element.col === 1)
      || (direction === "right" && element.col + element.colSpan - 1 === printLayout.grid.columns)
      || (direction === "top" && element.row === 1)
      || (direction === "bottom" && element.row + element.rowSpan - 1 === printLayout.grid.rows)
    );
    if (atBoundary) {
      return ["left", "right"].includes(direction)
        ? printLayout.grid.columns < 12
        : printLayout.grid.rows < 60;
    }
    const candidate = { ...element };
    if (direction === "left") {
      candidate.col -= 1;
      candidate.colSpan += 1;
    } else if (direction === "right") candidate.colSpan += 1;
    else if (direction === "top") {
      candidate.row -= 1;
      candidate.rowSpan += 1;
    } else candidate.rowSpan += 1;
    return !printLayout.elements.some((other) => other.id !== element.id && fieldsOverlap(candidate, other));
  };
  const resizePrintElement = (element, direction, shrink = false) => {
    if (shrink) {
      if (["left", "right"].includes(direction) && element.colSpan <= 1) return;
      if (["top", "bottom"].includes(direction) && element.rowSpan <= 1) return;
      if (direction === "left") { element.col += 1; element.colSpan -= 1; }
      else if (direction === "right") element.colSpan -= 1;
      else if (direction === "top") { element.row += 1; element.rowSpan -= 1; }
      else element.rowSpan -= 1;
    } else {
      const candidate = { ...element };
      if (direction === "left" && element.col > 1) {
        candidate.col -= 1;
        candidate.colSpan += 1;
      } else if (direction === "right" && element.col + element.colSpan - 1 < printLayout.grid.columns) {
        candidate.colSpan += 1;
      } else if (direction === "top" && element.row > 1) {
        candidate.row -= 1;
        candidate.rowSpan += 1;
      } else if (direction === "bottom" && element.row + element.rowSpan - 1 < printLayout.grid.rows) {
        candidate.rowSpan += 1;
      }
      if (
        (candidate.col !== element.col || candidate.row !== element.row
          || candidate.colSpan !== element.colSpan || candidate.rowSpan !== element.rowSpan)
        && printLayout.elements.some((other) => other.id !== element.id && fieldsOverlap(candidate, other))
      ) return;
      if (direction === "left") {
      if (element.col === 1 && printLayout.grid.columns >= 12) return;
      if (element.col === 1) insertPrintColumn(1);
      element.col -= 1;
      element.colSpan += 1;
      } else if (direction === "right") {
      if (element.col + element.colSpan - 1 >= printLayout.grid.columns) printLayout.grid.columns = Math.min(12, printLayout.grid.columns + 1);
      element.colSpan = Math.min(printLayout.grid.columns - element.col + 1, element.colSpan + 1);
      } else if (direction === "top") {
      if (element.row === 1 && printLayout.grid.rows >= 60) return;
      if (element.row === 1) insertPrintRow(1);
      element.row -= 1;
      element.rowSpan += 1;
      } else {
      if (element.row + element.rowSpan - 1 >= printLayout.grid.rows) printLayout.grid.rows = Math.min(60, printLayout.grid.rows + 1);
      element.rowSpan = Math.min(printLayout.grid.rows - element.row + 1, element.rowSpan + 1);
      }
    }
    markEditorDirty();
    renderPrintBuilder();
  };
  printCodeInput?.addEventListener("input", renderCodeHighlight);
  printCodeInput?.addEventListener("scroll", renderCodeHighlight);
  printSourceSelect?.addEventListener("change", () => {
    const selectedValue = printSourceSelect.value;
    if (!selectedValue) return;
    const field = formFields.find((item) => `campo.${item.name}` === selectedValue);
    const label = field?.label || printSourceSelect.selectedOptions[0]?.textContent || selectedValue;
    const labelInput = printSettingsModal.querySelector('[data-print-property="label"]');
    if (activePrintElement?.type === "variable") {
      if (
        variableLabelIsAutomatic
        || !labelInput.value.trim()
        || labelInput.value === previousAutomaticVariableLabel
      ) {
        labelInput.value = label;
        variableLabelIsAutomatic = true;
      }
      previousAutomaticVariableLabel = label;
    } else {
      if (!labelInput.value.trim()) labelInput.value = label;
      printCodeInput.value = `{{ ${field?.binding || selectedValue} }}`;
      renderCodeHighlight();
    }
  });
  printSettingsModal?.querySelector('[data-print-property="label"]')?.addEventListener("input", (event) => {
    if (activePrintElement?.type !== "variable" || !event.isTrusted) return;
    variableLabelIsAutomatic = !event.currentTarget.value.trim();
  });
  printSourceGroup?.addEventListener("change", () => {
    renderPrintSourceOptions(printSourceGroup.value);
    printSourceSelect.dispatchEvent(new Event("change", { bubbles: true }));
  });
  printImageFileInput?.addEventListener("change", () => {
    const file = printImageFileInput.files?.[0];
    if (!file || !activePrintElement) return;
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      const result = String(reader.result || "");
      printSettingsModal.querySelector('[data-print-property="imageUrl"]').value = result;
      const image = new Image();
      image.addEventListener("load", () => {
        const widthInput = printSettingsModal.querySelector('[data-print-property="imageWidth"]');
        const heightInput = printSettingsModal.querySelector('[data-print-property="imageHeight"]');
        const scale = Math.min(1, 600 / image.naturalWidth);
        widthInput.value = String(Math.max(1, Math.round(image.naturalWidth * scale)));
        heightInput.value = String(Math.max(1, Math.round(image.naturalHeight * scale)));
      });
      image.src = result;
    });
    reader.readAsDataURL(file);
  });
  const printCodeEditor = printSettingsModal?.querySelector(".document-code-editor");
  if (printCodeEditor && window.ResizeObserver) {
    new ResizeObserver(() => {
      const card = printSettingsModal.querySelector(":scope > .card");
      if (!card || printSettingsModal.hidden) return;
      const desiredWidth = Math.min(
        window.innerWidth - 330,
        Math.max(720, printCodeEditor.getBoundingClientRect().width + 64),
      );
      card.style.width = `${desiredWidth}px`;
      syncPrintSettingsHeight();
    }).observe(printCodeEditor);
  }
  const renderPrintBuilder = () => {
    if (!printElementList) return;
    document.querySelectorAll('[data-cell-menu-portal="print"]').forEach((menu) => menu.remove());
    printElementList.innerHTML = "";
    printElementList.style.gridTemplateColumns = `repeat(${printLayout.grid.columns}, minmax(110px, 1fr))`;
    printElementList.style.gridTemplateRows = `repeat(${printLayout.grid.rows}, minmax(82px, auto))`;
    const junctionPositions = new Set(printLineJunctions().map((junction) => `${junction.row}:${junction.col}`));
    for (let row = 1; row <= printLayout.grid.rows; row += 1) {
      for (let col = 1; col <= printLayout.grid.columns; col += 1) {
        const cell = document.createElement("div");
        cell.className = "document-grid-cell";
        cell.style.gridColumn = String(col);
        cell.style.gridRow = String(row);
        cell.dataset.gridCol = String(col);
        cell.dataset.gridRow = String(row);
        const isJunction = junctionPositions.has(`${row}:${col}`);
        if (isJunction) {
          cell.classList.add("document-grid-junction-cell");
          cell.dataset.junction = "true";
        }
        const fieldOptions = formFields.map((field) => (
          `<button type="button" data-print-create-field="${escapeHtml(field.name)}">${escapeHtml(field.label)}</button>`
        )).join("");
        if (!printCellOccupied(row, col) && !isJunction) {
          cell.innerHTML = `
            <div class="document-cell-actions">
              <button class="cell-direction cell-direction-top" type="button" data-print-row-before title="↑ Adicionar linha acima">+</button>
              <button class="cell-direction cell-direction-bottom" type="button" data-print-row-after title="↓ Adicionar linha abaixo">+</button>
              <button class="cell-direction cell-direction-left" type="button" data-print-column-before title="← Adicionar coluna à esquerda">+</button>
              <button class="cell-direction cell-direction-right" type="button" data-print-column-after title="Adicionar coluna à direita →">+</button>
              <div class="document-cell-create">
                <button type="button" data-print-create-toggle title="Adicionar elemento"><span>+</span></button>
                <button type="button" data-print-create-toggle aria-label="Outros elementos">▾</button>
                <div class="document-cell-create-menu" data-print-create-menu hidden>
                  <strong>Outros elementos</strong>
                  <button type="button" data-print-create-type="text">Texto fixo/variáveis</button>
                  <button type="button" data-print-create-type="variable">Variável</button>
                  <button type="button" data-print-create-type="image">Imagem</button>
                  <button type="button" data-print-create-type="line">Linha</button>
                  <button type="button" data-print-create-type="vline">Linha vertical</button>
                  <button type="button" data-print-create-type="pagebreak">Quebra de página</button>
                  ${fieldOptions ? `
                    <button class="document-cell-fields-toggle" type="button" data-print-fields-toggle>Campos do documento <span>›</span></button>
                    <div class="document-cell-fields-menu" data-print-fields-menu hidden>${fieldOptions}</div>
                  ` : ""}
                </div>
              </div>
            </div>`;
        }
        const printCreateMenu = cell.querySelector("[data-print-create-menu]");
        const printFieldsMenu = cell.querySelector("[data-print-fields-menu]");
        printCreateMenu?.addEventListener("click", (event) => {
          const action = event.target.closest("button");
          if (!action) return;
          event.preventDefault();
          event.stopPropagation();
          if (action.matches("[data-print-create-type]")) {
            addPrintElement(action.dataset.printCreateType, { row, col });
          } else if (action.matches("[data-print-fields-toggle]")) {
            if (printFieldsMenu.hidden) openVisibleCellMenu(printFieldsMenu, event, "print");
            else printFieldsMenu.hidden = true;
          }
        });
        printFieldsMenu?.addEventListener("click", (event) => {
          const action = event.target.closest("[data-print-create-field]");
          if (!action) return;
          event.preventDefault();
          event.stopPropagation();
          const field = formFields.find((item) => item.name === action.dataset.printCreateField);
          if (field) addPrintField(field, row, col);
        });
        if (col === 1) {
          cell.insertAdjacentHTML("beforeend", '<button class="document-track-handle document-row-handle" type="button" draggable="true" title="Arrastar linha" aria-label="Reordenar linha">⋮</button>');
        }
        if (row === 1 || row === printLayout.grid.rows) {
          const edgeClass = row === 1 ? "document-column-handle-top" : "document-column-handle-bottom";
          cell.insertAdjacentHTML("beforeend", `<button class="document-track-handle document-column-handle ${edgeClass}" type="button" draggable="true" title="Arrastar coluna" aria-label="Reordenar coluna">⋯</button>`);
        }
        cell.querySelectorAll(".document-track-handle").forEach((handle) => {
          handle.addEventListener("dragstart", (event) => {
            event.stopPropagation();
            const kind = handle.classList.contains("document-row-handle") ? "row" : "column";
            event.dataTransfer.setData("text/document-grid-track", kind);
            event.dataTransfer.setData("text/document-grid-scope", "print");
            event.dataTransfer.setData("text/document-grid-index", String(kind === "row" ? row : col));
            event.dataTransfer.effectAllowed = "move";
          });
        });
        cell.addEventListener("dragover", (event) => event.preventDefault());
        cell.addEventListener("contextmenu", (event) => {
          if (isJunction) {
            event.preventDefault();
            event.stopPropagation();
            return;
          }
          openGridContextMenu(event, row, col, "print");
        });
        cell.addEventListener("drop", (event) => {
          event.preventDefault();
          if (isJunction) return;
          handleGridDrop(event, "print", row, col);
        });
        cell.addEventListener("click", (event) => {
          if (isJunction) return;
          const action = event.target.closest("button");
          if (!action) return;
          event.preventDefault();
          event.stopPropagation();
          if (action.matches("[data-print-row-before]")) insertPrintRow(row);
          else if (action.matches("[data-print-row-after]")) insertPrintRow(row + 1);
          else if (action.matches("[data-print-column-before]")) insertPrintColumn(col);
          else if (action.matches("[data-print-column-after]")) insertPrintColumn(col + 1);
          else if (action.matches("[data-print-create-field]")) {
            const field = formFields.find((item) => item.name === action.dataset.printCreateField);
            if (field) addPrintField(field, row, col);
          } else if (action.matches("[data-print-create-type]")) {
            addPrintElement(action.dataset.printCreateType, { row, col });
          } else if (action.matches("[data-print-create-toggle]")) {
            if (printCreateMenu.hidden) openVisibleCellMenu(printCreateMenu, event, "print");
            else closeVisibleCellMenu(printCreateMenu);
          } else if (action.matches("[data-print-fields-toggle]")) {
            if (printFieldsMenu.hidden) openVisibleCellMenu(printFieldsMenu, event, "print");
            else closeVisibleCellMenu(printFieldsMenu);
          }
        });
        printElementList.appendChild(cell);
      }
    }
    printLayout.elements.forEach((element, index) => {
      const card = document.createElement("article");
      card.className = "document-form-field-card print-layout-element";
      card.draggable = true;
      card.style.gridColumn = `${element.col} / span ${element.colSpan}`;
      card.style.gridRow = `${element.row} / span ${element.rowSpan}`;
      card.innerHTML = `
        <div class="document-field-expand-actions">
          ${canExpandPrintElement(element, "top") ? '<button class="field-expand-top" type="button" data-print-resize="top" title="Expandir para cima">⌃</button>' : ""}
          ${canExpandPrintElement(element, "bottom") ? '<button class="field-expand-bottom" type="button" data-print-resize="bottom" title="Expandir para baixo">⌄</button>' : ""}
          ${canExpandPrintElement(element, "left") ? '<button class="field-expand-left" type="button" data-print-resize="left" title="Expandir para a esquerda">‹</button>' : ""}
          ${canExpandPrintElement(element, "right") ? '<button class="field-expand-right" type="button" data-print-resize="right" title="Expandir para a direita">›</button>' : ""}
          ${element.rowSpan > 1 ? '<button class="field-shrink-top" type="button" data-print-shrink="top">⌄</button><button class="field-shrink-bottom" type="button" data-print-shrink="bottom">⌃</button>' : ""}
          ${element.colSpan > 1 ? '<button class="field-shrink-left" type="button" data-print-shrink="left">›</button><button class="field-shrink-right" type="button" data-print-shrink="right">‹</button>' : ""}
        </div>
        <div class="document-field-card-heading">
          <span class="document-field-kind-icon" aria-hidden="true">${element.type === "image" ? "□" : (element.type === "line" ? "_" : (element.type === "vline" ? "|" : (element.type === "pagebreak" ? "┄" : (element.type === "variable" ? "V" : "T"))))}</span>
          <strong>${escapeHtml(element.label)}</strong>
        </div>
        <span>${escapeHtml(element.content || element.type)}</span>
        <div class="document-field-card-actions">
          <button type="button" data-print-settings title="Configurar">⚙</button>
          <button type="button" data-print-remove title="Remover">×</button>
        </div>`;
      card.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/print-element", element.id);
        const rect = card.getBoundingClientRect();
        event.dataTransfer.setData("text/document-drag-col-offset", String(Math.min(
          element.colSpan - 1,
          Math.max(0, Math.floor(((event.clientX - rect.left) / Math.max(rect.width, 1)) * element.colSpan)),
        )));
        event.dataTransfer.setData("text/document-drag-row-offset", String(Math.min(
          element.rowSpan - 1,
          Math.max(0, Math.floor(((event.clientY - rect.top) / Math.max(rect.height, 1)) * element.rowSpan)),
        )));
        event.dataTransfer.effectAllowed = "move";
        card.classList.add("dragging");
      });
      card.addEventListener("dragend", () => card.classList.remove("dragging"));
      card.addEventListener("dragover", (event) => {
        event.preventDefault();
        card.classList.add("drag-over");
      });
      card.addEventListener("dragleave", () => card.classList.remove("drag-over"));
      card.addEventListener("drop", (event) => {
        event.preventDefault();
        event.stopPropagation();
        card.classList.remove("drag-over");
        const position = gridPositionFromPointer(printElementList, event, element.row, element.col);
        handleGridDrop(event, "print", position.row, position.col);
      });
      card.addEventListener("contextmenu", (event) => openGridContextMenu(event, element.row, element.col, "print", element.id));
      card.querySelector("[data-print-settings]").addEventListener("click", () => openPrintSettings(element));
      card.querySelectorAll("[data-print-resize]").forEach((button) => {
        button.addEventListener("click", () => resizePrintElement(element, button.dataset.printResize));
      });
      card.querySelectorAll("[data-print-shrink]").forEach((button) => {
        button.addEventListener("click", () => resizePrintElement(element, button.dataset.printShrink, true));
      });
      card.querySelector("[data-print-remove]").addEventListener("click", () => {
        printLayout.elements.splice(index, 1);
        markEditorDirty();
        renderPrintBuilder();
      });
      printElementList.appendChild(card);
    });
    printLineJunctions().forEach((junction) => {
      const marker = document.createElement("div");
      marker.className = "document-grid-junction";
      marker.style.gridColumn = String(junction.col);
      marker.style.gridRow = String(junction.row);
      marker.innerHTML = lineJunctionHtml(junction);
      printElementList.appendChild(marker);
    });
    if (printColumnsInput) printColumnsInput.value = String(printLayout.grid.columns);
    if (printRowsInput) printRowsInput.value = String(printLayout.grid.rows);
    if (printFontSizeInput) printFontSizeInput.value = String(printLayout.grid.fontSize);
    if (printFontFamilyInput) printFontFamilyInput.value = printLayout.grid.fontFamily;
  };
  const addPrintElement = (type, requestedPosition = null) => {
    const requested = requestedPosition || firstFreePrintPosition();
    let position = requested;
    if (type === "pagebreak") {
      const occupants = printLayout.elements.filter((element) => (
        requested.row >= element.row
        && requested.row < element.row + element.rowSpan
      ));
      const targetRow = occupants.length
        ? Math.max(...occupants.map((element) => element.row + element.rowSpan))
        : requested.row;
      if (occupants.length && !insertPrintRow(targetRow)) return;
      position = { row: targetRow, col: 1 };
    }
    const defaults = {
      text: { label: "Texto", content: "Texto fixo {{ paciente.nome }}" },
      field: { label: "Campo", content: "{{ campo.nome_do_campo }}" },
      variable: {
        label: "",
        content: "",
        sourceField: "",
        labelColor: "#111111",
        textColor: "#111111",
        textBold: false,
        textAlign: "left",
      },
      image: { label: "Imagem", content: "", imageUrl: "" },
      line: { label: "Linha", content: "", lineColor: "#111111", lineWidth: 1, lineStyle: "solid", marginTop: 0, marginBottom: 0 },
      vline: { label: "Linha vertical", content: "", lineColor: "#111111", lineWidth: 1, lineStyle: "solid", marginTop: 0, marginBottom: 0 },
      pagebreak: { label: "Quebra de página", content: "" },
    }[type];
    printLayout.elements.push({
      id: crypto.randomUUID?.() || `print-${Date.now()}`,
      type,
      imageWidth: 240,
      imageHeight: 120,
      colSpan: type === "pagebreak"
        ? printLayout.grid.columns
        : (type === "line" ? freePrintColumnSpan(position.row, position.col) : 1),
      rowSpan: type === "vline" ? freePrintRowSpan(position.row, position.col) : 1,
      margin: "",
      padding: "",
      verticalAlign: "start",
      ...position,
      ...defaults,
    });
    markEditorDirty();
    renderPrintBuilder();
  };
  printBuilder?.querySelectorAll("[data-print-add]").forEach((button) => {
    button.addEventListener("click", () => addPrintElement(button.dataset.printAdd));
  });
  printColumnsInput?.addEventListener("change", () => {
    requestGridResize("column", Math.max(1, Math.min(12, Number(printColumnsInput.value || 1))), "print");
  });
  printRowsInput?.addEventListener("change", () => {
    requestGridResize("row", Math.max(1, Math.min(60, Number(printRowsInput.value || 1))), "print");
  });
  printFontSizeInput?.addEventListener("change", () => {
    printLayout.grid.fontSize = Math.max(7, Math.min(72, Number(printFontSizeInput.value || 11)));
    printLayout.elements.forEach((element) => {
      if (!element.fontSizeCustom) element.fontSize = "";
    });
    markEditorDirty();
    renderPrintBuilder();
  });
  printFontFamilyInput?.addEventListener("change", () => {
    printLayout.grid.fontFamily = printFontFamilyInput.value || "Arial, sans-serif";
    printLayout.elements.forEach((element) => {
      if (!element.fontFamilyCustom) element.fontFamily = "";
    });
    markEditorDirty();
    renderPrintBuilder();
  });
  printSettingsModal?.querySelector("[data-print-settings-close]")?.addEventListener("click", () => {
    if (printSettingsHelp) printSettingsHelp.hidden = true;
    printSettingsModal.hidden = true;
    activePrintElement = null;
  });
  printSettingsModal?.querySelector("[data-print-settings-save]")?.addEventListener("click", () => {
    if (!activePrintElement) return;
    const updates = {};
    printSettingsModal.querySelectorAll("[data-print-property]").forEach((input) => {
      const property = input.dataset.printProperty;
      updates[property] = input.type === "checkbox"
        ? input.checked
        : property === "fontSize"
        ? (input.value ? Math.max(7, Math.min(72, Number(input.value))) : "")
        : ["colSpan", "rowSpan", "imageWidth", "imageHeight", "lineWidth"].includes(property)
        ? Math.max(1, Number(input.value || 1))
        : ["marginTop", "marginBottom"].includes(property)
        ? Math.max(0, Number(input.value || 0))
        : input.value;
    });
    if (["field", "variable", "text", "html"].includes(activePrintElement.type)) {
      const selectedFontSize = Math.max(7, Math.min(72, Number(updates.fontSize || printLayout.grid.fontSize)));
      const selectedFontFamily = updates.fontFamily || printLayout.grid.fontFamily;
      updates.fontSizeCustom = selectedFontSize !== printLayout.grid.fontSize;
      updates.fontFamilyCustom = selectedFontFamily !== printLayout.grid.fontFamily;
      updates.fontSize = updates.fontSizeCustom ? selectedFontSize : "";
      updates.fontFamily = updates.fontFamilyCustom ? selectedFontFamily : "";
    }
    updates.colSpan = Math.min(
      Number(updates.colSpan || activePrintElement.colSpan),
      printLayout.grid.columns - activePrintElement.col + 1,
    );
    updates.rowSpan = Math.min(
      Number(updates.rowSpan || activePrintElement.rowSpan),
      printLayout.grid.rows - activePrintElement.row + 1,
    );
    const candidate = { ...activePrintElement, ...updates };
    const spanInput = printSettingsModal.querySelector('[data-print-property="colSpan"]');
    spanInput?.setCustomValidity("");
    if (printLayout.elements.some((other) => other.id !== activePrintElement.id && fieldsOverlap(candidate, other))) {
      spanInput?.setCustomValidity("O tamanho informado ocupa células que já pertencem a outro elemento.");
      spanInput?.reportValidity();
      return;
    }
    Object.assign(activePrintElement, updates);
    if (printSettingsHelp) printSettingsHelp.hidden = true;
    printSettingsModal.hidden = true;
    activePrintElement = null;
    markEditorDirty();
    renderPrintBuilder();
  });
  renderPrintBuilder();
  const screenCss = ".generated-clinical-form{display:grid;column-gap:18px;row-gap:14px;color:var(--text,#111)}.generated-clinical-form label{display:grid;gap:5px;font-weight:700;min-width:0}.generated-clinical-form input,.generated-clinical-form select,.generated-clinical-form textarea{box-sizing:border-box;width:100%;padding:8px;border:1px solid var(--line,#cbd5e1);border-radius:7px;background:var(--field-bg,#fff);color:var(--text,#111)}.generated-clinical-form textarea{width:100%;min-width:100%;max-width:100%;min-height:96px;max-height:144px;resize:vertical}.generated-clinical-form input:not([type=checkbox]),.generated-clinical-form select{height:38px;min-height:38px}.generated-clinical-form select:hover{border-color:var(--primary,#2563eb);background:var(--primary-soft,#eff6ff)}.generated-clinical-form select:focus{border-color:var(--primary,#2563eb);outline:0;box-shadow:0 0 0 3px color-mix(in srgb,var(--primary,#2563eb),transparent 76%)}.generated-clinical-form select option,.generated-clinical-form select optgroup{background:var(--field-bg,#fff);color:var(--text,#111)}.generated-clinical-form select option:checked{background:var(--primary,#2563eb);color:#fff}.dark .generated-clinical-form select{color-scheme:dark}.light .generated-clinical-form select{color-scheme:light}.generated-clinical-form :disabled{cursor:not-allowed;background:var(--panel-soft,#e9eef5);color:var(--muted,#475569);opacity:1}.generated-clinical-form .provider-checkbox{display:flex;align-self:end;align-items:center;box-sizing:border-box;width:100%;height:38px;min-height:38px;padding:0 8px;border:1px solid var(--line,#cbd5e1);background:var(--field-bg,#fff);color:var(--text,#111)}.generated-clinical-form .provider-checkbox input{appearance:none;display:grid;place-content:center;flex:0 0 32px;width:32px;height:32px;min-height:32px;margin:0;border:1px solid var(--line,#cbd5e1);border-radius:5px;background:var(--field-bg,#fff)}.generated-clinical-form .provider-checkbox input:checked{border-color:var(--primary,#2563eb);background-color:var(--primary,#2563eb);background-image:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round' d='m5 12 4 4L19 6'/%3E%3C/svg%3E\");background-position:center;background-repeat:no-repeat;background-size:20px}.generated-field-affix{display:flex;align-items:center;gap:6px;width:100%;min-width:0;min-height:38px}.generated-field-affix>input{flex:1 1 auto;width:auto;min-width:0;max-width:none}.generated-field-affix>span{flex:0 0 auto;white-space:nowrap}.generated-image-field img{display:block;max-width:100%;max-height:100%;object-fit:contain}.generated-screen-title{margin:0;align-self:end;font-size:20px}.generated-screen-description,.generated-screen-text,.generated-screen-variable{align-self:center;color:var(--text,#111)}.generated-screen-help{align-self:stretch;padding:8px 10px;border-left:3px solid var(--primary,#2563eb);border-radius:5px;background:var(--primary-soft,#eff6ff);color:var(--text,#111)}.generated-screen-line{align-self:center;width:100%}.provider-select-popup{position:fixed;z-index:1000;display:grid;gap:3px;max-height:240px;padding:5px;overflow:auto;border:1px solid var(--line,#cbd5e1);border-radius:8px;background:var(--panel,#fff);box-shadow:0 12px 28px rgba(15,23,42,.24)}.provider-select-popup button{width:100%;padding:8px 10px;border:0;border-radius:6px;background:transparent;color:var(--text,#111);text-align:left;cursor:pointer}.provider-select-popup button:hover,.provider-select-popup button[aria-selected=true]{background:var(--primary-soft,#eff6ff);color:var(--primary-dark,#1d4ed8)}";
  const exclusiveCheckboxCss = ".generated-exclusive-checkboxes{display:flex;align-items:center;align-self:start;flex-wrap:wrap;gap:6px 8px;box-sizing:border-box;width:100%;max-width:100%;min-width:0;margin:0 0 4px;padding:0;border:0}.generated-exclusive-checkboxes legend{flex:0 0 auto;margin:0;padding:0;font-weight:700;color:inherit}.generated-exclusive-checkboxes>div{display:flex;align-items:center;flex:1 1 240px;flex-wrap:wrap;gap:6px;min-width:0}.generated-exclusive-checkboxes .generated-exclusive-option{display:flex;align-items:center;flex:1 1 140px;gap:5px;box-sizing:border-box;max-width:100%;min-height:38px;min-width:0;padding:3px 7px;border:1px solid var(--line,#cbd5e1);border-radius:7px;background:var(--field-bg,#fff);font-weight:600}.generated-exclusive-checkboxes .generated-exclusive-option>span{flex:0 1 auto;min-width:0;overflow-wrap:anywhere}.generated-exclusive-checkboxes .generated-exclusive-option>input[type=checkbox]{appearance:none;flex:0 0 28px;width:28px;height:28px;min-height:28px;padding:0;border-radius:5px}.generated-exclusive-checkboxes .generated-exclusive-option>input[type=checkbox]:checked{border-color:var(--primary,#2563eb);background:var(--primary,#2563eb)}.generated-exclusive-checkboxes .generated-exclusive-detail{flex:1 1 80px;width:auto;min-width:70px;max-width:100%;height:30px;min-height:30px}";
  const multipleFieldsCss = ".generated-clinical-form input,.generated-clinical-form select,.generated-clinical-form textarea{font-size:var(--field-font-size,14px);font-family:inherit}.generated-clinical-form .provider-checkbox>span{font-size:var(--field-font-size,14px)}.generated-exclusive-checkboxes legend,.generated-multiple-fields legend,.generated-boolean-field legend{font-size:calc(var(--field-font-size,14px) + 1px);font-weight:700}.generated-exclusive-checkboxes .generated-exclusive-option{font-size:var(--field-font-size,14px)}.generated-exclusive-checkboxes .generated-exclusive-option>input[type=checkbox]{flex-basis:32px;width:32px;height:32px;min-height:32px}.generated-multiple-fields,.generated-boolean-field{box-sizing:border-box;min-width:0;margin:0;padding:0;border:0}.generated-multiple-fields>div{display:flex;align-items:end;flex-wrap:wrap;gap:8px;min-width:0}.generated-multiple-item{flex:1 1 120px;min-width:90px}.generated-multiple-item>span{font-size:calc(var(--field-font-size,14px) + 1px);font-weight:700}.generated-multiple-literal{align-self:center;padding:0 2px;font-size:var(--field-font-size,14px)}.generated-boolean-field .provider-checkbox{margin-top:5px}";
  const providerSelectScript = `<script>
    (() => {
      let popup = null;
      const close = () => { popup?.remove(); popup = null; };
      const open = (select) => {
        close();
        const rect = select.getBoundingClientRect();
        popup = document.createElement("div");
        popup.className = "provider-select-popup";
        popup.style.minWidth = Math.max(180, rect.width) + "px";
        [...select.options].forEach((option) => {
          const button = document.createElement("button");
          button.type = "button";
          button.textContent = option.textContent || "Selecione";
          button.setAttribute("aria-selected", String(option.selected));
          button.addEventListener("click", () => {
            select.value = option.value;
            select.dispatchEvent(new Event("change", { bubbles: true }));
            close();
            select.focus();
          });
          popup.appendChild(button);
        });
        document.body.appendChild(popup);
        const width = popup.offsetWidth;
        const height = Math.min(popup.offsetHeight, 240);
        popup.style.left = Math.max(6, Math.min(rect.left, innerWidth - width - 6)) + "px";
        popup.style.top = (rect.bottom + height <= innerHeight - 6 ? rect.bottom + 3 : Math.max(6, rect.top - height - 3)) + "px";
      };
      document.addEventListener("mousedown", (event) => {
        const select = event.target.closest(".generated-clinical-form select");
        if (select && !select.disabled) {
          event.preventDefault();
          open(select);
          return;
        }
        if (!event.target.closest(".provider-select-popup")) close();
      });
      addEventListener("resize", close);
      addEventListener("scroll", close, true);
      const syncExclusive = (fieldset, selected = null) => {
        const readonly = fieldset.dataset.exclusiveReadonly === "true";
        fieldset.querySelectorAll("[data-exclusive-choice]").forEach((choice) => {
          if (selected && choice !== selected) choice.checked = false;
          const detail = choice.closest("label")?.querySelector("[data-exclusive-detail]");
          if (!detail) return;
          detail.disabled = readonly || !choice.checked;
          detail.tabIndex = detail.disabled ? -1 : 0;
        });
      };
      document.querySelectorAll("[data-exclusive-group]").forEach((fieldset) => syncExclusive(fieldset));
      document.addEventListener("change", (event) => {
        const choice = event.target.closest("[data-exclusive-choice]");
        if (!choice) return;
        const fieldset = choice.closest("[data-exclusive-group]");
        if (!fieldset) return;
        syncExclusive(fieldset, choice.checked ? choice : null);
        choice.closest("label")?.querySelector("[data-exclusive-detail]:not(:disabled)")?.focus();
      });
    })();
  <\/script>`;
  const addField = (overrides = {}) => {
    const position = firstFreePosition();
    formFields.push({
      id: crypto.randomUUID?.() || `field-${Date.now()}`,
      name: `campo_${formFields.length + 1}`,
      label: `Campo ${formFields.length + 1}`,
      type: "text",
      placeholder: "",
      prefix: "",
      suffix: "",
      required: false,
      readonly: false,
      options: "",
      content: "",
      displayStyle: "text",
      sourceTable: "",
      sourceValueField: "cd_valor",
      sourceDisplayField: "ds_valor",
      binding: "",
      fontSize: gridConfig.fontSize,
      fontFamily: gridConfig.fontFamily,
      fontSizeCustom: false,
      fontFamilyCustom: false,
      imageUrl: "",
      imageWidth: 240,
      imageHeight: 120,
      lockAspectRatio: true,
      imageAspectRatio: 2,
      lineColor: "#111111",
      lineWidth: 1,
      lineStyle: "solid",
      marginTop: 0,
      marginBottom: 0,
      col: position.col,
      row: position.row,
      colSpan: 1,
      rowSpan: 1,
      ...overrides,
    });
    markEditorDirty();
    renderFieldBuilder();
  };
  builder?.querySelector("[data-form-field-add]")?.addEventListener("click", () => {
    addField();
  });
  builder?.querySelector("[data-form-image-add]")?.addEventListener("click", () => addField({
    name: `imagem_${formFields.length + 1}`, label: "Imagem", type: "image", colSpan: Math.min(2, gridConfig.columns),
  }));
  const columnsInput = builder?.querySelector("[data-grid-columns]");
  const rowsInput = builder?.querySelector("[data-grid-rows]");
  const screenFontSizeInput = builder?.querySelector("[data-grid-font-size]");
  const screenFontFamilyInput = builder?.querySelector("[data-grid-font-family]");
  if (columnsInput) columnsInput.value = String(gridConfig.columns);
  if (rowsInput) rowsInput.value = String(gridConfig.rows);
  if (screenFontSizeInput) screenFontSizeInput.value = String(gridConfig.fontSize);
  if (screenFontFamilyInput) screenFontFamilyInput.value = gridConfig.fontFamily;
  columnsInput?.addEventListener("change", () => {
    requestGridResize("column", Math.max(1, Math.min(12, Number(columnsInput.value || 1))), "form");
  });
  rowsInput?.addEventListener("change", () => {
    requestGridResize("row", Math.max(1, Math.min(30, Number(rowsInput.value || 1))), "form");
  });
  screenFontSizeInput?.addEventListener("change", () => {
    gridConfig.fontSize = Math.max(7, Math.min(72, Number(screenFontSizeInput.value || 14)));
    formFields.forEach((field) => {
      if (!field.fontSizeCustom) {
        field.fontSize = gridConfig.fontSize;
        field.fontSizeCustom = false;
      }
    });
    markEditorDirty();
    renderFieldBuilder();
  });
  screenFontFamilyInput?.addEventListener("change", () => {
    gridConfig.fontFamily = screenFontFamilyInput.value || "Arial, sans-serif";
    formFields.forEach((field) => {
      if (!field.fontFamilyCustom) {
        field.fontFamily = gridConfig.fontFamily;
        field.fontFamilyCustom = false;
      }
    });
    markEditorDirty();
    renderFieldBuilder();
  });
  builder?.querySelector("[data-reusable-field-add]")?.addEventListener("click", () => {
    const picker = builder.querySelector("[data-reusable-field-picker]");
    const reusable = reusableFields.find((item) => String(item.cd_modelo_documento) === picker.value);
    const reusableSchema = reusable?.ds_projeto_tela?.formFields || [];
    reusableSchema.forEach((field) => addField({
      ...field,
      id: crypto.randomUUID?.() || `field-${Date.now()}-${Math.random()}`,
      reusableId: reusable.cd_modelo_documento,
      ...firstFreePosition(),
    }));
  });
  if (builder) renderFieldBuilder();
  const printRegenerateModal = document.querySelector("[data-print-regenerate-modal]");
  const regeneratePrintLayout = () => {
    printLayout = {
      grid: {
        columns: gridConfig.columns,
        rows: Math.max(gridConfig.rows, 1),
        fontSize: 11,
        fontFamily: "Arial, sans-serif",
      },
      elements: formFields.map(printElementFromField),
    };
    renderPrintBuilder();
    markEditorDirty();
    document.querySelector('[data-editor-tab="impressao"]')?.click();
  };
  document.querySelector("[data-generate-print-model]")?.addEventListener("click", () => {
    if (printLayout.elements.length) {
      printRegenerateModal.hidden = false;
      return;
    }
    regeneratePrintLayout();
  });
  printRegenerateModal?.querySelector("[data-print-regenerate-cancel]")?.addEventListener("click", () => {
    printRegenerateModal.hidden = true;
  });
  printRegenerateModal?.querySelector("[data-print-regenerate-confirm]")?.addEventListener("click", () => {
    printRegenerateModal.hidden = true;
    regeneratePrintLayout();
  });

  const previewModal = document.querySelector("[data-document-preview-modal]");
  const previewFrame = previewModal?.querySelector("[data-document-preview-frame]");
  const previewTitle = previewModal?.querySelector("[data-document-preview-title]");
  const previewPrint = previewModal?.querySelector("[data-document-preview-print]");
  const previewBrowserPrint = previewModal?.querySelector("[data-document-preview-browser-print]");
  const selectedTestContext = () => (
    testContexts.find((context) => String(context.id) === String(testContextSelect?.value))
    || testContexts[0]
    || { variables: {} }
  );
  const applyTestContext = (html) => {
    let result = html;
    Object.entries(selectedTestContext().variables || {}).forEach(([name, value]) => {
      const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      result = result.replace(new RegExp(`{{\\s*${escapedName}\\s*}}`, "g"), escapeHtml(value));
    });
    return result;
  };
  const renderPreview = (kind, values = {}) => {
    let html = kind === "tela" ? buildScreenHtml() : buildPrintLayoutHtml();
    let extraCss = "";
    if (kind === "impressao") {
      const headerId = form.querySelector("[name='cd_cabecalho']")?.value;
      const footerId = form.querySelector("[name='cd_rodape']")?.value;
      const header = printElements.find((item) => String(item.cd_modelo_documento) === String(headerId));
      const footer = printElements.find((item) => String(item.cd_modelo_documento) === String(footerId));
      const headerHtml = header?.ds_html_impressao || "";
      const footerHtml = footer?.ds_html_impressao || "";
      html = `<table class="preview-print-table"><thead><tr><td>${headerHtml}</td></tr></thead><tbody><tr><td class="preview-print-body">${html}</td></tr></tbody><tfoot><tr><td><div class="preview-print-footer">${footerHtml}</div></td></tr></tfoot></table>`;
      extraCss = `${header?.ds_css_impressao || ""}\n${footer?.ds_css_impressao || ""}`;
    }
    html = applyTestContext(html);
    if (kind === "impressao") {
      html = html.replace(/{{\s*documento\.pagina\s*}}/g, '<span class="document-page-variable"></span>');
      Object.entries(values).forEach(([name, value]) => {
        const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        html = html.replace(new RegExp(`{{\\s*campo\\.${escapedName}\\s*}}`, "g"), String(value ?? ""));
        html = html.replace(new RegExp(`{{\\s*${escapedName}\\s*}}`, "g"), String(value ?? ""));
      });
      html = html.replace(/{{\s*campo\.[^}]+\s*}}/g, "");
    }
    const css = kind === "tela" ? `${screenCss}${exclusiveCheckboxCss}${multipleFieldsCss}` : extraCss;
    const watermarkSvg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1400 2000'%3E%3Cg font-family='Arial,sans-serif' font-size='190' font-weight='900' fill='%2394a3b8' fill-opacity='.22' text-anchor='middle'%3E%3Ctext x='700' y='420' transform='rotate(-36 700 420)'%3ERASCUNHO%3C/text%3E%3Ctext x='700' y='1000' transform='rotate(-36 700 1000)'%3ERASCUNHO%3C/text%3E%3Ctext x='700' y='1580' transform='rotate(-36 700 1580)'%3ERASCUNHO%3C/text%3E%3C/g%3E%3C/svg%3E";
    const watermark = kind === "impressao" ? `<img class="preview-watermark" alt="Rascunho" draggable="false" src="${watermarkSvg}">` : "";
    const themeSource = getComputedStyle(document.documentElement);
    const themeVariables = ["--text", "--muted", "--line", "--field-bg", "--panel", "--panel-soft", "--primary", "--primary-soft"]
      .map((name) => `${name}:${themeSource.getPropertyValue(name).trim() || "initial"}`)
      .join(";");
    const previewBodyStyle = kind === "tela"
      ? "background:var(--panel-soft,#eef2f7);color:var(--text,#111)"
      : "background:#eef2f7;color:#111";
    const previewContent = kind === "impressao"
      ? `<div class="preview-sheet">${watermark}<div class="preview-print-area">${html}</div></div>`
      : html;
    const darkTheme = document.documentElement.classList.contains("dark") || document.body.classList.contains("dark");
    previewFrame.srcdoc = `<!doctype html><html class="${darkTheme ? "dark" : "light"}"><head><style>
      :root{${themeVariables};color-scheme:${darkTheme ? "dark" : "light"}}
      body{margin:0;padding:18px;${previewBodyStyle};font:14px Arial}
      .preview-sheet{position:relative;box-sizing:border-box;width:210mm;min-height:297mm;margin:0 auto;padding:4mm;overflow:hidden;background:#fff;box-shadow:0 8px 28px rgba(15,23,42,.25)}
      .preview-print-area{position:relative;width:100%;height:289mm;overflow:hidden}
      .preview-watermark{position:absolute;inset:5%;z-index:20;width:90%;height:90%;object-fit:contain;pointer-events:none;user-select:none;-webkit-user-select:none}
      .preview-print-table{width:100%;height:289mm;min-height:289mm;margin:0;border-collapse:collapse;table-layout:fixed;background:#fff}.preview-print-table td{padding:0;border:0;vertical-align:top}.preview-print-table thead{display:table-header-group}.preview-print-table tfoot{display:table-footer-group}.preview-print-footer{display:flex;align-items:flex-end;justify-content:space-between;gap:10px;min-height:38px}.preview-print-footer>:first-child{flex:1}.document-page-variable::after{content:counter(page)}
      @media print{@page{size:A4;margin:4mm}.preview-sheet{width:auto;min-height:0;margin:0;padding:0;overflow:visible;box-shadow:none}.preview-print-area{width:100%;height:289mm;overflow:hidden}.preview-print-table{width:100%;height:289mm;min-height:0;margin:0}.preview-print-table thead{display:table-header-group!important}.preview-print-table tfoot{display:table-footer-group!important}.preview-print-body{height:auto}.preview-watermark{position:fixed;inset:5%;width:90%;height:90%}body{padding:0;background:#fff}}
      ${css}
    </style></head><body>${previewContent}${kind === "tela" ? providerSelectScript : ""}</body></html>`;
    previewTitle.textContent = kind === "tela" ? "Formulário visto pelo prestador" : "Relatório / impressão em rascunho";
    previewPrint.hidden = kind !== "tela";
    previewBrowserPrint.hidden = kind === "tela";
    previewModal.hidden = false;
  };
  document.querySelectorAll("[data-document-preview]").forEach((button) => {
    button.addEventListener("click", () => renderPreview(button.dataset.documentPreview));
  });
  document.querySelector("[data-document-preview-active]")?.addEventListener("click", () => {
    const activeKind = document.querySelector("[data-editor-tab].active")?.dataset.editorTab
      || (form.dataset.documentElement === "CAMPO" ? "tela" : "impressao");
    renderPreview(activeKind);
  });
  document.querySelectorAll("[data-document-preview-close]").forEach((button) => {
    button.addEventListener("click", () => { previewModal.hidden = true; });
  });
  previewPrint?.addEventListener("click", () => {
    const values = {};
    previewFrame.contentDocument?.querySelectorAll("[data-document-field][name]").forEach((field) => {
      const name = field.name.replace(/^campo_/, "");
      if (field.matches("[data-exclusive-choice]")) {
        if (field.checked) values[name] = field.value;
        else if (!(name in values)) values[name] = "";
        return;
      }
      values[name] = field.type === "checkbox" ? (field.checked ? "Sim" : "Não") : field.value;
    });
    renderPreview("impressao", values);
  });
  previewBrowserPrint?.addEventListener("click", () => {
    previewFrame.contentWindow?.focus();
    previewFrame.contentWindow?.print();
  });
  document.addEventListener("keydown", (event) => {
    if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "p" || previewModal?.hidden) return;
    event.preventDefault();
    previewFrame.contentWindow?.focus();
    previewFrame.contentWindow?.print();
  });
  const restoreEditorState = (serializedState, message) => {
    const state = JSON.parse(serializedState);
    restoringHistory = true;
    gridConfig.columns = state.gridConfig.columns;
    gridConfig.rows = state.gridConfig.rows;
    gridConfig.fontSize = state.gridConfig.fontSize || 14;
    gridConfig.fontFamily = state.gridConfig.fontFamily || "Arial, sans-serif";
    formFields = state.formFields;
    printLayout = state.printLayout;
    if (customVariableNameInput) customVariableNameInput.value = state.customVariableName || "";
    if (customVariableExpressionInput) customVariableExpressionInput.value = state.customVariableExpression || "";
    activateEditorTab(state.activeTab || "tela");
    updateGridInputs();
    renderFieldBuilder();
    renderPrintBuilder();
    historyCurrent = captureEditorState();
    restoringHistory = false;
    setEditorDirty();
    updateHistoryButtons();
    showHistoryIndicator(message);
  };
  const undoEditorAction = () => {
    if (!undoStack.length) return;
    redoStack.push(historyCurrent);
    restoreEditorState(undoStack.pop(), "Ação desfeita");
  };
  const redoEditorAction = () => {
    if (!redoStack.length) return;
    undoStack.push(historyCurrent);
    restoreEditorState(redoStack.pop(), "Ação refeita");
  };
  const clearDocumentEditor = () => {
    closeAllVisibleCellMenus();
    form.querySelectorAll("input:not([type='hidden']), select, textarea").forEach((field) => {
      if (field.name === "sn_ativo") {
        if (field.type === "checkbox") field.checked = true;
        else field.value = "True";
        return;
      }
      if (field.matches("[data-custom-variable-name], [data-custom-variable-expression]")) {
        field.value = "";
        return;
      }
      if (field.type === "checkbox" || field.type === "radio") {
        field.checked = false;
      } else if (field instanceof HTMLSelectElement) {
        if (field.multiple) {
          [...field.options].forEach((option) => { option.selected = false; });
        } else {
          field.selectedIndex = 0;
        }
      } else if (!field.readOnly) {
        field.value = "";
      }
    });
    gridConfig.columns = 2;
    gridConfig.rows = 4;
    gridConfig.fontSize = 14;
    gridConfig.fontFamily = "Arial, sans-serif";
    formFields = [];
    printLayout = {
      grid: { columns: 2, rows: 4, fontSize: 11, fontFamily: "Arial, sans-serif" },
      elements: [],
    };
    if (fieldList) {
      updateGridInputs();
      renderFieldBuilder();
    }
    renderPrintBuilder();
    if (customVariableTestResult) customVariableTestResult.hidden = true;
    registerHistoryState();
    form.dataset.dirty = "false";
    form.dataset.submitting = "false";
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = true;
    updateHistoryButtons();
    showHistoryIndicator("Editor limpo");
    const indexUrl = form.dataset.editorIndexUrl;
    deleteEditorDraft();
    if (indexUrl) {
      internalEditorNavigation = true;
      window.location.assign(indexUrl);
    }
  };
  const documentEditorHasContent = () => (
    formFields.length > 0
    || printLayout.elements.length > 0
    || Boolean(form.querySelector("[name='nm_modelo']")?.value.trim())
    || Boolean(form.querySelector("[name='ds_alteracoes_versao']")?.value.trim())
    || Boolean(customVariableNameInput?.value.trim())
    || Boolean(customVariableExpressionInput?.value.trim())
  );
  document.querySelector('[data-action="clear"]')?.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (form.dataset.dirty === "true" || documentEditorHasContent()) {
      documentClearModal.hidden = false;
      return;
    }
    clearDocumentEditor();
  });
  documentClearModal?.querySelector("[data-document-clear-cancel]")?.addEventListener("click", () => {
    documentClearModal.hidden = true;
  });
  documentClearModal?.querySelector("[data-document-clear-discard]")?.addEventListener("click", () => {
    documentClearModal.hidden = true;
    clearDocumentEditor();
  });
  documentClearModal?.querySelector("[data-document-clear-save]")?.addEventListener("click", () => {
    documentClearModal.hidden = true;
    form.requestSubmit();
  });
  undoButton?.addEventListener("click", undoEditorAction);
  redoButton?.addEventListener("click", redoEditorAction);
  document.addEventListener("keydown", (event) => {
    if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
    if (event.target.closest("input, textarea, [contenteditable='true']")) return;
    const key = event.key.toLowerCase();
    if (key === "z" && !event.shiftKey) {
      event.preventDefault();
      undoEditorAction();
    } else if (key === "y" || (key === "z" && event.shiftKey)) {
      event.preventDefault();
      redoEditorAction();
    }
  });

  function activateEditorTab(selected) {
    document.querySelectorAll("[data-editor-tab]").forEach((item) => {
      const active = item.dataset.editorTab === selected;
      item.classList.toggle("active", active);
      item.classList.toggle("button-primary", active);
      item.classList.toggle("button-secondary", !active);
    });
    document.querySelectorAll("[data-editor-pane]").forEach((pane) => {
      const active = pane.dataset.editorPane === selected;
      pane.hidden = !active;
      pane.classList.toggle("active", active);
    });
    editors[selected]?.refresh();
  }
  document.querySelectorAll("[data-editor-tab]").forEach((button) => {
    button.addEventListener("click", () => activateEditorTab(button.dataset.editorTab));
  });

  form.addEventListener("submit", () => {
    form.dataset.submitting = "true";
    form.elements.ds_html_tela.value = buildScreenHtml();
    form.elements.ds_css_tela.value = screenCss;
    const customVariableName = form.querySelector("[data-custom-variable-name]")?.value || "";
    const customVariableExpression = form.querySelector("[data-custom-variable-expression]")?.value || "";
    form.elements.ds_projeto_tela.value = JSON.stringify({
      grid: gridConfig,
      formFields,
      ...(form.dataset.documentElement === "VARIAVEL"
        ? { customVariable: { name: normalizeName(customVariableName), expression: customVariableExpression } }
        : {}),
    });
    form.elements.ds_html_impressao.value = buildPrintLayoutHtml();
    form.elements.ds_css_impressao.value = "";
    form.elements.ds_projeto_impressao.value = JSON.stringify({ printLayout });
  });

  const newMenu = document.querySelector("[data-document-new-menu]");
  const newOptions = newMenu?.querySelector("[data-document-new-options]");
  const studio = document.querySelector(".document-studio");
  const library = studio?.querySelector(".document-library");
  const history = studio?.querySelector("[data-document-history]");
  const libraryToggle = studio?.querySelector("[data-document-library-toggle]");
  const libraryViewOptions = studio?.querySelector("[data-document-library-view-options]");
  const libraryScroll = studio?.querySelector(".document-library-scroll");
  const libraryFolderForm = studio?.querySelector("[data-document-folder-form]");
  if (history && library) library.appendChild(history);
  libraryToggle?.addEventListener("click", () => {
    libraryViewOptions.hidden = !libraryViewOptions.hidden;
    libraryToggle.setAttribute("aria-expanded", libraryViewOptions.hidden ? "false" : "true");
  });
  libraryViewOptions?.querySelectorAll("[data-document-side-view]").forEach((button) => {
    button.addEventListener("click", () => {
      const showHistory = button.dataset.documentSideView === "history";
      if (history) history.hidden = !showHistory;
      if (libraryScroll) libraryScroll.hidden = showHistory;
      if (libraryFolderForm) libraryFolderForm.hidden = true;
      newMenu.hidden = showHistory;
      library?.classList.toggle("show-history", showHistory);
      libraryToggle.querySelector("[data-document-library-label]").textContent = showHistory ? "Histórico de versões" : "Biblioteca";
      libraryViewOptions.hidden = true;
    });
  });
  newMenu?.querySelector("[data-document-new-toggle]")?.addEventListener("click", () => {
    newOptions.hidden = !newOptions.hidden;
  });
  document.querySelector("[data-document-create-folder]")?.addEventListener("click", () => {
    const folderForm = document.querySelector("[data-document-folder-form]");
    folderForm.hidden = false;
    folderForm.querySelector("input[name='nm_pasta']")?.focus();
    newOptions.hidden = true;
  });

  const contextMenu = document.querySelector("[data-document-context-menu]");
  const actionForm = document.querySelector("[data-library-action-form]");
  const moveModal = document.querySelector("[data-document-move-modal]");
  const moveDestination = moveModal?.querySelector("[data-document-move-destination]");
  const copyModal = document.querySelector("[data-document-copy-modal]");
  const copyDestination = copyModal?.querySelector("[data-document-copy-destination]");
  const copyName = copyModal?.querySelector("[data-document-copy-name]");
  const leaveModal = document.querySelector("[data-document-leave-modal]");
  const leaveSaveButton = leaveModal?.querySelector("[data-document-leave-save]");
  if (leaveSaveButton) leaveSaveButton.hidden = document.body.dataset.canSave !== "true";
  let pendingDocumentUrl = "";
  let contextItem = null;
  const selectLibraryFolder = (item) => {
    const folder = item.closest(".document-folder-node");
    document.querySelectorAll(".document-folder-node.selected, .document-root-link.selected").forEach((selected) => {
      selected.classList.remove("selected");
    });
    if (folder) {
      folder.open = !folder.open;
      folder.classList.add("selected");
    } else {
      item.classList.add("selected");
    }
    const folderId = item.dataset.itemId || "";
    document.querySelectorAll('input[name="pasta_selecionada"]').forEach((input) => {
      if (input.closest("[data-document-editor-form]")?.dataset.documentModelId) return;
      input.value = folderId;
    });
    newMenu?.querySelectorAll('a[href*="novo="]').forEach((link) => {
      const url = new URL(link.href, window.location.origin);
      if (folderId) url.searchParams.set("pasta", folderId);
      else url.searchParams.delete("pasta");
      link.href = `${url.pathname}${url.search}`;
    });
  };
  const requestDocumentNavigation = (event, item) => {
    const destination = new URL(item.href, window.location.origin);
    if (destination.pathname === window.location.pathname && destination.search === window.location.search) {
      event.preventDefault();
      return;
    }
    if (form.dataset.dirty !== "true") return;
    event.preventDefault();
    pendingDocumentUrl = destination.href;
    leaveModal.hidden = false;
  };
  document.querySelectorAll("[data-library-item]").forEach((item) => {
    if (["CAMPO", "BLOCO", "VARIAVEL"].includes(item.dataset.elementType)) {
      item.draggable = true;
      item.title = "Arraste para uma célula do editor";
      item.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/document-library-reusable", item.dataset.itemId);
        event.dataTransfer.setData("text/document-library-element-type", item.dataset.elementType);
        event.dataTransfer.effectAllowed = "copy";
      });
    }
    if (item.dataset.itemType === "pasta") {
      item.addEventListener("click", (event) => {
        event.preventDefault();
        selectLibraryFolder(item);
      });
    } else if (item.dataset.itemType === "documento") {
      item.addEventListener("click", (event) => requestDocumentNavigation(event, item));
    }
    item.addEventListener("contextmenu", (event) => {
      event.preventDefault();
      contextItem = item;
      contextMenu.querySelectorAll("[data-context-action]").forEach((button) => {
        const action = button.dataset.contextAction;
        button.hidden = action === "copiar"
          ? item.dataset.itemType !== "documento"
          : item.dataset.protected === "true";
      });
      if (![...contextMenu.querySelectorAll("[data-context-action]")].some((button) => !button.hidden)) return;
      positionMenuInViewport(contextMenu, event);
    });
  });
  contextMenu?.addEventListener("click", (event) => {
    const action = event.target.closest("[data-context-action]")?.dataset.contextAction;
    if (!action || !contextItem) return;
    if (action === "excluir" && !window.confirm(`Excluir ${contextItem.dataset.itemName || "este item"}?`)) return;
    actionForm.elements.acao.value = action;
    actionForm.elements.tipo_item.value = contextItem.dataset.itemType;
    actionForm.elements.item_id.value = contextItem.dataset.itemId;
    if (action === "renomear") {
      const name = window.prompt("Novo nome", contextItem.dataset.itemName || "");
      if (!name) return;
      actionForm.elements.novo_nome.value = name;
    }
    if (action === "mover") {
      moveModal.hidden = false;
      moveDestination.focus();
      contextMenu.hidden = true;
      return;
    }
    if (action === "copiar") {
      copyName.value = contextItem.dataset.itemName || "";
      copyDestination.value = "";
      copyModal.hidden = false;
      copyName.focus();
      contextMenu.hidden = true;
      return;
    }
    actionForm.submit();
  });
  moveModal?.querySelector("[data-document-move-cancel]")?.addEventListener("click", () => {
    moveModal.hidden = true;
  });
  moveModal?.querySelector("[data-document-move-confirm]")?.addEventListener("click", () => {
    if (!contextItem) return;
    actionForm.elements.acao.value = "mover";
    actionForm.elements.tipo_item.value = contextItem.dataset.itemType;
    actionForm.elements.item_id.value = contextItem.dataset.itemId;
    actionForm.elements.destino_id.value = moveDestination.value;
    actionForm.submit();
  });
  copyModal?.querySelector("[data-document-copy-cancel]")?.addEventListener("click", () => {
    copyModal.hidden = true;
  });
  copyModal?.querySelector("[data-document-copy-confirm]")?.addEventListener("click", () => {
    if (!contextItem || contextItem.dataset.itemType !== "documento") return;
    actionForm.elements.acao.value = "copiar";
    actionForm.elements.tipo_item.value = "documento";
    actionForm.elements.item_id.value = contextItem.dataset.itemId;
    actionForm.elements.novo_nome.value = copyName.value.trim();
    actionForm.elements.destino_id.value = copyDestination.value;
    actionForm.submit();
  });
  document.querySelector("[data-document-company-root]")?.addEventListener("click", (event) => {
    event.preventDefault();
    document.querySelectorAll(".document-folder-node.selected").forEach((selected) => selected.classList.remove("selected"));
    event.currentTarget.closest(".document-company-root")?.classList.add("selected");
    document.querySelectorAll('input[name="pasta_selecionada"]').forEach((input) => {
      if (!input.closest("[data-document-editor-form]")?.dataset.documentModelId) input.value = "";
    });
  });
  leaveModal?.querySelector("[data-document-leave-cancel]")?.addEventListener("click", () => {
    pendingDocumentUrl = "";
    leaveModal.hidden = true;
  });
  leaveModal?.querySelector("[data-document-leave-discard]")?.addEventListener("click", () => {
    if (!pendingDocumentUrl) return;
    form.dataset.dirty = "false";
    deleteEditorDraft().finally(() => {
      internalEditorNavigation = true;
      window.location.href = pendingDocumentUrl;
    });
  });
  leaveModal?.querySelector("[data-document-leave-save]")?.addEventListener("click", () => {
    if (!pendingDocumentUrl) return;
    const destination = new URL(pendingDocumentUrl, window.location.origin);
    form.elements.return_to.value = `${destination.pathname}${destination.search}`;
    leaveModal.hidden = true;
    form.requestSubmit();
  });
  window.addEventListener("beforeunload", (event) => {
    if (!draftSyncPending || internalEditorNavigation || form.dataset.submitting === "true") return;
    event.preventDefault();
    event.returnValue = "";
  });
  document.addEventListener("click", (event) => {
    const internalNavigation = event.target.closest("a[href]");
    if (!internalNavigation || internalNavigation.target === "_blank" || internalNavigation.hasAttribute("download")) return;
    const destination = new URL(internalNavigation.href, window.location.origin);
    if (destination.origin !== window.location.origin || form.dataset.dirty !== "true") return;
    internalEditorNavigation = true;
    syncEditorDraft({ keepalive: true });
  }, true);
  document.addEventListener("click", (event) => {
    if (contextMenu && !contextMenu.contains(event.target)) contextMenu.hidden = true;
    if (gridContextMenu && !gridContextMenu.contains(event.target)) gridContextMenu.hidden = true;
    if (newMenu && !newMenu.contains(event.target)) newOptions.hidden = true;
    if (libraryViewOptions && !libraryToggle?.contains(event.target) && !libraryViewOptions.contains(event.target)) {
      libraryViewOptions.hidden = true;
    }
    if (!event.target.closest(".document-cell-create-menu, .document-cell-fields-menu, [data-cell-create-toggle], [data-print-create-toggle]")) {
      closeAllVisibleCellMenus();
    }
  });
  document.addEventListener("pointerdown", (event) => {
    if (event.target.closest("[data-cell-menu-portal], [data-cell-create-toggle], [data-print-create-toggle]")) return;
    closeAllVisibleCellMenus();
  }, true);
  if (previewModal?.parentElement !== document.body) document.body.appendChild(previewModal);
  if (moveModal?.parentElement !== document.body) document.body.appendChild(moveModal);
  if (copyModal?.parentElement !== document.body) document.body.appendChild(copyModal);
  if (gridDeleteModal?.parentElement !== document.body) document.body.appendChild(gridDeleteModal);
  if (leaveModal?.parentElement !== document.body) document.body.appendChild(leaveModal);
  if (printRegenerateModal?.parentElement !== document.body) document.body.appendChild(printRegenerateModal);
  if (customVariableHelpModal?.parentElement !== document.body) document.body.appendChild(customVariableHelpModal);
  if (systemModelCopyModal?.parentElement !== document.body) document.body.appendChild(systemModelCopyModal);
  if (documentClearModal?.parentElement !== document.body) document.body.appendChild(documentClearModal);
  if (settingsModal?.parentElement !== document.body) document.body.appendChild(settingsModal);
  if (printSettingsModal?.parentElement !== document.body) document.body.appendChild(printSettingsModal);
  if (undoButton) undoButton.hidden = false;
  if (redoButton) redoButton.hidden = false;
  historyCurrent = captureEditorState();
  updateHistoryButtons();
  restoreEditorDraft();
})();
