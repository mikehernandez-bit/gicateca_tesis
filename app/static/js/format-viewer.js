/*
Archivo: app/static/js/format-viewer.js
Proposito: Maneja la vista detalle de formatos (descarga, previews y requisitos).
Responsabilidades: Consumir /formatos/{id}/data, abrir modales y construir UI dinamica.
No hace: No genera documentos en servidor ni modifica datos.
Entradas/Salidas: Entradas = eventos UI; Salidas = cambios DOM, descargas y modales.
Donde tocar si falla: Revisar fetchFormatJson, previewCover/previewIndex/previewChapter y hydrateRequirementsList.
*/

/**
 * Lógica para visualización y descarga de formatos.
 * Maneja: Word (Descarga), PDF (Preview), Carátula (JSON), Índice (JSON) y Capítulos (JSON).
 */

function buildJsonPath(formatId) {
    return `/formatos/${formatId}/data`;
}

async function fetchFormatJson(formatId) {
    const jsonPath = buildJsonPath(formatId);
    const response = await fetch(jsonPath + '?t=' + new Date().getTime());
    if (!response.ok) {
        throw new Error(`No se encontr\u00f3 el archivo (Error ${response.status}) en: ${jsonPath}`);
    }
    return response.json();
}

function shortGuide(text) {
    if (!text) return 'Ver detalle en la vista previa.';
    const line = text.split(/\n+/)[0].trim();
    return line || 'Ver detalle en la vista previa.';
}

