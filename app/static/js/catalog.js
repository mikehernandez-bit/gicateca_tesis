/*
Archivo: app/static/js/catalog.js
Proposito: Controla el flujo del catalogo (modo, filtros, modales de vista).
Responsabilidades: Gestion de UI, filtros de tarjetas y modal de previsualizacion de caratulas.
No hace: No consume APIs fuera de /formatos/{id}/data ni maneja routing servidor.
Entradas/Salidas: Entradas = eventos UI; Salidas = cambios DOM y modales.
Donde tocar si falla: Revisar funciones de flujo y preview (iniciarFlujo, previewCover).
*/

/**
 * catalog.js v6.0
 * Flujo: Nivel 1 (Modo) -> Nivel 2 (Categoría Persistente) -> Nivel 3 (Resultados)
 */

let currentMode = 'normal'; // 'normal', 'caratula', 'referencias'
const referencesState = {
    items: [],
    loaded: false,
};

/* ==========================================================================
   1. GESTIÓN VISUAL (SOMBREADO DE TARJETAS)
   ========================================================================== */

// Sombrea las tarjetas de Nivel 1 (Accesos Rápidos)
function highlightTopCard(cardId) {
    document.querySelectorAll('.quick-card').forEach(card => {
        card.classList.remove('ring-2', 'ring-offset-2', 'ring-orange-500', 'ring-indigo-500', 'ring-green-500', 'border-orange-500', 'border-indigo-500', 'border-green-500');
        card.classList.add('border-gray-200');
    });

    const activeCard = document.getElementById(cardId);
    if (!activeCard) return;

    activeCard.classList.remove('border-gray-200');
    if (cardId.includes('caratulas')) activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-orange-500', 'border-orange-500');
    else if (cardId.includes('referencias')) activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-indigo-500', 'border-indigo-500');
    else activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-green-500', 'border-green-500');
}

