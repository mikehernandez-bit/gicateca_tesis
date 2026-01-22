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

function isSpecFormat(data) {
  return !!(data && data.content && Array.isArray(data.content.chapters));
}

function shortGuide(text) {
  if (!text) return 'Ver detalle en la vista previa.';
  const line = text.split(/\n+/)[0].trim();
  return line || 'Ver detalle en la vista previa.';
}

function normalizeTitle(text) {
  return (text || '').trim().toUpperCase();
}

function buildStructureFromSpec(data) {
  const structure = [];
  const prelims = Array.isArray(data.preliminaries) ? data.preliminaries : [];
  const wanted = new Set(['toc', 'index_tables', 'index_figures', 'abbreviations']);
  prelims.forEach((p) => {
    if (p && wanted.has(p.type)) {
      structure.push({ titulo: p.title || 'ÍNDICE', nivel: 1 });
    }
  });

  const chapters = data.content && Array.isArray(data.content.chapters) ? data.content.chapters : [];
  chapters.forEach((ch) => {
    if (ch && ch.title) {
      structure.push({ titulo: ch.title, nivel: ch.level || 1 });
    }
    if (ch && Array.isArray(ch.sections)) {
      ch.sections.forEach((sec) => {
        if (sec && sec.title) {
          structure.push({ titulo: sec.title, nivel: sec.level || 2 });
        }
      });
    }
  });

  return structure;
}

function findChapterInSpec(chapters, searchKey) {
  const key = normalizeTitle(searchKey);
  let found = chapters.find((ch) => normalizeTitle(ch.title) === key);
  if (!found) {
    found = chapters.find((ch) => normalizeTitle(ch.title).startsWith(key));
  }
  return found || null;
}

function getCoverFromSpec(data) {
  if (!data || !data.cover || !Array.isArray(data.cover.blocks)) return null;
  const texts = data.cover.blocks
    .filter((b) => b && b.type === 'text' && b.text)
    .map((b) => String(b.text).trim())
    .filter(Boolean);

  if (!texts.length) return null;

  const title = texts.find((t) => t.includes('[T') || t.includes('TÍTULO') || t.includes('TITULO') || t.startsWith('"')) || '';
  const grado = texts.find((t) => t.toUpperCase().includes('TESIS PARA OPTAR')) || '';
  const year = texts.find((t) => /\b(19|20)\d{2}\b/.test(t)) || '';
  const country = texts.slice(-1)[0] || '';

  return {
    universidad: texts[0] || '',
    facultad: texts[1] || '',
    escuela: texts[2] || '',
    titulo_placeholder: title || 'TÍTULO DE INVESTIGACIÓN',
    frase_grado: grado,
    grado_objetivo: '',
    pais: country,
    fecha: year || '2026',
  };
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
    a.download = `UNAC_${formatId.split('-').slice(1).join('_').toUpperCase()}.docx`;
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
    
    if(title) title.innerText = "Vista de Lectura";

    const pdfUrl = `/formatos/${formatId}/pdf`; 
    
    viewer.src = pdfUrl + "#page=1&view=Fit&toolbar=0&navpanes=0"; 
    modal.classList.remove('hidden'); 
}

function closePdfModal() {
    const modal = document.getElementById('pdfModal');
    const viewer = document.getElementById('pdfViewer');
    modal.classList.add('hidden'); 
    viewer.src = ''; 
}

// --- 3. Visualizador de Carátula (JSON) ---
async function previewCover(formatId) {
    const modal = document.getElementById('coverModal');
    const loader = document.getElementById('coverLoader');
    const content = document.getElementById('coverContent');
    
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');

    try {
        const data = await fetchFormatJson(formatId);
        const c = data.caratula || getCoverFromSpec(data);
        if (!c) throw new Error("No se encontró configuración de carátula.");

        document.getElementById('c-uni').textContent = c.universidad || "UNIVERSIDAD NACIONAL DEL CALLAO";
        document.getElementById('c-fac').textContent = c.facultad || "";
        document.getElementById('c-esc').textContent = c.escuela || "";
        document.getElementById('c-titulo').textContent = c.titulo_placeholder || "TÍTULO DE INVESTIGACIÓN";
        document.getElementById('c-frase').textContent = c.frase_grado || "";
        document.getElementById('c-grado').textContent = c.grado_objetivo || "";
        document.getElementById('c-lugar').textContent = (c.pais || "CALLAO, PERÚ");
        document.getElementById('c-anio').textContent = (c.fecha || "2026");

        loader.classList.add('hidden');
        content.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        alert("Error cargando carátula: " + error.message);
        closeCoverModal();
    }
}

