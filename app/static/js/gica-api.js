/**
 * =============================================================================
 * ARCHIVO: app/static/js/gica-api.js
 * FASE: 1 - Limpieza JS
 * =============================================================================
 * 
 * PROPÓSITO:
 * Wrapper centralizado para peticiones HTTP (fetch) con manejo automático de:
 * - Cache-busting (evita respuestas cacheadas agregando ?t=timestamp)
 * - Parsing JSON automático
 * - Manejo de errores HTTP
 * 
 * API GLOBAL:
 * window.GicaApi = {
 *   withCacheBuster(url) -> Agrega ?t=Date.now() a la URL
 *   fetchJson(url, opts) -> Fetch + parse JSON + manejo de errores
 *                           opts.cacheBuster = true para agregar timestamp
 * }
 * 
 * COMUNICACIÓN CON OTROS MÓDULOS:
 * - NO depende de otros módulos JS (es base).
 * - Es CONSUMIDO por:
 *   - cover-preview.js (para obtener /formatos/{id}/cover-model)
 *   - Cualquier módulo futuro que necesite hacer peticiones API
 * 
 * ENDPOINTS QUE TÍPICAMENTE CONSUME:
 * - GET /formatos/{id}/cover-model -> View-model de carátula (Fase 2)
 * - GET /formatos/{id}/data        -> Datos crudos del formato (legacy)
 * 
 * ORDEN DE CARGA (en base.html):
 * 1. gica-dom.js
 * 2. gica-api.js    <- ESTE ARCHIVO
 * 3. cover-preview.js
 * 4. navigation.js
 * 
 * =============================================================================
 */

(function () {
    'use strict';

    /**
     * Agrega un parámetro de cache-buster a una URL.
     * @param {string} url - URL original
     * @returns {string} URL con parámetro t=timestamp
     */
    function withCacheBuster(url) {
        if (!url) return url;
        var separator = url.indexOf('?') === -1 ? '?' : '&';
        return url + separator + 't=' + Date.now();
    }

    /**
     * Realiza un fetch y parsea JSON.
     * @param {string} url - URL a consultar
     * @param {Object} options - Opciones
     * @param {boolean} [options.cacheBuster=true] - Si agregar cache buster
     * @returns {Promise<Object>} Datos JSON parseados
     * @throws {Error} Si la respuesta no es ok o hay error de parsing
     */
    async function fetchJson(url, options) {
        options = options || {};
        var useCacheBuster = options.cacheBuster !== false;

        var finalUrl = useCacheBuster ? withCacheBuster(url) : url;

        try {
            var response = await fetch(finalUrl);

            if (!response.ok) {
                throw new Error('Error HTTP ' + response.status + ' en ' + url);
            }

            var data = await response.json();
            return data;

        } catch (error) {
            console.error('[GicaApi] Error en fetchJson:', url, error);
            throw error;
        }
    }

    // Exposición global
    window.GicaApi = {
        withCacheBuster: withCacheBuster,
        fetchJson: fetchJson
    };

})();
