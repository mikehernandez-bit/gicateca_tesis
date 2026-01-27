/*
Archivo: app/static/js/references.js
Propósito: Gestiona la vista de detalle de referencias.
Fix: Botones funcionando + Calibración matemática "Quirúrgica" (Scroll 100px vs Ojo 90px).
*/

(function () {
  const app = document.getElementById("referencesApp");
  if (!app) return;

  const gridView = document.getElementById("refs-grid-view");
  const detailView = document.getElementById("refs-detail-view");
  const gridEl = document.getElementById("refs-grid");
  const gridEmptyEl = document.getElementById("refs-grid-empty");
  const gridSearchEl = document.getElementById("refs-search");
  const backBtn = document.getElementById("refs-back-btn");
  const breadcrumbEl = document.getElementById("ref-breadcrumb");

  const sideSearchEl = document.getElementById("refs-side-search");
  const sideListEl = document.getElementById("refs-side-list");

  const drawerEl = document.getElementById("refs-drawer");
  const drawerBackdrop = document.getElementById("refs-drawer-backdrop");
  const drawerSearchEl = document.getElementById("refs-drawer-search");
  const drawerListEl = document.getElementById("refs-drawer-list");
  const openDrawerBtn = document.getElementById("refs-open-drawer");
  const closeDrawerBtn = document.getElementById("refs-close-drawer");

  const detailLoader = document.getElementById("ref-detail-loader");
  const detailTitle = document.getElementById("ref-title");
  const detailTags = document.getElementById("ref-tags");
  const detailDesc = document.getElementById("ref-desc");
  const detailNote = document.getElementById("ref-note");
  const detailContent = document.getElementById("ref-content");
  const detailSources = document.getElementById("ref-sources");
  const tocContainer = document.getElementById("ref-toc");
  const tocListEl = document.getElementById("ref-toc-list");

  const routingEnabled = app.dataset.routing !== "false";
  const basePath = app.dataset.base || window.location.pathname || "/referencias";

  // Bandera para evitar conflictos visuales mientras viaja el scroll
  let isManualScroll = false;

  const state = {
    uni: (app.dataset.uni || "unac").toLowerCase(),
    items: [],
    filtered: [],
    order: [],
    activeId: null,
    observer: null,
  };

  function parseQuery() {
    const params = new URLSearchParams(window.location.search);
    const uni = (params.get("uni") || state.uni || "unac").toLowerCase();
    const ref = routingEnabled ? params.get("ref") : null;
    return { uni, ref };
  }

  async function fetchIndex(uni) {
    const res = await fetch(`/api/referencias?uni=${encodeURIComponent(uni)}`);
    if (!res.ok) throw new Error("Error cargando referencias.");
    return await res.json();
  }

  async function fetchDetail(refId, uni) {
    const res = await fetch(`/api/referencias/${encodeURIComponent(refId)}?uni=${encodeURIComponent(uni)}`);
    if (!res.ok) throw new Error("Norma no encontrada.");
    return await res.json();
  }

  function escapeHtml(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function applyItalicMarkup(text) {
    const escaped = escapeHtml(text);
    return escaped.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  }

  function toggleViews(showDetail) {
    gridView.classList.toggle("hidden", showDetail);
    detailView.classList.toggle("hidden", !showDetail);
  }

  function setDetailLoading(isLoading) {
    detailLoader.classList.toggle("hidden", !isLoading);
    detailContent.classList.toggle("hidden", isLoading);
  }

  function toggleDrawer(show) {
    if (!drawerEl) return;
    drawerEl.classList.toggle("hidden", !show);
    drawerEl.setAttribute("aria-hidden", show ? "false" : "true");
  }

  function syncSearchValue(value, source) {
    const inputs = [gridSearchEl, sideSearchEl, drawerSearchEl];
    inputs.forEach(input => {
      if (!input || input === source) return;
      input.value = value;
    });
  }

  function renderTags(tags) {
    detailTags.innerHTML = "";
    (tags || []).forEach(tag => {
      const chip = document.createElement("span");
      chip.className = "ref-chip";
      chip.textContent = tag;
      detailTags.appendChild(chip);
    });
  }

  // --- RENDERIZADO DE BLOQUES ---
  function renderListBlock(item) { const block = document.createElement("div"); block.className = "ref-block"; if (item.titulo) { const title = document.createElement("div"); title.className = "ref-block-title"; title.textContent = item.titulo; block.appendChild(title); } const list = document.createElement("ul"); list.className = "ref-bullets"; (item.items || []).forEach(text => { const li = document.createElement("li"); li.textContent = text; list.appendChild(li); }); block.appendChild(list); return block; }
  function renderChecklist(item) { const list = document.createElement("ul"); list.className = "ref-check"; (item.items || []).forEach(text => { const li = document.createElement("li"); const checkbox = document.createElement("input"); checkbox.type = "checkbox"; checkbox.disabled = true; const span = document.createElement("span"); span.textContent = text; li.appendChild(checkbox); li.appendChild(span); list.appendChild(li); }); return list; }
  function renderSampleText(item) { const block = document.createElement("div"); block.className = "ref-sample"; const label = document.createElement("div"); label.className = "ref-sample-label"; label.textContent = item.etiqueta || "Ejemplo"; block.appendChild(label); (item.items || []).forEach(line => { const row = document.createElement("div"); row.className = "ref-sample-line"; row.innerHTML = applyItalicMarkup(line); block.appendChild(row); }); return block; }
  function renderFormattedReferences(item) { const block = document.createElement("div"); block.className = "ref-block"; if (item.etiqueta) { const title = document.createElement("div"); title.className = "ref-block-title"; title.textContent = item.etiqueta; block.appendChild(title); } const list = document.createElement("ul"); list.className = "ref-apa7"; (item.lineas || item.items || item.contenido || []).forEach(line => { const li = document.createElement("li"); li.innerHTML = applyItalicMarkup(line); list.appendChild(li); }); block.appendChild(list); return block; }
  function renderNumericReferences(item) { const block = document.createElement("div"); block.className = "ref-block"; if (item.etiqueta) { const title = document.createElement("div"); title.className = "ref-block-title"; title.textContent = item.etiqueta; block.appendChild(title); } const container = document.createElement("div"); container.className = "ref-numeric"; (item.items || item.contenido || []).forEach((entry, idx) => { const row = document.createElement("div"); row.className = "ref-row"; const num = document.createElement("div"); num.className = "ref-num"; const label = entry.n || entry.numero || entry.indice || idx + 1; num.textContent = `[${label}]`; const text = document.createElement("div"); text.className = "ref-text"; text.innerHTML = applyItalicMarkup(entry.texto || entry.contenido || entry); row.appendChild(num); row.appendChild(text); container.appendChild(row); }); block.appendChild(container); return block; }
  
  function renderItem(item) {
    const tipo = (item.tipo || "texto").toLowerCase();
    const etiqueta = item.etiqueta || "";
    const contenido = item.contenido || "";
    if (tipo === "lista") return renderListBlock(item);
    if (tipo === "checklist") return renderChecklist(item);
    if (tipo === "muestra_cita_texto") return renderSampleText(item);
    if (tipo === "formato") { const block = document.createElement("div"); block.className = "ref-format"; if (etiqueta) { const label = document.createElement("div"); label.className = "label"; label.textContent = etiqueta; block.appendChild(label); } const pre = document.createElement("pre"); pre.innerHTML = applyItalicMarkup(contenido); block.appendChild(pre); return block; }
    if (tipo === "ejemplo") { const block = document.createElement("div"); block.className = "ref-example"; const label = document.createElement("div"); label.className = "label"; label.textContent = etiqueta || "Ejemplo"; block.appendChild(label); const pre = document.createElement("pre"); pre.innerHTML = applyItalicMarkup(contenido); block.appendChild(pre); return block; }
    if (tipo === "nota") { const block = document.createElement("div"); block.className = "ref-note"; block.textContent = contenido; return block; }
    if (tipo === "link") { const href = item.url || contenido; const link = document.createElement("a"); link.href = href; link.target = "_blank"; link.rel = "noopener"; link.className = "text-indigo-600 hover:underline text-sm"; link.textContent = `${etiqueta ? etiqueta + ": " : ""}${contenido}`; return link; }
    if (tipo === "referencias_formateadas") return renderFormattedReferences(item);
    if (tipo === "referencias_numeradas") return renderNumericReferences(item);
    const paragraph = document.createElement("p"); paragraph.className = "ref-text"; paragraph.textContent = contenido; return paragraph;
  }

  // --- 1. SETUP DEL SCROLL SPY (EL OJO) ---
  function setupScrollSpy(sections) {
    if (!tocListEl) return;
    if (state.observer) {
      state.observer.disconnect();
      state.observer = null;
    }
    const links = new Map();
    tocListEl.querySelectorAll("a").forEach(link => {
      const id = link.getAttribute("href").replace("#", "");
      links.set(id, link);
    });
    if (!sections.length) return;

    // >>> CALIBRACIÓN QUIRÚRGICA <<<
    // -90px top: El observador empieza a detectar desde el pixel 90 hacia abajo.
    state.observer = new IntersectionObserver(
      entries => {
        if (isManualScroll) return; // Pausa si estamos en viaje manual

        entries.forEach(entry => {
          if (entry.isIntersecting) {
            links.forEach(l => l.classList.remove("active"));
            const activeLink = links.get(entry.target.id);
            if (activeLink) activeLink.classList.add("active");
          }
        });
      },
      { rootMargin: "-90px 0px -80% 0px", threshold: 0 }
    );
    sections.forEach(section => state.observer.observe(section));
  }

  // --- 2. RENDER DETAIL ---
  function renderDetail(detail) {
    const title = detail.titulo || detail.id || "";
    detailTitle.textContent = title;
    detailDesc.textContent = detail.descripcion || "";
    renderTags(detail.tags || []);

    if (breadcrumbEl) {
      breadcrumbEl.textContent = title ? `Referencias > ${title}` : "Referencias";
    }

    if (detail.nota_universidad) {
      detailNote.textContent = detail.nota_universidad;
      detailNote.classList.remove("hidden");
    } else {
      detailNote.classList.add("hidden");
    }

    detailContent.innerHTML = "";
    tocListEl.innerHTML = "";

    const sections = [];
    (detail.secciones || []).forEach((section, idx) => {
      const sectionId = `ref-section-${idx + 1}`;
      
      const block = document.createElement("section");
      block.id = sectionId;
      block.className = "ref-section";
      
      // >>> CALIBRACIÓN QUIRÚRGICA EN EL ELEMENTO <<<
      // 100px: Esto asegura que el título aterrice en el pixel 100.
      // Como el ojo mira desde el 90, el título estará 10px DENTRO de la zona.
      block.style.scrollMarginTop = "100px";

      const heading = document.createElement("h3");
      heading.textContent = section.titulo || "";
      block.appendChild(heading);

      (section.items || []).forEach(item => {
        block.appendChild(renderItem(item));
      });

      detailContent.appendChild(block);
      sections.push(block);

      const anchor = document.createElement("a");
      anchor.href = `#${sectionId}`;
      anchor.textContent = section.titulo || `Sección ${idx + 1}`;
      
      // >>> LÓGICA DE CLIC (BOTONES FUNCIONALES) <<<
      anchor.addEventListener("click", (e) => {
          e.preventDefault();
          
          isManualScroll = true; // Bloqueo momentáneo

          // 1. Feedback visual inmediato
          tocListEl.querySelectorAll("a").forEach(a => a.classList.remove("active"));
          anchor.classList.add("active");

          // 2. Scroll Nativo Inteligente
          // Gracias a scrollMarginTop="100px", esto lo dejará en el sitio exacto.
          block.scrollIntoView({ behavior: "smooth", block: "start" });

          // 3. Desbloqueo
          setTimeout(() => {
              isManualScroll = false;
          }, 1000);
      });

      tocListEl.appendChild(anchor);
    });

    if (tocListEl.children.length) {
      tocContainer.classList.remove("hidden");
    } else {
      tocContainer.classList.add("hidden");
    }

    detailSources.innerHTML = "";
    if (detail.fuentes && Array.isArray(detail.fuentes) && detail.fuentes.length) {
      const titleEl = document.createElement("div");
      titleEl.className = "text-xs uppercase tracking-wider text-gray-400 mb-2";
      titleEl.textContent = "Fuentes";
      detailSources.appendChild(titleEl);
      detail.fuentes.forEach(source => {
        const row = document.createElement("div");
        row.className = "text-sm text-gray-600";
        row.textContent = `${source.label || "Fuente"}: ${source.nota || ""}`;
        detailSources.appendChild(row);
      });
      detailSources.classList.remove("hidden");
    } else {
      detailSources.classList.add("hidden");
    }

    setupScrollSpy(sections);
  }

  function createTagChips(tags) {
    const container = document.createElement("div");
    container.className = "ref-card-tags";
    (tags || []).forEach(tag => {
      const chip = document.createElement("span");
      chip.className = "ref-chip";
      chip.textContent = tag;
      container.appendChild(chip);
    });
    return container;
  }

  function renderPreview(preview) {
    if (!preview) return null;
    const block = document.createElement("div");
    block.className = "ref-preview";
    if (typeof preview === "string") {
      const line = document.createElement("div");
      line.className = "ref-preview-line";
      line.textContent = preview;
      block.appendChild(line);
      return block;
    }
    if (preview.cita) {
      const line = document.createElement("div");
      line.className = "ref-preview-line";
      line.textContent = preview.cita;
      block.appendChild(line);
    }
    if (preview.referencia) {
      const line = document.createElement("div");
      line.className = "ref-preview-line";
      line.innerHTML = applyItalicMarkup(preview.referencia);
      block.appendChild(line);
    }
    if (preview.autor_fecha) {
      const line = document.createElement("div");
      line.className = "ref-preview-line";
      line.textContent = `Autor-fecha: ${preview.autor_fecha}`;
      block.appendChild(line);
    }
    if (preview.numerica) {
      const line = document.createElement("div");
      line.className = "ref-preview-line";
      line.textContent = `Numérica: ${preview.numerica}`;
      block.appendChild(line);
    }
    return block;
  }

  function renderCards(items) {
    gridEl.innerHTML = "";
    if (!items.length) {
      gridEmptyEl.classList.remove("hidden");
      return;
    }
    gridEmptyEl.classList.add("hidden");

    items.forEach(item => {
      const card = document.createElement("article");
      card.className = "ref-card";
      card.dataset.refId = item.id;

      const header = document.createElement("div");
      header.className = "flex items-start justify-between gap-2";
      const title = document.createElement("h3");
      title.className = "text-lg font-bold text-gray-900";
      title.textContent = item.titulo;
      const badge = document.createElement("span");
      badge.className = "text-xs uppercase tracking-wider text-gray-400";
      badge.textContent = "Guía";
      header.appendChild(title);
      header.appendChild(badge);

      card.appendChild(header);
      card.appendChild(createTagChips(item.tags || []));

      const desc = document.createElement("p");
      desc.className = "ref-card-desc";
      desc.textContent = item.descripcion || "";
      card.appendChild(desc);

      const preview = renderPreview(item.preview);
      if (preview) {
        card.appendChild(preview);
      }

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ref-card-btn mt-5 inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-800";
      btn.innerHTML = `Ver guía <i data-lucide="arrow-right" class="w-4 h-4"></i>`;
      btn.addEventListener("click", () => openDetail(item.id, true));
      card.appendChild(btn);

      card.addEventListener("click", event => {
        if (event.target.closest(".ref-card-btn")) return;
        openDetail(item.id, true);
      });

      gridEl.appendChild(card);
    });

    if (typeof lucide !== "undefined") lucide.createIcons();
  }

  function renderSidebarList(items) {
    const containers = [sideListEl, drawerListEl];
    containers.forEach(container => {
      if (!container) return;
      container.innerHTML = "";
      items.forEach(item => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "ref-side-item";
        button.textContent = item.titulo;
        if (item.id === state.activeId) {
          button.classList.add("active");
        }
        button.addEventListener("click", () => {
          openDetail(item.id, true);
          toggleDrawer(false);
        });
        container.appendChild(button);
      });
    });
  }

  function filterItems(term) {
    const value = (term || "").trim().toLowerCase();
    if (!value) return state.items;
    return state.items.filter(item => {
      const text = `${item.titulo || ""} ${(item.tags || []).join(" ")} ${item.descripcion || ""}`.toLowerCase();
      return text.includes(value);
    });
  }

  function applySearch(term, source) {
    const filtered = filterItems(term);
    state.filtered = filtered;
    renderCards(filtered);
    renderSidebarList(filtered);
    syncSearchValue(term, source);
  }

  async function openDetail(refId, pushState = false) {
    if (!refId) return;
    state.activeId = refId;
    toggleViews(true);
    setDetailLoading(true);
    try {
      const detail = await fetchDetail(refId, state.uni);
      renderDetail(detail);
      setDetailLoading(false);
      renderSidebarList(state.filtered.length ? state.filtered : state.items);
      if (pushState && routingEnabled) {
        const url = `${basePath}?uni=${encodeURIComponent(state.uni)}&ref=${encodeURIComponent(refId)}`;
        history.pushState({ ref: refId, uni: state.uni }, "", url);
      }
    } catch (error) {
      detailContent.innerHTML = "<p class='text-sm text-red-600'>No se pudo cargar la norma.</p>";
      setDetailLoading(false);
    }
  }

  function showGrid(pushState = false) {
    toggleViews(false);
    if (pushState && routingEnabled) {
      const url = `${basePath}?uni=${encodeURIComponent(state.uni)}`;
      history.pushState({ ref: null, uni: state.uni }, "", url);
    }
  }

  function showGridError(message) {
    if (!gridEmptyEl) return;
    gridEmptyEl.textContent = message || "No se pudieron cargar las normas.";
    gridEmptyEl.classList.remove("hidden");
  }

  async function loadList() {
    const { uni } = parseQuery();
    state.uni = uni;
    try {
      const data = await fetchIndex(uni);
      state.items = data.items || [];
      state.order = data.config?.order || state.items.map(item => item.id);

      const ordered = state.order
        .map(id => state.items.find(item => item.id === id))
        .filter(Boolean);

      state.items = ordered;
      state.filtered = ordered;
      renderCards(ordered);
      renderSidebarList(ordered);
      return true;
    } catch (error) {
      renderCards([]);
      renderSidebarList([]);
      showGridError("No se pudieron cargar las normas.");
      return false;
    }
  }

  async function init() {
    // Configurar botón Volver -> Ir al Catálogo
    if (backBtn) {
        backBtn.innerHTML = '<i data-lucide="arrow-left" class="w-4 h-4"></i> Volver al Catálogo';
        backBtn.addEventListener("click", (e) => {
            e.preventDefault();
            window.location.href = "/catalog";
        });
    }

    const { ref } = parseQuery();
    const ok = await loadList();

    if (ref && ok) {
      await openDetail(ref, false);
    } else {
      toggleViews(false);
    }
  }

  gridSearchEl?.addEventListener("input", event => applySearch(event.target.value, gridSearchEl));
  sideSearchEl?.addEventListener("input", event => applySearch(event.target.value, sideSearchEl));
  drawerSearchEl?.addEventListener("input", event => applySearch(event.target.value, drawerSearchEl));

  openDrawerBtn?.addEventListener("click", () => toggleDrawer(true));
  closeDrawerBtn?.addEventListener("click", () => toggleDrawer(false));
  drawerBackdrop?.addEventListener("click", () => toggleDrawer(false));

  if (routingEnabled) {
    window.addEventListener("popstate", () => {
      const { ref } = parseQuery();
      if (ref) {
        openDetail(ref, false);
      } else {
        window.location.href = "/catalog";
      }
    });
  }

  init();
})();