// --- 1. Descargar DOCX ---
async function downloadDocument(formatId) {
    const btn = document.getElementById('download-btn');
    const btnText = document.getElementById('download-text');
    const originalText = btnText.textContent;

    try {
        btn.disabled = true;
        btnText.textContent = 'Generando...';

        const response = await fetch(`/formatos/${formatId}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al generar el documento');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const parts = formatId.split('-');
        const university = parts[0].toUpperCase();
        const rest = parts.slice(1).join('_').toUpperCase();
        a.download = `${university}_${rest}.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        btnText.textContent = 'Descargado ✓';
        setTimeout(() => {
            btnText.textContent = originalText;
            btn.disabled = false;
        }, 2000);
    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
        btnText.textContent = originalText;
        btn.disabled = false;
    }
}

// --- 2. Modal PDF (Vista Previa General) ---
function openPdfModal(formatId) {
    const modal = document.getElementById('pdfModal');
    const viewer = document.getElementById('pdfViewer');
    const title = document.getElementById('modal-title');

    if (title) title.innerText = "Vista de Lectura";

    const pdfUrl = `/formatos/${formatId}/pdf`;
    const cacheBust = `t=${Date.now()}`;
    viewer.src = `${pdfUrl}?${cacheBust}#page=1&view=Fit&toolbar=0&navpanes=0`;
    modal.classList.remove('hidden');
}

function closePdfModal() {
    const modal = document.getElementById('pdfModal');
    const viewer = document.getElementById('pdfViewer');
    modal.classList.add('hidden');
    viewer.src = '';
}

// --- 3. Visualizador de Carátula (JSON) ---
// WRAPPER: Toda la lógica vive en cover-preview.js para evitar divergencias
async function previewCover(formatId) {
    if (window.GicaCover && window.GicaCover.open) {
        return window.GicaCover.open(formatId);
    }
    console.error('[format-viewer.js] ERROR: GicaCover no está disponible. Verifica que cover-preview.js esté cargado antes de format-viewer.js');
    return;
}

// WRAPPER: Cierre centralizado en GicaCover
function closeCoverModal() {
    if (window.GicaCover && window.GicaCover.close) {
        window.GicaCover.close();
    } else {
        console.error('[format-viewer.js] ERROR: GicaCover.close no disponible');
    }
}

// --- 4. Visualizador de Índice (Inteligente) ---
async function previewIndex(formatId) {
    const modal = document.getElementById('indexModal');
    const loader = document.getElementById('indexLoader');
    const content = document.getElementById('indexContent');
    const listContainer = document.getElementById('indexList');
    const footer = document.getElementById('indexFooter');

    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    listContainer.innerHTML = '';

    try {
        const data = await fetchFormatJson(formatId);
        let structure = [];

        const sanitizeTitle = (value) => {
            if (!value) return null;
            const text = String(value).trim();
            if (!text) return null;
            if (text.toUpperCase() === "UNDEFINED") return null;
            return text;
        };

        const makeTitle = (num, title) => {
            const cleanTitle = sanitizeTitle(title);
            const cleanNum = sanitizeTitle(num);
            if (!cleanTitle && !cleanNum) return null;
            if (cleanTitle && cleanNum) {
                const lowerTitle = cleanTitle.toLowerCase();
                const lowerNum = cleanNum.toLowerCase();
                if (lowerTitle.startsWith(lowerNum)) return cleanTitle;
                return `${cleanNum}. ${cleanTitle}`;
            }
            return cleanTitle || cleanNum;
        };

        const inferLevel = (title, fallback = 1) => {
            const raw = String(title || "").trim();
            if (!raw) return fallback;
            if (/^CAP[ÍI]TULO/i.test(raw)) return 1;
            if (/^[IVXLCDM]+\./i.test(raw)) return 1;
            const match = raw.match(/^(\d+(?:\.\d+)+)/);
            if (match && match[1]) {
                return match[1].split(".").length;
            }
            return fallback;
        };

        const pushItem = (title, level) => {
            const clean = sanitizeTitle(title);
            if (!clean) return;
            structure.push({ titulo: clean, nivel: inferLevel(clean, level || 1) });
        };

        if (Array.isArray(data.estructura)) {
            data.estructura.forEach(item => {
                const title = item?.titulo || item?.title || item?.texto;
                const lvl = item?.nivel || item?.level;
                pushItem(title, lvl || 1);
            });
        } else {
            if (data.preliminares && data.preliminares.introduccion) {
                pushItem(data.preliminares.introduccion.titulo, 1);
            }
            if (Array.isArray(data.cuerpo)) {
                data.cuerpo.forEach(cap => {
                    pushItem(cap.titulo, 1);
                    if (Array.isArray(cap.contenido)) {
                        cap.contenido.forEach(sub => {
                            pushItem(sub.texto, 2);
                        });
                    }
                    if (Array.isArray(cap.items)) {
                        cap.items.forEach(item => {
                            pushItem(item.titulo, 2);
                            if (Array.isArray(item.subitems)) {
                                item.subitems.forEach(sub => {
                                    pushItem(sub, 3);
                                });
                            }
                        });
                    }
                });
            } else if (Array.isArray(data.secciones)) {
                data.secciones.forEach(sec => {
                    const title = makeTitle(sec.numero || sec.romano || sec.id, sec.titulo || sec.title);
                    pushItem(title, 1);
                    if (Array.isArray(sec.items)) {
                        sec.items.forEach(item => {
                            pushItem(makeTitle(null, item.titulo || item.title), 2);
                            if (Array.isArray(item.subitems)) {
                                item.subitems.forEach(sub => {
                                    pushItem(sub, 3);
                                });
                            }
                        });
                    }
                    if (Array.isArray(sec.subitems)) {
                        sec.subitems.forEach(sub => {
                            pushItem(sub, 2);
                        });
                    }
                });
            }
            if (data.finales) {
                const refTitle = typeof data.finales.referencias === "string"
                    ? data.finales.referencias
                    : data.finales.referencias?.titulo;
                const anexTitle = typeof data.finales.anexos === "string"
                    ? data.finales.anexos
                    : data.finales.anexos?.titulo_seccion || data.finales.anexos?.titulo;
                pushItem(refTitle, 1);
                pushItem(anexTitle, 1);
            }
        }

        if (!structure.length) {
            const empty = document.createElement('div');
            empty.className = "text-sm text-gray-500";
            empty.textContent = "Sin estructura referencial disponible.";
            listContainer.appendChild(empty);
        } else {
            structure.forEach(item => {
                const row = document.createElement('div');
                row.className = "flex items-baseline w-full";
                const level = inferLevel(item.titulo, item.nivel || 1);
                let textClass = "text-gray-700";
                if (level === 1) {
                    textClass = "font-bold text-gray-900 uppercase mt-2";
                } else if (level === 2) {
                    textClass = "pl-6 text-gray-700";
                } else if (level === 3) {
                    textClass = "pl-12 text-gray-700";
                } else {
                    textClass = "pl-16 text-gray-700";
                }

                row.innerHTML = `
                    <span class="${textClass} flex-shrink-0">${item.titulo}</span>
                    <span class="border-b border-dotted border-gray-400 flex-1 mx-2 relative top-[-4px]"></span>
                    <span class="text-gray-500 text-xs">∞</span>
                `;
                listContainer.appendChild(row);
            });
        }

        if (footer) {
            const lower = (formatId || "").toLowerCase();
            if (lower.startsWith("uni")) {
                footer.textContent = "Estructura referencial basada en normativa UNI";
            } else if (lower.startsWith("unac")) {
                footer.textContent = "Estructura referencial basada en normativa UNAC";
            } else {
                footer.textContent = "Estructura referencial basada en normativa académica";
            }
        }

        loader.classList.add('hidden');
        content.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        const errorRow = document.createElement('div');
        errorRow.className = "text-sm text-red-600";
        errorRow.textContent = "No se pudo cargar el índice.";
        listContainer.appendChild(errorRow);
        loader.classList.add('hidden');
        content.classList.remove('hidden');
    }
}

function closeIndexModal() {
    document.getElementById('indexModal').classList.add('hidden');
}

// --- 5. Visualizador Genérico de Capítulos (I al VII) ---
async function previewChapter(formatId, searchPrefix, sectionObj = null) {
    const modal = document.getElementById('chapterModal');
    const loader = document.getElementById('chapterLoader');
    const content = document.getElementById('chapterContent');
    const listContainer = document.getElementById('chapterList');
    const titleContainer = document.getElementById('chapterTitle');

    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    listContainer.innerHTML = '';

    try {
        const data = await fetchFormatJson(formatId);

        const normalizeKey = (value) => {
            return String(value || "")
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "")
                .replace(/[^a-zA-Z0-9]+/g, " ")
                .trim()
                .toLowerCase()
                .replace(/\s+/g, "_");
        };

        const targetKey = normalizeKey(searchPrefix);

        // BÚSQUEDA INTELIGENTE
        let capitulo = sectionObj || null;
        // 1. Buscar en el cuerpo
        if (!capitulo && Array.isArray(data.cuerpo)) {
            capitulo = data.cuerpo.find(cap => {
                const titleKey = normalizeKey(cap.titulo || cap.title);
                if (!targetKey) return false;
                return titleKey.startsWith(targetKey) || titleKey.includes(targetKey) || targetKey.includes(titleKey);
            });
        }
        // 2. Buscar en secciones (UNI pregrado)
        if (!capitulo && Array.isArray(data.secciones)) {
            capitulo = data.secciones.find(sec => {
                const title = sec.titulo || sec.title;
                const displayTitle = sec.numero ? `${sec.numero}. ${title || ""}` : (title || "");
                const secKey = normalizeKey(displayTitle || title || sec.numero);
                if (!targetKey) return false;
                return secKey.startsWith(targetKey) || secKey.includes(targetKey) || targetKey.includes(secKey);
            });
        }
        // 3. Buscar en finales (Referencias/Anexos)
        if (!capitulo && data.finales) {
            const prefix = (searchPrefix || "").toUpperCase();
            if ((prefix.includes("REFERENCIAS") || prefix.includes("BIBLIOGRAF")) && data.finales.referencias) {
                capitulo = data.finales.referencias;
            } else if (prefix.includes("ANEXO") && data.finales.anexos) {
                capitulo = data.finales.anexos;
            }
        }

        if (typeof capitulo === "string") {
            capitulo = { titulo: capitulo };
        }

        if (!capitulo) {
            titleContainer.textContent = searchPrefix || "Sección";
            const empty = document.createElement('div');
            empty.className = "p-6 bg-gray-50 rounded-lg border border-gray-200 text-center text-gray-600";
            empty.textContent = "Sin vista previa disponible para esta sección.";
            listContainer.appendChild(empty);
            loader.classList.add('hidden');
            content.classList.remove('hidden');
            return;
        }

        // RENDERIZADO
        if (capitulo.numero && capitulo.titulo && !capitulo.titulo.trim().startsWith(String(capitulo.numero))) {
            titleContainer.textContent = `${capitulo.numero}. ${capitulo.titulo}`;
        } else {
            titleContainer.textContent = capitulo.titulo || capitulo.titulo_seccion || capitulo.title || "Capítulo";
        }

        // Caso A: Lista de contenidos
        if (capitulo.contenido && Array.isArray(capitulo.contenido)) {
            capitulo.contenido.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = "p-4 bg-gray-50 rounded-lg border border-gray-100 hover:border-blue-200 transition-colors";

                let html = `<h4 class="font-bold text-gray-800 text-base mb-1">${item.texto || ""}</h4>`;

                const notes = [];
                if (item.instruccion_detallada) notes.push(item.instruccion_detallada);
                if (item.nota) notes.push(item.nota);
                if (item.tabla_nota) notes.push(item.tabla_nota);
                if (Array.isArray(item.imagenes)) {
                    item.imagenes.forEach((img) => {
                        if (img && img.fuente) notes.push(img.fuente);
                    });
                }

                notes.forEach((note) => {
                    const noteText = shortGuide(note);
                    html += `
                        <div class="flex gap-2 mt-2">
                            <span class="text-blue-500 mt-0.5"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></span>
                            <p class="text-gray-600 text-sm italic">${noteText}</p>
                        </div>
                    `;
                });
                itemDiv.innerHTML = html;
                listContainer.appendChild(itemDiv);
            });
        }
        // Caso B: Estructura jerárquica (items/subitems) - Nuevo Formato Posgrado
        else if (capitulo.items && Array.isArray(capitulo.items)) {
            capitulo.items.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = "p-4 bg-gray-50 rounded-lg border border-gray-100 mt-2";

                let html = `<h4 class="font-bold text-gray-800 text-base mb-2">${item.titulo || ""}</h4>`;

                if (item.subitems && Array.isArray(item.subitems)) {
                    html += `<ul class="list-disc pl-5 space-y-1">`;
                    item.subitems.forEach(sub => {
                        html += `<li class="text-gray-700 text-sm">${sub}</li>`;
                    });
                    html += `</ul>`;
                }

                itemDiv.innerHTML = html;
                listContainer.appendChild(itemDiv);
            });
        }
        // Caso C: Plan de Tesis (Instrucción + Lista opcional)
        else if (capitulo.instruccion) {
            const itemDiv = document.createElement('div');
            itemDiv.className = "p-6 bg-blue-50 rounded-lg border border-blue-100";

            let html = `<p class="text-gray-800 text-lg font-medium italic mb-4">"${capitulo.instruccion}"</p>`;

            if (capitulo.lista && Array.isArray(capitulo.lista)) {
                html += `<ul class="list-disc pl-5 space-y-2">`;
                capitulo.lista.forEach(li => {
                    html += `<li class="text-gray-700">${li}</li>`;
                });
                html += `</ul>`;
            }
            itemDiv.innerHTML = html;
            listContainer.appendChild(itemDiv);
        }
        // Caso extra: solo lista sin instrucción
        else if (capitulo.lista && Array.isArray(capitulo.lista)) {
            const itemDiv = document.createElement('div');
            itemDiv.className = "p-6 bg-blue-50 rounded-lg border border-blue-100";
            let html = `<ul class="list-disc pl-5 space-y-2">`;
            capitulo.lista.forEach(li => {
                html += `<li class="text-gray-700">${li}</li>`;
            });
            html += `</ul>`;
            itemDiv.innerHTML = html;
            listContainer.appendChild(itemDiv);
        }
        // Caso D: Texto simple (Conclusiones, etc)
        else if (capitulo.nota_capitulo || capitulo.nota) {
            const texto = capitulo.nota_capitulo || capitulo.nota;
            const itemDiv = document.createElement('div');
            itemDiv.className = "p-6 bg-blue-50 rounded-lg border border-blue-100 text-center";
            itemDiv.innerHTML = `
                <p class="text-gray-800 text-lg font-medium italic">"${texto}"</p>
            `;
            listContainer.appendChild(itemDiv);
        }
        else {
            const empty = document.createElement('div');
            empty.className = "p-6 bg-gray-50 rounded-lg border border-gray-200 text-center text-gray-600";
            empty.textContent = "Sin vista previa disponible para esta sección.";
            listContainer.appendChild(empty);
        }

        loader.classList.add('hidden');
        content.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        const empty = document.createElement('div');
        empty.className = "p-6 bg-gray-50 rounded-lg border border-gray-200 text-center text-gray-600";
        empty.textContent = "Sin vista previa disponible para esta sección.";
        listContainer.appendChild(empty);
        loader.classList.add('hidden');
        content.classList.remove('hidden');
    }
}

