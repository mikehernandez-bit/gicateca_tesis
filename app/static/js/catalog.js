/*
Archivo: app/static/js/catalog.js
Proposito: Controla el flujo del catalogo (modo, filtros, modales de vista).
Responsabilidades: Gestion de UI, filtros de tarjetas y modales de previsualizacion.
No hace: No consume APIs fuera de /formatos/{id}/data ni maneja routing servidor.
Entradas/Salidas: Entradas = eventos UI; Salidas = cambios DOM y modales.
Donde tocar si falla: Revisar funciones de flujo y preview (iniciarFlujo, previewCover, previewReferencias).
*/

/**
 * catalog.js v6.0
 * Flujo: Nivel 1 (Modo) -> Nivel 2 (CategorÃ­a Persistente) -> Nivel 3 (Resultados)
 */

let currentMode = 'normal'; // 'normal', 'caratula', 'referencias'

/* ==========================================================================
   1. GESTIÃ“N VISUAL (SOMBREADO DE TARJETAS)
   ========================================================================== */

// Sombrea las tarjetas de Nivel 1 (Accesos RÃ¡pidos)
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

// Sombrea las tarjetas de Nivel 2 (Filtro CategorÃ­a)
function highlightCategoryCard(cardId) {
    document.querySelectorAll('.cat-card').forEach(card => {
        card.classList.remove('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
        card.classList.add('border-gray-200');
        // Reset backgrounds (opcional, si quisieras un estado "inactivo" mÃ¡s fuerte)
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

    // 1. Mostrar Bloque CategorÃ­as (Nivel 2)
    const categorias = document.getElementById("bloque-categorias");
    categorias.classList.remove("hidden");
    setTimeout(() => { 
        categorias.classList.remove("opacity-0", "translate-y-4");
        categorias.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);

    // 2. Ocultar Resultados (Nivel 3) hasta que elija categorÃ­a
    const resultados = document.getElementById("bloque-resultados");
    resultados.classList.add("hidden", "opacity-0", "translate-y-4");

    // 3. Limpiar selecciÃ³n visual del Nivel 2
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

    // 2. Filtrar Grid
    filtrarGrid(filtro);

    // 3. Aplicar Estilos segÃºn el Modo (Normal, CarÃ¡tula, Ref)
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
            badge.innerHTML = `<i data-lucide="eye" class="w-3 h-3"></i> CARÃTULA`;
            badge.classList.remove("hidden");

            actionText.innerHTML = `Ver CarÃ¡tula <i data-lucide="eye" class="w-4 h-4"></i>`;
            actionText.className = "action-text text-orange-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform";

        } else if (currentMode === 'referencias') {
            card.querySelector(".original-badges").classList.add("opacity-30");
            card.classList.add("hover:border-indigo-300");

            badge.className = "mode-badge absolute top-3 right-3 z-10 bg-indigo-100 text-indigo-700 text-[10px] font-bold px-2 py-1 rounded shadow-sm border border-indigo-200 flex items-center gap-1";
            badge.innerHTML = `<i data-lucide="book-open" class="w-3 h-3"></i> REFERENCIAS`;
            badge.classList.remove("hidden");

            actionText.innerHTML = `Ver Normas <i data-lucide="search" class="w-4 h-4"></i>`;
            actionText.className = "action-text text-indigo-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform";

        } else { // Normal
            card.classList.add("hover:border-blue-300");
            actionText.innerHTML = `Ver Estructura <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>`;
            actionText.className = "action-text text-blue-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform";
        }
    });
    
    if(typeof lucide !== 'undefined') lucide.createIcons();
}

/* ==========================================================================
   4. INTERCEPTOR DE CLICS (MODALES vs NAVEGACIÃ“N)
   ========================================================================== */
function handleCardClick(event, formatId) {
    if (currentMode === 'caratula') {
        event.preventDefault();
        previewCover(formatId);
        return false;
    } 
    else if (currentMode === 'referencias') {
        event.preventDefault();
        previewReferencias(formatId);
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

// Modal CarÃ¡tula
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
        document.getElementById('c-titulo').textContent = c.titulo_placeholder || "TÃTULO DEL PROYECTO";
        document.getElementById('c-frase').textContent = c.frase_grado || "";
        document.getElementById('c-grado').textContent = c.grado_objetivo || "";
        document.getElementById('c-lugar').textContent = (c.pais || "CALLAO, PERÃš");
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
        alert("Error cargando carÃ¡tula.");
    }
}

// Modal Referencias
async function previewReferencias(formatId) {
    const modal = document.getElementById('refModal');
    const loader = document.getElementById('refLoader');
    const content = document.getElementById('refContent');
    const list = document.getElementById('refList');
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    list.innerHTML = "";
    try {
        const data = await fetchFormatData(formatId);
        const refData = data.finales?.referencias || {};
        let htmlContent = "";
        if (refData.titulo) htmlContent += `<h4 class="font-bold text-lg mb-3 text-indigo-900 border-b pb-2">${refData.titulo}</h4>`;
        if (refData.nota) htmlContent += `<div class="p-4 bg-indigo-50 text-indigo-800 rounded-lg mb-4 text-sm italic">${refData.nota}</div>`;
        if (refData.secciones && Array.isArray(refData.secciones)) {
            refData.secciones.forEach(sec => { htmlContent += `<p class="mb-3"><span class="font-bold">${sec.sub || ''}</span> ${sec.texto}</p>`; });
        } else if (refData.contenido && Array.isArray(refData.contenido)) {
             refData.contenido.forEach(item => { htmlContent += `<p class="mb-2">â€¢ ${item.texto}</p>`; });
        } else if (!refData.titulo) { htmlContent = "<p class='text-gray-500 italic text-center'>No se encontrÃ³ informaciÃ³n.</p>"; }
        list.innerHTML = htmlContent;
        loader.classList.add('hidden');
        content.classList.remove('hidden');
    } catch (error) {
        closeModal('refModal');
        alert("Error cargando referencias.");
    }
}

