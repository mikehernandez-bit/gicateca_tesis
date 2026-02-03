"""
=============================================================================
ARCHIVO: app/core/view_models.py
FASE: 2 - Backend View-Models
=============================================================================

PROPÓSITO:
Construye view-models (datos listos para renderizar) a partir de datos crudos.
Este módulo contiene la lógica de negocio que antes estaba en el frontend,
permitiendo que el cliente sea "tonto" y solo renderice lo que recibe.

FUNCIONES PRINCIPALES:
- build_cover_view_model(format_data, provider) -> dict
  Construye el view-model de carátula con todos los campos resueltos:
  logo_url, universidad, facultad, escuela, titulo, frase, grado,
  lugar, anio, autor, asesor, guia.
  
- normalize_logo_path(ruta_logo) -> str | None
  Normaliza rutas de logo para que comiencen con /static/.
  Ej: "app/static/assets/Logo.png" -> "/static/assets/Logo.png"

COMUNICACIÓN CON OTROS MÓDULOS:
- RECIBE datos de:
  - app/core/loaders.py (format_data via load_format_by_id)
  - app/core/registry.py (provider via get_provider)
  
- Es CONSUMIDO por:
  - app/modules/formats/router.py (endpoint GET /cover-model)
  - tests/test_cover_view_model.py

CADENA DE FALLBACKS PARA LOGO:
1. format_data["configuracion"]["ruta_logo"] (normalizado)
2. provider.default_logo_url
3. "/static/assets/LogoGeneric.png"

CADENA DE FALLBACKS PARA OTROS CAMPOS:
1. format_data["caratula"][campo]
2. provider.defaults[campo]
3. String vacío ""

=============================================================================
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Regex para encontrar años 1900-2099
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def normalize_logo_path(ruta_logo: Optional[str]) -> Optional[str]:
    """
    Normaliza una ruta de logo para que comience con /static/.
    
    Casos manejados:
    - "app/static/assets/Logo.png" -> "/static/assets/Logo.png"
    - "/static/assets/Logo.png" -> sin cambio
    - "C:/path/to/static/assets/Logo.png" -> "/static/assets/Logo.png"
    """
    if not ruta_logo:
        return None
    
    ruta = str(ruta_logo).strip()
    if not ruta:
        return None
    
    # Caso 1: empieza con "app/static/"
    if ruta.startswith("app/static/"):
        return "/static/" + ruta[len("app/static/"):]
    
    # Caso 2: ya empieza con "/static/"
    if ruta.startswith("/static/"):
        return ruta
    
    # Caso 3: contiene "/static/" en algún lugar
    idx = ruta.find("/static/")
    if idx != -1:
        return ruta[idx:]
    
    # Caso 4: no es una ruta de static válida
    return None


def build_cover_view_model(format_data: Dict[str, Any], provider: Any) -> Dict[str, str]:
    """
    Construye el view-model de carátula listo para renderizar.
    
    Args:
        format_data: Diccionario del formato JSON completo.
        provider: UniversityProvider con defaults y default_logo_url.
    
    Returns:
        Dict con todos los campos resueltos para la carátula.
    """
    # Extraer secciones
    c = format_data.get("caratula") or {}
    cfg = format_data.get("configuracion") or {}
    
    # Obtener defaults del provider (defensivo)
    provider_defaults = getattr(provider, "defaults", {}) or {}
    provider_logo = getattr(provider, "default_logo_url", "/static/assets/LogoGeneric.png")
    
    # =========================================================================
    # UNIVERSIDAD
    # =========================================================================
    universidad = (
        c.get("universidad")
        or provider_defaults.get("universidad", "")
        or getattr(provider, "display_name", "")
    )
    
    # =========================================================================
    # CAMPOS PRINCIPALES
    # =========================================================================
    facultad = c.get("facultad") or ""
    escuela = c.get("escuela") or ""
    
    titulo = (
        c.get("titulo_placeholder")
        or c.get("titulo")
        or c.get("titulo_proyecto")
        or c.get("titulo_tesis")
        or "TÍTULO DEL PROYECTO"
    )
    
    frase = c.get("frase_grado") or c.get("frase") or ""
    grado = c.get("grado_objetivo") or c.get("carrera") or c.get("grado") or ""
    guia = (c.get("guia") or c.get("nota") or "").strip()
    
    # =========================================================================
    # AUTOR Y ASESOR
    # =========================================================================
    autor = c.get("autor") or ""
    asesor = c.get("asesor") or ""
    
    # =========================================================================
    # LUGAR Y AÑO
    # =========================================================================
    lugar = ""
    anio = ""
    
    # Intentar extraer de lugar_fecha
    lugar_fecha = c.get("lugar_fecha")
    if lugar_fecha:
        s = str(lugar_fecha)
        year_match = _YEAR_RE.search(s)
        if year_match:
            anio = year_match.group(0)
            # Limpiar lugar: quitar año, guiones, comas, saltos, espacios múltiples
            lugar = s.replace(anio, "").replace("-", " ").replace(",", " ")
            lugar = " ".join(lugar.split()).strip()
        else:
            lugar = s.strip()
    
    # Fallback a campos separados
    if not lugar:
        lugar = c.get("lugar") or c.get("pais") or ""
    if not anio:
        anio = c.get("anio") or c.get("fecha") or ""
    
    # Fallback a defaults del provider
    if not lugar:
        lugar = provider_defaults.get("lugar", "")
    if not anio:
        anio = provider_defaults.get("anio", "")
    
    # Warning si aún están vacíos
    if not lugar:
        logger.warning("build_cover_view_model: lugar vacío para formato")
    if not anio:
        logger.warning("build_cover_view_model: año vacío para formato")
    
    # =========================================================================
    # LOGO URL
    # =========================================================================
    ruta_logo = cfg.get("ruta_logo")
    logo_url = normalize_logo_path(ruta_logo)
    
    if not logo_url:
        logo_url = provider_logo
    
    if not logo_url:
        logo_url = "/static/assets/LogoGeneric.png"
    
    # =========================================================================
    # RESULTADO FINAL
    # =========================================================================
    return {
        "logo_url": logo_url,
        "universidad": universidad,
        "facultad": facultad,
        "escuela": escuela,
        "titulo": titulo,
        "frase": frase,
        "grado": grado,
        "lugar": lugar,
        "anio": anio,
        "autor": autor,
        "asesor": asesor,
        "guia": guia,
    }