function closeChapterModal() {
    document.getElementById('chapterModal').classList.add('hidden');
}

/**
 * Genera dinámicamente la lista de requisitos desde el JSON
 */
async function hydrateRequirementsList() {
    const container = document.getElementById('formatRequirements');
    if (!container) return;

    const formatId = container.dataset.formatId;
    if (!formatId) return;

    try {
        // 1. Obtener datos del JSON
        const data = await fetchFormatJson(formatId);

        // 2. Limpiar contenedor
        container.innerHTML = '';

        // 3. Siempre agregar Carátula e Índice
        container.appendChild(buildRequirementItem(
            "Carátula Institucional",
            "Debe seguir estrictamente el modelo oficial.",
            () => previewCover(formatId)
        ));

        container.appendChild(buildRequirementItem(
            "Índice General",
            "Generado automáticamente por Word con estilos aplicados.",
            () => previewIndex(formatId)
        ));

        // 4. Agregar capítulos del cuerpo (Soporte dual: cuerpo o secciones)
        const chaptersList = data.cuerpo || data.secciones;

        const buildDisplayTitle = (capitulo) => {
            const rawTitle = capitulo?.titulo || capitulo?.title || "";
            const num = capitulo?.numero || capitulo?.romano || "";
            if (num && rawTitle && !rawTitle.trim().startsWith(String(num))) {
                return `${num}. ${rawTitle}`.trim();
            }
            return rawTitle || String(num || "");
        };

        if (chaptersList && Array.isArray(chaptersList)) {
            chaptersList.forEach((capitulo) => {
                // Soporte para secciones simples (nuevo formato UNI)

                // Extraer número romano o arábigo del título
                const rawTitle = capitulo?.titulo || capitulo?.title || "";
                const match = rawTitle.match(/^([IVXLCDM0-9]+)[\.\s]/);
                const prefijo = capitulo?.numero ? `${capitulo.numero}.` : (match ? match[1] + '.' : '');
                const displayTitle = buildDisplayTitle(capitulo);

                // Obtener descripción del capítulo
                let descripcion = "Estructura principal del capítulo.";

                if (capitulo.instruccion) {
                    descripcion = capitulo.instruccion;
                } else if (capitulo.nota_capitulo) {
                    descripcion = capitulo.nota_capitulo;
                } else if (capitulo.contenido && typeof capitulo.contenido === 'string') {
                    // Soporte para contenido simple string (nuevo formato UNI)
                    descripcion = capitulo.contenido;
                } else if (capitulo.contenido && Array.isArray(capitulo.contenido) && capitulo.contenido.length > 0) {
                    // Intentar obtener la primera nota disponible
                    const primerContenido = capitulo.contenido[0];
                    if (primerContenido.instruccion_detallada) {
                        descripcion = primerContenido.instruccion_detallada;
                    } else if (primerContenido.nota) {
                        descripcion = primerContenido.nota;
                    } else if (primerContenido.tabla_nota) {
                        descripcion = primerContenido.tabla_nota;
                    } else if (Array.isArray(primerContenido.imagenes)) {
                        const fuente = primerContenido.imagenes.find(img => img && img.fuente)?.fuente;
                        if (fuente) {
                            descripcion = fuente;
                        }
                    } else if (primerContenido.texto) {
                        descripcion = primerContenido.texto;
                    }
                } else if (capitulo.items && Array.isArray(capitulo.items) && capitulo.items.length > 0) {
                    // Nuevo formato Posgrado con items
                    const primerItem = capitulo.items[0];
                    descripcion = primerItem.titulo || "Estructura del capítulo.";
                    if (capitulo.items.length > 1) {
                        descripcion += ` (+${capitulo.items.length - 1} sub-secciones)`;
                    }
                }
                // Truncar descripción si es muy larga
                if (descripcion.length > 100) {
                    descripcion = descripcion.substring(0, 97) + '...';
                }

                container.appendChild(buildRequirementItem(
                    displayTitle,
                    descripcion,
                    () => previewChapter(formatId, prefijo || displayTitle, capitulo)
                ));
            });
        }

        // 5. Agregar Referencias (buscar en finales o en cuerpo)
        let referenciasTitulo = null;
        let referenciasDescripcion = null;
        let referenciasPrefijo = null;

        // Opción A: Buscar en data.finales.referencias
        if (data.finales?.referencias?.titulo) {
            referenciasTitulo = data.finales.referencias.titulo;
            referenciasDescripcion = data.finales.referencias.nota || "Normativa bibliográfica según corresponda.";
            referenciasPrefijo = "REFERENCIAS"; // Palabra clave para búsqueda
        }
        // Opción B: Buscar en el cuerpo (por si está como capítulo)
        else if (data.cuerpo && Array.isArray(data.cuerpo)) {
            const capituloReferencias = data.cuerpo.find(cap =>
                cap.titulo && (
                    cap.titulo.toUpperCase().includes('REFERENCIAS') ||
                    cap.titulo.toUpperCase().includes('BIBLIOGRAF')
                )
            );

            if (capituloReferencias) {
                referenciasTitulo = capituloReferencias.titulo;
                referenciasDescripcion = capituloReferencias.nota_capitulo || capituloReferencias.nota || "Normativa bibliográfica según corresponda.";
                const match = capituloReferencias.titulo.match(/^([IVXLCDM]+)\./);
                referenciasPrefijo = match ? match[1] + '.' : 'REFERENCIAS';
            }
        }

        // Agregar la tarjeta de Referencias si se encontró
        if (referenciasTitulo) {
            container.appendChild(buildRequirementItem(
                referenciasTitulo,
                referenciasDescripcion,
                () => previewChapter(formatId, referenciasPrefijo)
            ));
        }

        // 6. Agregar Anexos (si existen)
        if (data.finales?.anexos) {
            const anexos = data.finales.anexos;
            const anexosTitulo = anexos.titulo_seccion || "Anexos";
            const anexosDescripcion = anexos.nota_general || anexos.nota || "Documentación complementaria.";

            container.appendChild(buildRequirementItem(
                anexosTitulo,
                anexosDescripcion,
                null // Sin preview por ahora, o puedes crear una función previewAnexos
            ));
        }

        // 7. Reinicializar iconos de Lucide
        if (window.lucide) {
            window.lucide.createIcons();
        }

    } catch (error) {
        console.error("Error cargando requisitos:", error);
        container.innerHTML = `
            <div class="p-6 bg-red-50 text-red-700 rounded-lg border border-red-200">
                <p class="font-semibold">Error cargando estructura del formato</p>
                <p class="text-sm mt-1">${error.message}</p>
            </div>
        `;
    }
}
/**
 * Construye un elemento de requisito individual
 */
