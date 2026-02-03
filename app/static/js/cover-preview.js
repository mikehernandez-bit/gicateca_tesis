/*
Archivo: app/static/js/cover-preview.js
Propósito: Controlador unificado para el modal de carátula institucional.
API global: window.GicaCover = { open(formatId), close() }
Compatibilidad: window.previewCover(formatId) = alias de GicaCover.open
Dependencias: GicaDom, GicaApi (deben cargarse antes)
Fase 2: Consume /formatos/{id}/cover-model, sin hardcodes UNI/UNAC.
*/

(function () {
    'use strict';

    // =========================================================================
    // VERIFICACIÓN DE DEPENDENCIAS
    // =========================================================================

    if (typeof window.GicaDom === 'undefined') {
        console.error('[GicaCover] Error: GicaDom no está cargado. Asegúrese de cargar gica-dom.js antes.');
    }
    if (typeof window.GicaApi === 'undefined') {
        console.error('[GicaCover] Error: GicaApi no está cargado. Asegúrese de cargar gica-api.js antes.');
    }

    // Alias locales para mejor legibilidad
    var Dom = window.GicaDom || {};
    var Api = window.GicaApi || {};

    // =========================================================================
    // CORE LOGIC (Fase 2: Sin hardcodes, consume view-model)
    // =========================================================================

    /**
     * Abre el modal de carátula para un formato dado.
     * Consume el endpoint /formatos/{id}/cover-model que retorna datos ya resueltos.
     */
    async function openCover(formatId) {
        var modal = Dom.byId('coverModal');
        var loader = Dom.byId('coverLoader');
        var content = Dom.byId('coverContent');

        if (!modal) {
            console.warn('[GicaCover] Modal #coverModal no encontrado.');
            return;
        }

        // Mostrar modal y loader
        Dom.show(modal);
        Dom.show(loader);
        Dom.hide(content);

        try {
            // Fase 2: Consumir view-model con cache-buster
            var url = '/formatos/' + encodeURIComponent(formatId) + '/cover-model';
            var data = await Api.fetchJson(url, { cacheBuster: true });

            // =========================================================================
            // PINTAR DOM (datos ya resueltos por backend)
            // =========================================================================

            // Logo
            Dom.setImgSrc('c-logo', data.logo_url);

            // Textos principales
            Dom.setText('c-uni', data.universidad);
            Dom.setText('c-fac', data.facultad);
            Dom.setText('c-esc', data.escuela);
            Dom.setText('c-titulo', data.titulo);
            Dom.setText('c-frase', data.frase);
            Dom.setText('c-grado', data.grado);
            Dom.setText('c-lugar', data.lugar);
            Dom.setText('c-anio', data.anio);

            // Guía (mostrar/ocultar)
            var guiaEl = Dom.byId('c-guia');
            if (guiaEl) {
                guiaEl.textContent = data.guia || "";
                if (data.guia) Dom.show(guiaEl); else Dom.hide(guiaEl);
            }

            // Escuela (ocultar si vacío)
            var escEl = Dom.byId('c-esc');
            if (escEl) {
                if (!data.escuela) Dom.hide(escEl); else Dom.show(escEl);
            }

            // Autor/Asesor UI
            var autorEl = Dom.byId('c-autor');
            var asesorEl = Dom.byId('c-asesor');

            if (autorEl) {
                autorEl.textContent = data.autor || "[Nombres y Apellidos]";
                autorEl.classList.toggle('text-gray-400', !data.autor);
            }
            if (asesorEl) {
                asesorEl.textContent = data.asesor || "[Grado y Nombre del Asesor]";
                asesorEl.classList.toggle('text-gray-400', !data.asesor);
            }

            // Mostrar contenido, ocultar loader
            Dom.hide(loader);
            Dom.show(content);

        } catch (error) {
            console.error('[GicaCover] Error:', error);
            Dom.hide(loader);
            closeCover();
            alert('Error cargando carátula: ' + (error.message || error));
        }
    }

    /**
     * Cierra el modal de carátula.
     */
    function closeCover() {
        var modal = Dom.byId('coverModal');
        if (modal) Dom.hide(modal);
    }

    // =========================================================================
    // EXPOSICIÓN GLOBAL
    // =========================================================================

    window.GicaCover = {
        open: openCover,
        close: closeCover
    };

    // Compatibilidad: alias global para llamadas existentes
    window.previewCover = function (formatId) {
        return window.GicaCover.open(formatId);
    };

    // Compatibilidad adicional para closeModal('coverModal')
    window.closeCoverModal = function () {
        closeCover();
    };

})();
