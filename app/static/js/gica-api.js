/*
Archivo: app/static/js/gica-api.js
Propósito: Wrapper de fetch para GicaTesis.
API global: window.GicaApi = { withCacheBuster, fetchJson }
Fase 1: Centraliza lógica de fetch sin cambiar comportamiento.
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