function closeCoverModal() {
    document.getElementById('coverModal').classList.add('hidden');
}

// --- 4. Visualizador de Índice (Inteligente) ---
async function previewIndex(formatId) {
    const modal = document.getElementById('indexModal');
    const loader = document.getElementById('indexLoader');
    const content = document.getElementById('indexContent');
    const listContainer = document.getElementById('indexList');
    
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    listContainer.innerHTML = ''; 

    try {
        const data = await fetchFormatJson(formatId);
        let structure = [];

        if (isSpecFormat(data)) {
            structure = buildStructureFromSpec(data);
        } else if (data.estructura) {
            structure = data.estructura;
        } else {
            if (data.preliminares && data.preliminares.introduccion) {
                structure.push({ titulo: data.preliminares.introduccion.titulo, nivel: 1 });
            }
            if (data.cuerpo) {
                data.cuerpo.forEach(cap => {
                    if (cap.titulo) structure.push({ titulo: cap.titulo, nivel: 1 });
                    if (cap.contenido && Array.isArray(cap.contenido)) {
                        cap.contenido.forEach(sub => {
                            if (sub.texto) structure.push({ titulo: sub.texto, nivel: 2 });
                        });
                    }
                });
            }
            if (data.finales) {
                if (data.finales.referencias) structure.push({ titulo: data.finales.referencias.titulo, nivel: 1 });
                if (data.finales.anexos) structure.push({ titulo: data.finales.anexos.titulo_seccion, nivel: 1 });
            }
        }

        structure.forEach(item => {
            const row = document.createElement('div');
            row.className = "flex items-baseline w-full";
            const isMain = item.nivel === 1;
            const textClass = isMain ? "font-bold text-gray-900 uppercase mt-2" : "pl-6 text-gray-700";
            
            row.innerHTML = `
                <span class="${textClass} flex-shrink-0">${item.titulo}</span>
                <span class="border-b border-dotted border-gray-400 flex-1 mx-2 relative top-[-4px]"></span>
                <span class="text-gray-500 text-xs">00</span>
            `;
            listContainer.appendChild(row);
        });

        loader.classList.add('hidden');
        content.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        alert("Error cargando índice: " + error.message);
        closeIndexModal();
    }
}

function closeIndexModal() {
    document.getElementById('indexModal').classList.add('hidden');
}