// Sombrea las tarjetas de Nivel 2 (Filtro Categoría)
function highlightCategoryCard(cardId) {
    document.querySelectorAll('.cat-card').forEach(card => {
        card.classList.remove('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
        card.classList.add('border-gray-200');
        // Reset backgrounds (opcional, si quisieras un estado "inactivo" más fuerte)
    });

    const activeCard = document.getElementById(cardId);
    if (activeCard) {
        activeCard.classList.remove('border-gray-200');
        activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
    }
}

/* ==========================================================================
   2. CONTROL DE FLUJO (NIVEL 1 -> NIVEL 2)
   ========================================================================== */

function iniciarFlujo(modo, cardId) {
    currentMode = modo;
    highlightTopCard(cardId);

    const referencias = document.getElementById("bloque-referencias");
    const categorias = document.getElementById("bloque-categorias");
    const resultados = document.getElementById("bloque-resultados");

    if (modo === 'referencias') {
        if (categorias) categorias.classList.add("hidden", "opacity-0", "translate-y-4");
        if (resultados) resultados.classList.add("hidden", "opacity-0", "translate-y-4");
        if (referencias) {
            referencias.classList.remove("hidden");
            setTimeout(() => {
                referencias.classList.remove("opacity-0", "translate-y-4");
                referencias.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 50);
        }
        if (!referencesState.loaded) {
            loadReferencesGrid();
        }
        return;
    }

    if (referencias) referencias.classList.add("hidden", "opacity-0", "translate-y-4");

    // 1. Mostrar Bloque Categorías (Nivel 2)
    categorias.classList.remove("hidden");
    setTimeout(() => { 
        categorias.classList.remove("opacity-0", "translate-y-4");
        categorias.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);

    // 2. Ocultar Resultados (Nivel 3) hasta que elija categoría
    resultados.classList.add("hidden", "opacity-0", "translate-y-4");

    // 3. Limpiar selección visual del Nivel 2
    document.querySelectorAll('.cat-card').forEach(c => {
        c.classList.remove('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
        c.classList.add('border-gray-200');
    });
}

/* ==========================================================================
   3. CONTROL DE FLUJO (NIVEL 2 -> NIVEL 3)
   ========================================================================== */

function seleccionarCategoriaFinal(filtro, cardId) {
    // 1. Visual Nivel 2
    highlightCategoryCard(cardId);

    const referencias = document.getElementById("bloque-referencias");
    if (referencias) referencias.classList.add("hidden", "opacity-0", "translate-y-4");

    // 2. Filtrar Grid
    filtrarGrid(filtro);

    // 3. Aplicar Estilos según el Modo (Normal, Carátula)
    aplicarEstilosGrid();

    // 4. Mostrar Resultados (Nivel 3)
    const resultados = document.getElementById("bloque-resultados");
    resultados.classList.remove("hidden");
    setTimeout(() => { 
        resultados.classList.remove("opacity-0", "translate-y-4");
        // Scroll suave hacia los resultados, pero manteniendo Nivel 2 visible
        resultados.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
}

function filtrarGrid(categoria) {
    const cards = document.querySelectorAll(".formato-card");
    let count = 0;
    cards.forEach((card) => {
        if (categoria === "todos" || card.getAttribute("data-tipo") === categoria) {
            card.style.display = "flex"; 
            count++;
        } else {
            card.style.display = "none";
        }
    });
}

function aplicarEstilosGrid() {
    document.querySelectorAll(".formato-card").forEach(card => {
        const badge = card.querySelector(".mode-badge");
        const actionText = card.querySelector(".action-text");
        
        // Reset clases base
        card.className = "formato-card group bg-white rounded-xl shadow-sm border border-gray-200 transition-all cursor-pointer flex flex-col h-full overflow-hidden relative hover:shadow-lg";
        card.querySelector(".original-badges").classList.remove("opacity-30");
        badge.classList.add("hidden");

        if (currentMode === 'caratula') {
            card.querySelector(".original-badges").classList.add("opacity-30");
            card.classList.add("hover:border-orange-300");
            
            badge.className = "mode-badge absolute top-3 right-3 z-10 bg-orange-100 text-orange-700 text-[10px] font-bold px-2 py-1 rounded shadow-sm border border-orange-200 flex items-center gap-1";
            badge.innerHTML = `<i data-lucide="eye" class="w-3 h-3"></i> CARÁTULA`;
            badge.classList.remove("hidden");

            actionText.innerHTML = `Ver Carátula <i data-lucide="eye" class="w-4 h-4"></i>`;
            actionText.className = "action-text text-orange-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform";

        } else { // Normal
            card.classList.add("hover:border-blue-300");
            actionText.innerHTML = `Ver Estructura <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>`;
            actionText.className = "action-text text-blue-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform";
        }
    });
    
    if(typeof lucide !== 'undefined') lucide.createIcons();
}

/* ==========================================================================
   3.5. REFERENCIAS (GRID EN CATÁLOGO)
   ========================================================================== */

function getActiveUni() {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get("uni");
    const block = document.getElementById("bloque-referencias");
    const fromDom = block ? block.dataset.uni : null;
    return (fromQuery || fromDom || "unac").toLowerCase();
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

async function fetchReferencesIndex() {
    const uni = getActiveUni();
    const res = await fetch(`/api/referencias?uni=${encodeURIComponent(uni)}`);
    if (!res.ok) throw new Error("Error cargando referencias.");
    return await res.json();
}

function renderReferencesCards(items) {
    const grid = document.getElementById("refs-grid-catalog");
    const empty = document.getElementById("refs-grid-empty-catalog");
    if (!grid || !empty) return;

    grid.innerHTML = "";
    if (!items.length) {
        empty.classList.remove("hidden");
        empty.textContent = "No hay normas disponibles.";
        return;
    }
    empty.classList.add("hidden");

    const uni = getActiveUni();
    items.forEach(item => {
        const card = document.createElement("article");
        card.className = "ref-card";

        const header = document.createElement("div");
        header.className = "flex items-start justify-between gap-2";
        const title = document.createElement("h3");
        title.className = "text-lg font-bold text-gray-900";
        title.textContent = item.titulo || item.id;
        const badge = document.createElement("span");
        badge.className = "text-xs uppercase tracking-wider text-gray-400";
        badge.textContent = "Guía";
        header.appendChild(title);
        header.appendChild(badge);
        card.appendChild(header);

        const tags = document.createElement("div");
        tags.className = "ref-card-tags";
        (item.tags || []).forEach(tag => {
            const chip = document.createElement("span");
            chip.className = "ref-chip";
            chip.textContent = tag;
            tags.appendChild(chip);
        });
        card.appendChild(tags);

        const desc = document.createElement("p");
        desc.className = "ref-card-desc";
        desc.textContent = item.descripcion || "";
        card.appendChild(desc);

        if (item.preview) {
            const preview = document.createElement("div");
            preview.className = "ref-preview";
            if (typeof item.preview === "string") {
                const line = document.createElement("div");
                line.className = "ref-preview-line";
                line.textContent = item.preview;
                preview.appendChild(line);
            } else {
                if (item.preview.cita) {
                    const line = document.createElement("div");
                    line.className = "ref-preview-line";
                    line.textContent = item.preview.cita;
                    preview.appendChild(line);
                }
                if (item.preview.referencia) {
                    const line = document.createElement("div");
                    line.className = "ref-preview-line";
                    line.innerHTML = applyItalicMarkup(item.preview.referencia);
                    preview.appendChild(line);
                }
                if (item.preview.autor_fecha) {
                    const line = document.createElement("div");
                    line.className = "ref-preview-line";
                    line.textContent = `Autor-fecha: ${item.preview.autor_fecha}`;
                    preview.appendChild(line);
                }
                if (item.preview.numerica) {
                    const line = document.createElement("div");
                    line.className = "ref-preview-line";
                    line.textContent = `Numérica: ${item.preview.numerica}`;
                    preview.appendChild(line);
                }
            }
            card.appendChild(preview);
        }

        const link = document.createElement("a");
        link.href = `/referencias?uni=${encodeURIComponent(uni)}&ref=${encodeURIComponent(item.id)}`;
        link.className = "ref-card-btn mt-5 inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-800";
        link.innerHTML = `Ver guía <i data-lucide="arrow-right" class="w-4 h-4"></i>`;
        card.appendChild(link);

        grid.appendChild(card);
    });

    if (typeof lucide !== "undefined") lucide.createIcons();
}

async function loadReferencesGrid() {
    const empty = document.getElementById("refs-grid-empty-catalog");
    if (empty) {
        empty.textContent = "Cargando normas...";
        empty.classList.remove("hidden");
    }
    try {
        const data = await fetchReferencesIndex();
        referencesState.items = data.items || [];
        referencesState.loaded = true;
        renderReferencesCards(referencesState.items);
    } catch (error) {
        if (empty) {
            empty.textContent = "No se pudieron cargar las normas. Intenta recargar la página.";
            empty.classList.remove("hidden");
        }
    }
}

/* ==========================================================================
   4. INTERCEPTOR DE CLICS (MODALES vs NAVEGACIÓN)
   ========================================================================== */
function handleCardClick(event, formatId) {
    if (currentMode === 'caratula') {
        event.preventDefault();
        previewCover(formatId);
        return false;
    }
    return true; 
}

/* ==========================================================================
   5. MODALES (DATA FETCH)
   ========================================================================== */
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

async function fetchFormatData(formatId) {
    const response = await fetch(`/formatos/${formatId}/data`);
    if (!response.ok) throw new Error("Error cargando datos.");
    return await response.json();
}

// Modal Carátula
async function previewCover(formatId) {
    const modal = document.getElementById('coverModal');
    const loader = document.getElementById('coverLoader');
    const content = document.getElementById('coverContent');
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    try {
        const data = await fetchFormatData(formatId);
        const c = data.caratula || {}; 
        document.getElementById('c-uni').textContent = c.universidad || "UNIVERSIDAD NACIONAL DEL CALLAO";
        document.getElementById('c-fac').textContent = c.facultad || "";
        document.getElementById('c-esc').textContent = c.escuela || "";
        document.getElementById('c-titulo').textContent = c.titulo_placeholder || "TÍTULO DEL PROYECTO";
        document.getElementById('c-frase').textContent = c.frase_grado || "";
        document.getElementById('c-grado').textContent = c.grado_objetivo || "";
        document.getElementById('c-lugar').textContent = (c.pais || "CALLAO, PERÚ");
        document.getElementById('c-anio').textContent = (c.fecha || "2026");
        const guiaEl = document.getElementById('c-guia');
        if (guiaEl) {
            const guia = (c.guia || c.nota || "").trim();
            guiaEl.textContent = guia;
            guiaEl.classList.toggle('hidden', !guia);
        }
        loader.classList.add('hidden');
        content.classList.remove('hidden');
    } catch (error) {
        closeModal('coverModal');
        alert("Error cargando carátula.");
    }
}

