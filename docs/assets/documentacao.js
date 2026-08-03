(() => {
  const state = { topics: [], activeId: "", query: "" };
  const content = document.querySelector("[data-topic-content]");
  const navigation = document.querySelector("[data-docs-navigation]");
  const search = document.querySelector("[data-docs-search]");
  const searchStatus = document.querySelector("[data-search-status]");
  const version = document.querySelector("[data-docs-version]");
  const themeButton = document.querySelector("[data-theme-toggle]");

  const escapeHTML = (value) => String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const normalize = (value) => String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR");

  function inlineMarkdown(value) {
    return escapeHTML(value)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\[([^\]]+)]\((https?:\/\/[^\s)]+|#[^\s)]+|\.\.?\/[^\s)]+)\)/g, '<a href="$2">$1</a>');
  }

  function renderMarkdown(markdown) {
    const lines = String(markdown || "").replace(/\r/g, "").split("\n");
    const output = [];
    let listType = "";
    let code = false;
    const closeList = () => {
      if (!listType) return;
      output.push(`</${listType}>`);
      listType = "";
    };
    lines.forEach((line) => {
      if (line.startsWith("```")) {
        closeList();
        output.push(code ? "</code></pre>" : "<pre><code>");
        code = !code;
        return;
      }
      if (code) {
        output.push(`${escapeHTML(line)}\n`);
        return;
      }
      if (!line.trim()) {
        closeList();
        return;
      }
      const heading = line.match(/^(#{2,3})\s+(.+)$/);
      if (heading) {
        closeList();
        const level = heading[1].length;
        output.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
        return;
      }
      const unordered = line.match(/^[-*]\s+(.+)$/);
      const ordered = line.match(/^\d+\.\s+(.+)$/);
      if (unordered || ordered) {
        const nextType = unordered ? "ul" : "ol";
        if (listType !== nextType) {
          closeList();
          listType = nextType;
          output.push(`<${listType}>`);
        }
        output.push(`<li>${inlineMarkdown((unordered || ordered)[1])}</li>`);
        return;
      }
      if (line.startsWith("> ")) {
        closeList();
        output.push(`<blockquote>${inlineMarkdown(line.slice(2))}</blockquote>`);
        return;
      }
      closeList();
      output.push(`<p>${inlineMarkdown(line)}</p>`);
    });
    closeList();
    if (code) output.push("</code></pre>");
    return output.join("\n");
  }

  function topicMatches(topic, query) {
    if (!query) return true;
    const searchable = [topic.title, topic.summary, topic.category, topic.body, ...(topic.keywords || [])].join(" ");
    return normalize(searchable).includes(normalize(query));
  }

  function groupedTopics(topics) {
    return topics.reduce((groups, topic) => {
      groups[topic.category] = groups[topic.category] || [];
      groups[topic.category].push(topic);
      return groups;
    }, {});
  }

  function renderNavigation() {
    const visible = state.topics.filter((topic) => topicMatches(topic, state.query));
    const groups = groupedTopics(visible);
    navigation.innerHTML = Object.entries(groups).map(([category, topics]) => `
      <details class="docs-nav-group" open>
        <summary>${escapeHTML(category)} <span>(${topics.length})</span></summary>
        <div>
          ${topics.map((topic) => `
            <a class="docs-nav-link${topic.id === state.activeId ? " active" : ""}" href="#${escapeHTML(topic.id)}" data-topic-link="${escapeHTML(topic.id)}">
              <span>${escapeHTML(topic.title)}</span>
              <small>${escapeHTML(topic.summary)}</small>
            </a>
          `).join("")}
        </div>
      </details>
    `).join("") || '<div class="docs-empty">Nenhum tópico corresponde à busca.</div>';
    searchStatus.textContent = state.query
      ? `${visible.length} tópico(s) encontrado(s)`
      : `${state.topics.length} tópico(s) disponíveis`;
  }

  function renderTopic(topic) {
    if (!topic) {
      content.innerHTML = '<div class="docs-empty">Tópico não encontrado. Selecione outro item na biblioteca.</div>';
      return;
    }
    state.activeId = topic.id;
    const index = state.topics.findIndex((item) => item.id === topic.id);
    const previous = state.topics[index - 1];
    const next = state.topics[index + 1];
    content.innerHTML = `
      <div class="topic-breadcrumb">Biblioteca / ${escapeHTML(topic.category)}</div>
      <header class="topic-header">
        <h1>${escapeHTML(topic.title)}</h1>
        <p class="topic-summary">${escapeHTML(topic.summary)}</p>
        <div class="topic-meta">
          <span>Atualizado em <time datetime="${escapeHTML(topic.updatedAt)}">${new Date(`${topic.updatedAt}T12:00:00`).toLocaleDateString("pt-BR")}</time></span>
          <span>Por <strong>${escapeHTML(topic.updatedBy)}</strong></span>
          <span>Revisão ${escapeHTML(topic.revision || "1")}</span>
        </div>
      </header>
      <div class="topic-body">${renderMarkdown(topic.body)}</div>
      <footer class="topic-footer">
        ${previous ? `<a class="topic-pagination" href="#${escapeHTML(previous.id)}"><small>Anterior</small><strong>← ${escapeHTML(previous.title)}</strong></a>` : "<span></span>"}
        ${next ? `<a class="topic-pagination" href="#${escapeHTML(next.id)}"><small>Próximo</small><strong>${escapeHTML(next.title)} →</strong></a>` : ""}
      </footer>
    `;
    document.title = `${topic.title} · Biblioteca Celeris`;
    renderNavigation();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function openFromHash() {
    const id = decodeURIComponent(window.location.hash.slice(1)) || state.topics[0]?.id;
    renderTopic(state.topics.find((topic) => topic.id === id) || state.topics[0]);
  }

  function setupTheme() {
    const stored = localStorage.getItem("celeris-docs-theme");
    const dark = stored ? stored === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    const sunIcon = `
      <svg xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true">
        <circle cx="12" cy="12" r="4"/>
        <path d="M12 2v2"/>
        <path d="M12 20v2"/>
        <path d="m4.93 4.93 1.41 1.41"/>
        <path d="m17.66 17.66 1.41 1.41"/>
        <path d="M2 12h2"/>
        <path d="M20 12h2"/>
        <path d="m6.34 17.66-1.41 1.41"/>
        <path d="m19.07 4.93-1.41 1.41"/>
      </svg>
    `;
    const moonIcon = `
      <svg xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true">
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9"/>
      </svg>
    `;

    document.documentElement.classList.toggle("dark", dark);
    themeButton.innerHTML = dark ? sunIcon : moonIcon;
    themeButton.addEventListener("click", () => {
      const enabled = document.documentElement.classList.toggle("dark");
      localStorage.setItem("celeris-docs-theme", enabled ? "dark" : "light");
      themeButton.textContent = enabled ? sunIcon: moonIcon;
    });
  }

  search.addEventListener("input", () => {
    state.query = search.value.trim();
    renderNavigation();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && !event.target.matches("input, textarea")) {
      event.preventDefault();
      search.focus();
    }
  });
  window.addEventListener("hashchange", openFromHash);
  setupTheme();

  fetch("data/topics.json", { cache: "no-cache" })
    .then((response) => {
      if (!response.ok) throw new Error(`Falha ao carregar conteúdo (${response.status})`);
      return response.json();
    })
    .then((library) => {
      state.topics = [...(library.topics || [])].sort((left, right) => (left.order || 0) - (right.order || 0));
      version.textContent = `${library.site?.version || "1.0"} · ${state.topics.length} tópicos`;
      renderNavigation();
      openFromHash();
    })
    .catch((error) => {
      content.innerHTML = `<div class="docs-empty"><strong>Não foi possível abrir a biblioteca.</strong><p>${escapeHTML(error.message)}</p><p>Use um servidor HTTP local; navegadores bloqueiam JSON aberto diretamente por arquivo.</p></div>`;
    });
})();