// --- 5. Visualizador Genérico de Capítulos (I al VII) ---
async function previewChapter(formatId, searchPrefix) {
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

        if (isSpecFormat(data)) {
            const chapters = data.content.chapters || [];
            const capitulo = findChapterInSpec(chapters, searchPrefix);
            if (!capitulo) throw new Error(`No se encontró el capítulo solicitado.`);

            titleContainer.textContent = capitulo.title || "Capítulo";

            const guideText = shortGuide(capitulo.guide || "");
            if (capitulo.guide) {
                const guideDiv = document.createElement('div');
                guideDiv.className = "p-4 bg-blue-50 rounded-lg border border-blue-100 text-sm italic text-gray-700";
                guideDiv.textContent = guideText;
                listContainer.appendChild(guideDiv);
            }

            if (Array.isArray(capitulo.sections) && capitulo.sections.length) {
                capitulo.sections.forEach((sec) => {
                    if (!sec || !sec.title) return;
                    const itemDiv = document.createElement('div');
                    itemDiv.className = "p-4 bg-gray-50 rounded-lg border border-gray-100 hover:border-blue-200 transition-colors";

                    const titleEl = document.createElement('h4');
                    titleEl.className = "font-bold text-gray-800 text-base mb-1";
                    titleEl.textContent = sec.title;
                    itemDiv.appendChild(titleEl);

                    const noteText = shortGuide(sec.guide || "");
                    if (sec.guide) {
                        const noteWrap = document.createElement('div');
                        noteWrap.className = "flex gap-2 mt-2";
                        noteWrap.innerHTML = `
                            <span class="text-blue-500 mt-0.5">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="16" x2="12" y2="12"></line>
                                <line x1="12" y1="8" x2="12.01" y2="8"></line>
                              </svg>
                            </span>
                            <p class="text-gray-600 text-sm italic"></p>
                        `;
                        noteWrap.querySelector('p').textContent = noteText;
                        itemDiv.appendChild(noteWrap);
                    }

                    listContainer.appendChild(itemDiv);
                });
            } else if (!capitulo.guide) {
                const emptyDiv = document.createElement('div');
                emptyDiv.className = "p-4 bg-gray-50 rounded-lg border border-gray-100 text-sm text-gray-600 italic";
                emptyDiv.textContent = "Sin detalles adicionales en la estructura.";
                listContainer.appendChild(emptyDiv);
            }

            loader.classList.add('hidden');
            content.classList.remove('hidden');
            return;
        }
        
        // BÚSQUEDA INTELIGENTE
        let capitulo = null;
        // 1. Buscar en el cuerpo
        if (data.cuerpo) {
            capitulo = data.cuerpo.find(cap => 
                cap.titulo && cap.titulo.trim().toUpperCase().startsWith(searchPrefix)
            );
        }
        // 2. Buscar en finales (Referencias/Anexos)
        if (!capitulo && data.finales) {
            const prefix = (searchPrefix || "").toUpperCase();
            if ((prefix.includes("REFERENCIAS") || prefix.includes("BIBLIOGRAF")) && data.finales.referencias) {
                capitulo = data.finales.referencias;
            } else if (prefix.includes("ANEXO") && data.finales.anexos) {
                capitulo = data.finales.anexos;
            }
        }

        if (!capitulo) throw new Error(`No se encontró el Capítulo ${searchPrefix} en el JSON.`);

        // RENDERIZADO
        titleContainer.textContent = capitulo.titulo || capitulo.titulo_seccion || "Capítulo";

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
        // Caso B: Texto simple (Conclusiones, etc)
        else if (capitulo.nota_capitulo || capitulo.nota) {
            const texto = capitulo.nota_capitulo || capitulo.nota;
            const itemDiv = document.createElement('div');
            itemDiv.className = "p-6 bg-blue-50 rounded-lg border border-blue-100 text-center";
            itemDiv.innerHTML = `
                <p class="text-gray-800 text-lg font-medium italic">"${texto}"</p>
            `;
            listContainer.appendChild(itemDiv);
        }

        loader.classList.add('hidden');
        content.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        alert("Información: " + error.message);
        closeChapterModal();
    }
}

// ESTA ES LA FUNCIÓN QUE FALTABA O FALLABA
function closeChapterModal() {
    document.getElementById('chapterModal').classList.add('hidden');
}

function buildRequirementItem(title, description, checked, onPreview) {
    const wrapper = document.createElement('div');
    wrapper.className = "flex items-start gap-4 p-4 rounded-lg bg-gray-50 border border-gray-200 group hover:border-blue-300 transition-colors";

    const left = document.createElement('div');
    left.className = "mt-1 flex-shrink-0";
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.disabled = true;
    if (checked) {
        checkbox.checked = true;
        checkbox.className = "w-5 h-5 text-blue-600 rounded cursor-not-allowed";
    } else {
        checkbox.className = "w-5 h-5 text-gray-400 rounded";
    }
    left.appendChild(checkbox);
    wrapper.appendChild(left);

    const body = document.createElement('div');
    body.className = "flex-1";
    const header = document.createElement('div');
    header.className = "flex items-center justify-between";

    const h4 = document.createElement('h4');
    h4.className = "font-semibold text-gray-900";
    h4.textContent = title;
    header.appendChild(h4);

    if (onPreview) {
        const btn = document.createElement('button');
        btn.className = "text-gray-400 hover:text-blue-600 transition-colors p-1 rounded-md hover:bg-blue-50";
        btn.title = "Ver detalle";
        btn.innerHTML = '<i data-lucide="eye" class="w-5 h-5"></i>';
        btn.addEventListener('click', onPreview);
        header.appendChild(btn);
    }

    body.appendChild(header);

    if (description) {
        const p = document.createElement('p');
        p.className = "text-sm text-gray-600 mt-1";
        p.textContent = description;
        body.appendChild(p);
    }

    wrapper.appendChild(body);
    return wrapper;
}