function buildRequirementItem(title, description, onPreview) {
    const wrapper = document.createElement('div');
    wrapper.className = "flex items-start gap-4 p-4 rounded-lg bg-gray-50 border border-gray-200 group hover:border-blue-300 transition-colors";

    // Contenido
    const body = document.createElement('div');
    body.className = "flex-1";

    const header = document.createElement('div');
    header.className = "flex items-center justify-between";

    const h4 = document.createElement('h4');
    h4.className = "font-semibold text-gray-900";
    h4.textContent = title;
    header.appendChild(h4);

    // Botón de preview (si existe callback)
    if (onPreview) {
        const btn = document.createElement('button');
        btn.className = "text-gray-400 hover:text-blue-600 transition-colors p-1 rounded-md hover:bg-blue-50";
        btn.title = "Ver detalle";
        btn.innerHTML = '<i data-lucide="eye" class="w-5 h-5"></i>';
        btn.addEventListener('click', onPreview);
        header.appendChild(btn);
    }

    body.appendChild(header);

    // Descripción
    if (description) {
        const p = document.createElement('p');
        p.className = "text-sm text-gray-600 mt-1";
        p.textContent = description;
        body.appendChild(p);
    }

    wrapper.appendChild(body);
    return wrapper;
}

// Ejecutar al cargar la página
document.addEventListener('DOMContentLoaded', hydrateRequirementsList);
