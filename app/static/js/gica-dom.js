/*
Archivo: app/static/js/gica-dom.js
Propósito: Helpers DOM puros para GicaTesis.
API global: window.GicaDom = { byId, setText, setImgSrc, show, hide }
Fase 1: Extracción de helpers sin cambiar comportamiento.
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
