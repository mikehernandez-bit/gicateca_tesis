/*
Archivo: app/static/js/catalog.js
Propósito: Controlador híbrido. Gestiona el flujo del catálogo y consume la API de referencias existente.
*/

let currentMode = 'normal'; // 'normal', 'caratula', 'referencias'
const referencesState = { items: [], loaded: false };

/* ==========================================================================
   1. GESTIÓN VISUAL (SOMBREADO)
   ========================================================================== */
function highlightTopCard(cardId) {
    document.querySelectorAll('.quick-card').forEach(card => {
        card.classList.remove('ring-2', 'ring-offset-2', 'ring-orange-500', 'ring-indigo-500', 'ring-green-500', 'border-orange-500', 'border-indigo-500', 'border-green-500');
        card.classList.add('border-gray-200');
    });
    const activeCard = document.getElementById(cardId);
    if (activeCard) {
        activeCard.classList.remove('border-gray-200');
        if (cardId.includes('caratulas')) activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-orange-500', 'border-orange-500');
        else if (cardId.includes('referencias')) activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-indigo-500', 'border-indigo-500');
        else activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-green-500', 'border-green-500');
    }
}

function highlightCategoryCard(cardId) {
    document.querySelectorAll('.cat-card').forEach(card => {
        card.classList.remove('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
        card.classList.add('border-gray-200');
    });
    const activeCard = document.getElementById(cardId);
    if (activeCard) {
        activeCard.classList.remove('border-gray-200');
        activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
    }
}

/* ==========================================================================
   2. CONTROL DE FLUJO
   ========================================================================== */
function iniciarFlujo(modo, cardId) {
    currentMode = modo;
    highlightTopCard(cardId);

    const bloqueRefs = document.getElementById("bloque-referencias");
    const bloqueCats = document.getElementById("bloque-categorias");
    const bloqueRes = document.getElementById("bloque-resultados");

    // --- MODO REFERENCIAS ---
    if (modo === 'referencias') {
        if (bloqueCats) bloqueCats.classList.add("hidden", "opacity-0", "translate-y-4");
        if (bloqueRes) bloqueRes.classList.add("hidden", "opacity-0", "translate-y-4");

        if (bloqueRefs) {
            bloqueRefs.classList.remove("hidden");
            setTimeout(() => {
                bloqueRefs.classList.remove("opacity-0", "translate-y-4");
                bloqueRefs.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 50);

            if (!referencesState.loaded) {
                loadReferencesGrid();
            }
        }
        return;
    }

    // --- MODOS CARÁTULA / NORMAL ---
    if (bloqueRefs) bloqueRefs.classList.add("hidden", "opacity-0");

    // 1. Mostrar Categorías
    if (bloqueCats) {
        const titulo = document.getElementById('titulo-paso-2');
        if (titulo) titulo.textContent = (modo === 'caratula') ? "¿Qué carátula deseas visualizar?" : "Selecciona qué documentos ver";

        bloqueCats.classList.remove("hidden");
        setTimeout(() => {
            bloqueCats.classList.remove("opacity-0", "translate-y-4");
            bloqueCats.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 50);
    }

    // 2. Ocultar Resultados hasta selección
    if (bloqueRes) bloqueRes.classList.add("hidden", "opacity-0");

    // Limpiar selección previa
    document.querySelectorAll('.cat-card').forEach(c => {
        c.classList.remove('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
        c.classList.add('border-gray-200');
    });
}

function seleccionarCategoriaFinal(filtro, cardId) {
    highlightCategoryCard(cardId);

    const bloqueRefs = document.getElementById("bloque-referencias");
    if (bloqueRefs) bloqueRefs.classList.add("hidden");

    filtrarGrid(filtro);
    aplicarEstilosGrid();

    const resultados = document.getElementById("bloque-resultados");
    if (resultados) {
        resultados.classList.remove("hidden");
        setTimeout(() => {
            resultados.classList.remove("opacity-0", "translate-y-4");
            resultados.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 50);
    }
}

/* ==========================================================================
   3. LOGICA REFERENCIAS (VISUALIZACIÓN LIMPIA)
   ========================================================================== */

function getActiveUni() {
    const block = document.getElementById("bloque-referencias");
    return (block ? block.dataset.uni : "unac").toLowerCase();
}

async function fetchReferencesIndex() {
    const uni = getActiveUni();
    const res = await fetch(`/api/referencias?uni=${encodeURIComponent(uni)}`);
    if (!res.ok) throw new Error("Error cargando referencias.");
    return await res.json();
}

// --- FUNCIÓN DE RENDERIZADO LIMPIA ---
function renderReferencesCards(items) {
    const grid = document.getElementById("refs-grid-catalog");
    const empty = document.getElementById("refs-grid-empty-catalog");
    if (!grid) return;

    grid.innerHTML = "";

    if (!items || !items.length) {
        if (empty) empty.classList.remove("hidden");
        return;
    }
    if (empty) empty.classList.add("hidden");

    const uni = getActiveUni();

    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow flex flex-col h-full";

        // 1. HEADER (Solo Título y Badge)
        const header = document.createElement("div");
        header.className = "flex justify-between items-start mb-3";
        header.innerHTML = `
            <h3 class="font-bold text-lg text-gray-900">${item.titulo || item.id}</h3>
            <span class="text-[10px] uppercase tracking-wider font-bold text-gray-400 border border-gray-100 px-2 py-1 rounded">GUÍA</span>
        `;
        card.appendChild(header);

        // --- SECCIÓN DE TAGS ELIMINADA FÍSICAMENTE ---

        // 2. DESCRIPCIÓN (CORTADA AL PRIMER PUNTO)
        const desc = document.createElement("p");
        desc.className = "text-sm text-gray-600 mb-6 leading-relaxed flex-grow";

        let fullDesc = item.descripcion || "";
        const dotIndex = fullDesc.indexOf('.');

        if (dotIndex !== -1) {
            desc.textContent = fullDesc.substring(0, dotIndex + 1);
        } else {
            desc.textContent = fullDesc;
        }
        card.appendChild(desc);

        // --- SECCIÓN PREVIEW BOX ELIMINADA FÍSICAMENTE ---

        // 3. BOTÓN ENLACE
        const btnLink = document.createElement("a");
        // Se mantiene el enlace normal por ahora
        // AHORA (Con la marca de origen)
        // ANTES (Línea actual)
        btnLink.href = `/referencias?uni=${encodeURIComponent(uni)}&ref=${encodeURIComponent(item.id)}`;
        btnLink.className = "text-indigo-600 text-sm font-bold flex items-center gap-1 hover:underline mt-auto cursor-pointer";
        btnLink.innerHTML = `Ver guía <i data-lucide="arrow-right" class="w-4 h-4"></i>`;

        card.appendChild(btnLink);
        grid.appendChild(card);
    });

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

async function loadReferencesGrid() {
    const loader = document.getElementById("refs-loader");
    const empty = document.getElementById("refs-grid-empty-catalog");

    if (loader) loader.classList.remove("hidden");
    if (empty) empty.classList.add("hidden");

    try {
        const data = await fetchReferencesIndex();
        referencesState.items = data.items || [];
        referencesState.loaded = true;
        renderReferencesCards(referencesState.items);
    } catch (error) {
        console.error(error);
        if (empty) {
            empty.textContent = "No se pudieron cargar las normas.";
            empty.classList.remove("hidden");
        }
    } finally {
        if (loader) loader.classList.add("hidden");
    }
}

/* ==========================================================================
   4. FILTRADO Y DEDUPLICACIÓN (FORMATOS)
   ========================================================================== */
function filtrarGrid(categoria) {
    const cards = document.querySelectorAll(".formato-card");
    const seenGroups = new Set();

    cards.forEach((card) => {
        const cardType = card.getAttribute("data-tipo");
        const cardGroup = card.getAttribute("data-group");
        const cardUni = card.getAttribute("data-uni") || "";
        const groupKey = `${cardGroup}-${cardUni}`;
        const titleEl = card.querySelector(".card-title");
        const originalTitle = card.getAttribute("data-original-title");

        const matchesCategory = (categoria === "todos" || cardType === categoria);

        if (currentMode === 'caratula') {
            if (matchesCategory && !seenGroups.has(groupKey)) {
                card.style.display = "flex";
                seenGroups.add(groupKey);
                if (titleEl && originalTitle) titleEl.textContent = originalTitle.split(" - ")[0];
            } else {
                card.style.display = "none";
            }
        } else {
            if (matchesCategory) {
                card.style.display = "flex";
                if (titleEl && originalTitle) titleEl.textContent = originalTitle;
            } else {
                card.style.display = "none";
            }
        }
    });
}

function aplicarEstilosGrid() {
    document.querySelectorAll(".formato-card").forEach(card => {
        const badge = card.querySelector(".mode-badge");
        const actionText = card.querySelector(".action-text");

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
        } else {
            card.classList.add("hover:border-blue-300");
            actionText.innerHTML = `Ver Estructura <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>`;
            actionText.className = "action-text text-blue-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform";
        }
    });
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

/* ==========================================================================
   5. INTERCEPTOR Y MODALES
   ========================================================================== */
function handleCardClick(event, formatId) {
    if (currentMode === 'caratula') {
        event.preventDefault();
        previewCover(formatId);
        return false;
    }
    return true;
}

function closeModal(modalId) {
    // Si es coverModal, delegar a GicaCover para cierre centralizado
    if (modalId === 'coverModal' && window.GicaCover && window.GicaCover.close) {
        window.GicaCover.close();
        return;
    }
    // Para otros modales, usar lógica estándar
    var modal = document.getElementById(modalId);
    if (modal) modal.classList.add('hidden');
}

async function fetchFormatData(formatId) {
    const response = await fetch(`/formatos/${formatId}/data`);
    if (!response.ok) throw new Error("Error cargando datos.");
    return await response.json();
}

async function previewCover(formatId) {
    // Delegar a la lógica unificada en cover-preview.js
    if (window.GicaCover && window.GicaCover.open) {
        return window.GicaCover.open(formatId);
    } else {
        console.error('[catalog.js] GicaCover no está disponible.');
    }
}

// === FIN DE FUNCIONES DE CARÁTULA ===
// La lógica completa de previewCover está en cover-preview.js
