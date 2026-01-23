/*
Archivo: app/static/js/navigation.js
Proposito: Resalta el item activo del sidebar segun active_nav.
Responsabilidades: Leer window.__ACTIVE_NAV__ y aplicar clases CSS.
No hace: No modifica rutas ni carga datos.
Entradas/Salidas: Entradas = valor active_nav; Salidas = clases CSS en DOM.
Donde tocar si falla: Revisar data-nav en templates y asignacion de __ACTIVE_NAV__.
*/

// Activa el item del sidebar segÃºn `active_nav` inyectado por el backend (Jinja)
// En este scaffold, se marca con un atributo data-nav, y el backend pasa `active_nav`.

(function() {
  const active = (window.__ACTIVE_NAV__ || "").toString();
  const items = document.querySelectorAll("[data-nav]");
  items.forEach(el => {
    const key = el.getAttribute("data-nav");
    if (key === active) {
      el.classList.add("bg-blue-50", "text-blue-700");
    } else {
      el.classList.add("text-gray-600", "hover:bg-gray-50", "hover:text-gray-900");
    }
  });
})();

