"""
Archivo: app/core/format_builder.py
Proposito:
- Centraliza constantes, etiquetas y funciones de construccion de formatos.

Responsabilidades:
- Definir TIPO_LABELS, ENFOQUE_LABELS, TIPO_FILTRO (fuente unica de verdad).
- Construir titulo visible y dict de entrada de formato.
- Resolver aliases de categorias.
No hace:
- No accede a HTTP ni a templates.
- No ejecuta generadores ni gestiona cache.

Entradas/Salidas:
- Entradas: item de indice (FormatIndexItem) y data JSON.
- Salidas: dict listo para UI/API.

Dependencias:
- Ninguna externa. Solo tipos de Python estandar.

Puntos de extension:
- Agregar nuevas categorias o etiquetas al catalogo.

Donde tocar si falla:
- Revisar mapping de categorias y logica de fallback en _build_format_entry.
"""

from typing import Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES UNIFICADAS (fuente unica de verdad)
# ─────────────────────────────────────────────────────────────────────────────

ALIASES: Dict[str, str] = {
    "pregrado": "informe",
}

TIPO_LABELS: Dict[str, str] = {
    "informe": "Informe de Tesis",
    "maestria": "Tesis de Maestría",
    "posgrado": "Posgrado",
    "proyecto": "Proyecto de Tesis",
}

ENFOQUE_LABELS: Dict[str, str] = {
    "cual": "Cualitativo",
    "cuant": "Cuantitativo",
}

TIPO_FILTRO: Dict[str, str] = {
    "informe": "Informe de Tesis",
    "maestria": "Tesis de Postgrado",
    "posgrado": "Tesis de Postgrado",
    "proyecto": "Proyecto de Tesis",
}


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES DE CONSTRUCCION
# ─────────────────────────────────────────────────────────────────────────────

def normalize_format_type(fmt_type: str) -> str:
    """Normaliza el tipo de formato aplicando aliases (pregrado -> informe)."""
    fmt_type = (fmt_type or "").strip().lower()
    return ALIASES.get(fmt_type, fmt_type)


def build_format_title(
    categoria: str,
    enfoque: str,
    raw_title: Optional[str],
    fallback_title: Optional[str],
) -> str:
    """
    Calcula el titulo visible de un formato.

    Prioridad: raw_title > label compuesto > fallback > capitalize.
    """
    if raw_title:
        return raw_title
    cat_label = TIPO_LABELS.get(categoria)
    enfoque_label = ENFOQUE_LABELS.get(enfoque)
    if cat_label and enfoque_label:
        return f"{cat_label} - {enfoque_label}"
    if cat_label:
        return cat_label
    return fallback_title or categoria.capitalize()


def build_format_entry(item, data: Dict) -> Dict:
    """
    Construye el dict unificado para UI (catalogo y detalle).

    Lee _meta del JSON cuando existe, con fallback a campos del item.
    Esta es la VERSION CANONICA que reemplaza las dos versiones previas
    en catalog/service.py y formats/service.py.
    """
    meta = data.get("_meta", {}) if isinstance(data, dict) else {}

    # Titulo: preferir _meta.title > data.titulo > generar
    raw_title = meta.get("title") or (data.get("titulo") if isinstance(data, dict) else None)
    titulo = build_format_title(item.categoria, item.enfoque, raw_title, item.titulo)

    # Categoria: preferir _meta.category > TIPO_LABELS
    category_from_meta = meta.get("category")
    cat_label = category_from_meta or TIPO_LABELS.get(item.categoria, item.categoria.capitalize())

    enfoque_label = ENFOQUE_LABELS.get(item.enfoque)

    # Resumen
    resumen = None
    if isinstance(data, dict):
        resumen = data.get("descripcion")
    if not resumen:
        if enfoque_label:
            resumen = f"Plantilla oficial de {cat_label} con enfoque {enfoque_label}"
        else:
            resumen = f"Plantilla oficial de {cat_label}"

    # Facultad y escuela: JSON > caratula > escalable por universidad
    caratula = data.get("caratula", {}) if isinstance(data, dict) else {}
    facultad = None
    escuela = None
    if isinstance(data, dict):
        facultad = data.get("facultad")
        escuela = data.get("escuela")
    if not facultad and isinstance(caratula, dict):
        facultad = caratula.get("facultad")
        escuela = escuela or caratula.get("escuela")

    # Leyenda uniforme y escalable por universidad
    uni_code = meta.get("university") or item.uni
    if uni_code:
        facultad = f"Centro de Formatos {uni_code.upper()}"
    if not facultad:
        facultad = "Centro de Formatos"
    if not escuela:
        escuela = "Dirección Académica"

    return {
        "id": meta.get("id") or item.format_id,
        "uni": (meta.get("university") or item.uni).upper(),
        "uni_code": meta.get("university") or item.uni,
        "tipo": category_from_meta or TIPO_FILTRO.get(item.categoria, "Otros"),
        "categoria": category_from_meta or item.categoria,
        "titulo": titulo,
        "facultad": facultad,
        "escuela": escuela,
        "estado": "VIGENTE",
        "version": data.get("version", "1.0.0") if isinstance(data, dict) else "1.0.0",
        "fecha": (data.get("fecha") if isinstance(data, dict) and data.get("fecha") else "2026-01-17"),
        "resumen": resumen,
        "tipo_formato": item.categoria,
        "enfoque": meta.get("documentType") or item.enfoque,
    }
