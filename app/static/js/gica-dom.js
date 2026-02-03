/**
 * =============================================================================
 * ARCHIVO: app/static/js/gica-dom.js
 * FASE: 1 - Limpieza JS
 * =============================================================================
 * 
 * PROPÓSITO:
 * Módulo de helpers DOM puros para manipulación de elementos HTML.
 * Centraliza operaciones comunes para evitar duplicación en otros módulos.
 * 
 * API GLOBAL:
 * window.GicaDom = {
 *   byId(id)           -> Obtiene elemento por ID (null-safe)
 *   setText(id, value) -> Establece textContent de un elemento
 *   setImgSrc(id, src) -> Establece src de una imagen
 *   show(elOrId)       -> Remueve clase 'hidden' (muestra elemento)
 *   hide(elOrId)       -> Agrega clase 'hidden' (oculta elemento)
 * }
 * 
 * COMUNICACIÓN CON OTROS MÓDULOS:
 * - Este módulo NO tiene dependencias (es la base del stack JS).
 * - Es CONSUMIDO por:
 *   - gica-api.js (opcional, para mostrar errores)
 *   - cover-preview.js (manipulación del modal de carátula)
 *   - Cualquier módulo futuro que necesite manipular DOM
 * 
 * ORDEN DE CARGA (en base.html):
 * 1. gica-dom.js    <- ESTE ARCHIVO (primero)
 * 2. gica-api.js
 * 3. cover-preview.js
 * 4. navigation.js
 * 
 * =============================================================================
 */

(function () {
    'use strict';

    /**
     * Obtiene un elemento por ID.
     * @param {string} id - ID del elemento
     * @returns {HTMLElement|null}
     */
    function byId(id) {
        return document.getElementById(id);
    }

    /**
     * Establece el textContent de un elemento por ID.
     * @param {string} id - ID del elemento
     * @param {*} value - Valor a establecer (se convierte a string)
     */
    function setText(id, value) {
        var el = byId(id);
        if (el) {
            el.textContent = (value != null) ? String(value) : "";
        } else {
            console.warn('[GicaDom] Elemento no encontrado: #' + id);
        }
    }

    /**
     * Establece el src de una imagen por ID.
     * @param {string} id - ID del elemento img
     * @param {string} src - URL de la imagen
     */
    function setImgSrc(id, src) {
        var el = byId(id);
        if (el && typeof src === 'string') {
            el.src = src;
        } else if (!el) {
            console.warn('[GicaDom] Imagen no encontrada: #' + id);
        }
    }

    /**
     * Muestra un elemento removiendo clase 'hidden'.
     * @param {HTMLElement|string} elOrId - Elemento o ID
     */
    function show(elOrId) {
        var el = (typeof elOrId === 'string') ? byId(elOrId) : elOrId;
        if (el) {
            el.classList.remove('hidden');
        }
    }

    /**
     * Oculta un elemento agregando clase 'hidden'.
     * @param {HTMLElement|string} elOrId - Elemento o ID
     */
    function hide(elOrId) {
        var el = (typeof elOrId === 'string') ? byId(elOrId) : elOrId;
        if (el) {
            el.classList.add('hidden');
        }
    }

    // Exposición global
    window.GicaDom = {
        byId: byId,
        setText: setText,
        setImgSrc: setImgSrc,
        show: show,
        hide: hide
    };

})();
