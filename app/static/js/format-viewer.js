/*
Archivo: app/static/js/format-viewer.js
Proposito: Maneja la vista detalle de formatos (descarga, previews y requisitos).
Responsabilidades: Consumir /formatos/{id}/data, abrir modales y construir UI dinamica.
No hace: No genera documentos en servidor ni modifica datos.
Entradas/Salidas: Entradas = eventos UI; Salidas = cambios DOM, descargas y modales.
Donde tocar si falla: Revisar fetchFormatJson, previewCover/previewIndex/previewChapter y hydrateRequirementsList.
*/

/**
 * LÃ³gica para visualizaciÃ³n y descarga de formatos.
 * Maneja: Word (Descarga), PDF (Preview), CarÃ¡tula (JSON), Ãndice (JSON) y CapÃ­tulos (JSON).
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
    a.download = `UNAC_${formatId.split('-').slice(1).join('_').toUpperCase()}.docx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
    
    btnText.textContent = 'Descargado âœ“';
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

// --- 3. Visualizador de CarÃ¡tula (JSON) ---
async function previewCover(formatId) {
    const modal = document.getElementById('coverModal');
    const loader = document.getElementById('coverLoader');
    const content = document.getElementById('coverContent');
    
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');

    try {
        const data = await fetchFormatJson(formatId);
        const c = data.caratula || {};
        if (!Object.keys(c).length) throw new Error("No se encontrÃ³ configuraciÃ³n de carÃ¡tula.");

        document.getElementById('c-uni').textContent = c.universidad || "UNIVERSIDAD NACIONAL DEL CALLAO";
        document.getElementById('c-fac').textContent = c.facultad || "";
        document.getElementById('c-esc').textContent = c.escuela || "";
        document.getElementById('c-titulo').textContent = c.titulo_placeholder || "TÃTULO DE INVESTIGACIÃ“N";
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
        console.error(error);
        alert("Error cargando carÃ¡tula: " + error.message);
        closeCoverModal();
    }
}

function closeCoverModal() {
    document.getElementById('coverModal').classList.add('hidden');
}

// --- 4. Visualizador de Ãndice (Inteligente) ---
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

        if (data.estructura) {
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
        alert("Error cargando Ã­ndice: " + error.message);
        closeIndexModal();
    }
}

function closeIndexModal() {
    document.getElementById('indexModal').classList.add('hidden');
}

// --- 5. Visualizador GenÃ©rico de CapÃ­tulos (I al VII) ---
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

        // BÃšSQUEDA INTELIGENTE
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

        if (!capitulo) throw new Error(`No se encontrÃ³ el CapÃ­tulo ${searchPrefix} en el JSON.`);

        // RENDERIZADO
        titleContainer.textContent = capitulo.titulo || capitulo.titulo_seccion || "CapÃ­tulo";

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
        alert("InformaciÃ³n: " + error.message);
        closeChapterModal();
    }
}

// ESTA ES LA FUNCIÃ“N QUE FALTABA O FALLABA
function closeChapterModal() {
    document.getElementById('chapterModal').classList.add('hidden');
}

/**
 * Genera dinÃ¡micamente la lista de requisitos desde el JSON
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
        
        // 3. Siempre agregar CarÃ¡tula e Ãndice
        container.appendChild(buildRequirementItem(
            "CarÃ¡tula Institucional",
            "Debe seguir estrictamente el modelo oficial.",
            () => previewCover(formatId)
        ));
        
        container.appendChild(buildRequirementItem(
            "Ãndice General",
            "Generado automÃ¡ticamente por Word con estilos aplicados.",
            () => previewIndex(formatId)
        ));
        
        // 4. Agregar capÃ­tulos del cuerpo
        if (data.cuerpo && Array.isArray(data.cuerpo)) {
            data.cuerpo.forEach((capitulo) => {
                if (!capitulo.titulo) return;
                
                // Extraer nÃºmero romano del tÃ­tulo (I., II., III., etc.)
                const match = capitulo.titulo.match(/^([IVXLCDM]+)\./);
                const prefijo = match ? match[1] + '.' : '';
                
                // Obtener descripciÃ³n del capÃ­tulo
                let descripcion = "Estructura principal del capÃ­tulo.";
                
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
                // Truncar descripciÃ³n si es muy larga
                if (descripcion.length > 100) {
                    descripcion = descripcion.substring(0, 97) + '...';
                }
                
                container.appendChild(buildRequirementItem(
                    capitulo.titulo,
                    descripcion,
                    () => previewChapter(formatId, prefijo || capitulo.titulo)
                ));
            });
        }
        
        // 5. Agregar Referencias (buscar en finales o en cuerpo)
        let referenciasTitulo = null;
        let referenciasDescripcion = null;
        let referenciasPrefijo = null;
        
        // OpciÃ³n A: Buscar en data.finales.referencias
        if (data.finales?.referencias?.titulo) {
            referenciasTitulo = data.finales.referencias.titulo;
            referenciasDescripcion = data.finales.referencias.nota || "Normativa bibliogrÃ¡fica segÃºn corresponda.";
            referenciasPrefijo = "REFERENCIAS"; // Palabra clave para bÃºsqueda
        } 
        // OpciÃ³n B: Buscar en el cuerpo (por si estÃ¡ como capÃ­tulo)
        else if (data.cuerpo && Array.isArray(data.cuerpo)) {
            const capituloReferencias = data.cuerpo.find(cap => 
                cap.titulo && (
                    cap.titulo.toUpperCase().includes('REFERENCIAS') ||
                    cap.titulo.toUpperCase().includes('BIBLIOGRAF')
                )
            );
            
            if (capituloReferencias) {
                referenciasTitulo = capituloReferencias.titulo;
                referenciasDescripcion = capituloReferencias.nota_capitulo || capituloReferencias.nota || "Normativa bibliogrÃ¡fica segÃºn corresponda.";
                const match = capituloReferencias.titulo.match(/^([IVXLCDM]+)\./);
                referenciasPrefijo = match ? match[1] + '.' : 'REFERENCIAS';
            }
        }
        
        // Agregar la tarjeta de Referencias si se encontrÃ³
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
            const anexosDescripcion = anexos.nota_general || anexos.nota || "DocumentaciÃ³n complementaria.";
            
            container.appendChild(buildRequirementItem(
                anexosTitulo,
                anexosDescripcion,
                null // Sin preview por ahora, o puedes crear una funciÃ³n previewAnexos
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
    
    // BotÃ³n de preview (si existe callback)
    if (onPreview) {
        const btn = document.createElement('button');
        btn.className = "text-gray-400 hover:text-blue-600 transition-colors p-1 rounded-md hover:bg-blue-50";
        btn.title = "Ver detalle";
        btn.innerHTML = '<i data-lucide="eye" class="w-5 h-5"></i>';
        btn.addEventListener('click', onPreview);
        header.appendChild(btn);
    }
    
    body.appendChild(header);
    
    // DescripciÃ³n
    if (description) {
        const p = document.createElement('p');
        p.className = "text-sm text-gray-600 mt-1";
        p.textContent = description;
        body.appendChild(p);
    }
    
    wrapper.appendChild(body);
    return wrapper;
}

// Ejecutar al cargar la pÃ¡gina
document.addEventListener('DOMContentLoaded', hydrateRequirementsList);