async function hydrateRequirementsList() {
    const container = document.getElementById('formatRequirements');
    if (!container) return;
    const formatId = container.dataset.formatId;
    if (!formatId) return;

    try {
        const data = await fetchFormatJson(formatId);
        if (!isSpecFormat(data)) return;

        const chapters = data.content.chapters || [];
        if (!chapters.length) return;

        container.innerHTML = '';
        container.appendChild(buildRequirementItem(
            "Carátula Institucional",
            "Debe seguir estrictamente el modelo del Anexo 1.",
            true,
            () => previewCover(formatId)
        ));
        container.appendChild(buildRequirementItem(
            "Índice General",
            "Generado automáticamente por Word con estilos aplicados.",
            true,
            () => previewIndex(formatId)
        ));

        chapters.forEach((ch) => {
            if (!ch || !ch.title) return;
            container.appendChild(buildRequirementItem(
                ch.title,
                shortGuide(ch.guide || ""),
                false,
                () => previewChapter(formatId, ch.title)
            ));
        });

        if (window.lucide) {
            window.lucide.createIcons();
        }
    } catch (error) {
        console.warn("No se pudo hidratar requisitos:", error);
    }
}

/**
 * Genera dinámicamente la lista de requisitos desde el JSON
 */
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
            true,
            () => previewCover(formatId)
        ));
        
        container.appendChild(buildRequirementItem(
            "Índice General",
            "Generado automáticamente por Word con estilos aplicados.",
            true,
            () => previewIndex(formatId)
        ));
        
        // 4. Agregar capítulos del cuerpo
        if (data.cuerpo && Array.isArray(data.cuerpo)) {
            data.cuerpo.forEach((capitulo) => {
                if (!capitulo.titulo) return;
                
                // Extraer número romano del título (I., II., III., etc.)
                const match = capitulo.titulo.match(/^([IVXLCDM]+)\./);
                const prefijo = match ? match[1] + '.' : '';
                
                // Obtener descripción del capítulo
                let descripcion = "Estructura principal del capítulo.";
                
                if (capitulo.nota_capitulo) {
                    descripcion = capitulo.nota_capitulo;
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
                }
                // Truncar descripción si es muy larga
                if (descripcion.length > 100) {
                    descripcion = descripcion.substring(0, 97) + '...';
                }
                
                container.appendChild(buildRequirementItem(
                    capitulo.titulo,
                    descripcion,
                    false,
                    () => previewChapter(formatId, prefijo || capitulo.titulo)
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
                false,
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
                false,
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
function buildRequirementItem(title, description, checked, onPreview) {
    const wrapper = document.createElement('div');
    wrapper.className = "flex items-start gap-4 p-4 rounded-lg bg-gray-50 border border-gray-200 group hover:border-blue-300 transition-colors";
    
    // Checkbox
    const left = document.createElement('div');
    left.className = "mt-1 flex-shrink-0";
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.disabled = true;
    if (checked) {
        checkbox.checked = true;
        checkbox.className = "w-5 h-5 text-blue-600 rounded cursor-not-allowed";
    } else {
        checkbox.className = "w-5 h-5 text-gray-400 rounded";
    }
    left.appendChild(checkbox);
    wrapper.appendChild(left);
    
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


