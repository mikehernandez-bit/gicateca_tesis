#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de maestria UNAC (legacy-style).
- Espera JSON con schema legacy: caratula/preliminares/cuerpo/finales.
- Mantiene flujo y secciones similares a generador_informe_tesis.py.
"""
import json
import os
import re
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Inches

from generador_informe_tesis import (
    configurar_seccion_unac,
    configurar_estilos_base,
    agregar_bloque,
    agregar_titulo_formal,
    agregar_nota_estilizada,
    imprimir_ejemplos_apa,
    crear_tabla_matriz_consistencia,
    _add_fldSimple,
    _insertar_n,
)
from generador_proyecto_tesis import (
    crear_tabla_estilizada,
    agregar_nota_guia,
    encontrar_recurso,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORMATS_DIR = os.path.join(BASE_DIR, "formats")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FALLBACK_FIGURE_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", "static", "assets", "figura_ejemplo.png"))


# ==========================================
# CARGA JSON
# ==========================================

def cargar_contenido(path_archivo):
    if not os.path.exists(path_archivo):
        nombre = os.path.basename(path_archivo)
        path_archivo = os.path.join(FORMATS_DIR, nombre)
    if not os.path.exists(path_archivo):
        raise FileNotFoundError(f"No se encontro el JSON en: {path_archivo}")
    try:
        with open(path_archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error de sintaxis en el archivo JSON: {e}")


# ==========================================
# CARATULA
# ==========================================

def crear_caratula_dinamica(doc, data):
    c = data.get("caratula", {})
    agregar_bloque(doc, c.get("universidad", ""), negrita=True, tamano=16, despues=4)
    agregar_bloque(doc, c.get("facultad", ""), negrita=True, tamano=13, despues=4)
    agregar_bloque(doc, c.get("escuela", ""), negrita=True, tamano=13, despues=14)

    ruta_logo = os.path.join(ASSETS_DIR, "LogoUNAC.png")
    if os.path.exists(ruta_logo):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(ruta_logo, width=Inches(2.4))

    agregar_bloque(doc, c.get("tipo_documento", ""), negrita=True, tamano=15, antes=22)
    agregar_bloque(doc, c.get("titulo_placeholder", ""), negrita=True, tamano=14, antes=14, despues=14)

    if c.get("guia"):
        agregar_nota_estilizada(doc, c.get("guia"))

    frase = c.get("frase_grado") or "PARA OPTAR EL GRADO ACADEMICO DE:"
    agregar_bloque(doc, frase, tamano=11, antes=10)
    agregar_bloque(doc, c.get("grado_objetivo", ""), negrita=True, tamano=12, despues=20)
    agregar_bloque(doc, c.get("label_autor", ""), negrita=True, tamano=11, despues=3)
    agregar_bloque(doc, c.get("label_asesor", ""), negrita=True, tamano=11, despues=10)
    agregar_bloque(doc, c.get("label_linea", ""), tamano=10, despues=16)
    agregar_bloque(doc, c.get("fecha", ""), tamano=11)
    agregar_bloque(doc, c.get("pais", ""), negrita=True, tamano=11)


# ==========================================
# PRELIMINARES
# ==========================================

def _add_label_value(doc, label, value):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(label or "")
    run.bold = True
    p.add_run(" ")
    p.add_run(value or "")


def agregar_titulo_preliminar(doc, texto):
    if not texto:
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(texto)
    run.bold = True
    run.font.name = 'Arial'
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)

def agregar_informacion_basica(doc, info, add_page_break=True):
    if not info:
        return
    agregar_titulo_preliminar(doc, info.get("titulo", "INFORMACION BASICA"))
    for item in info.get("elementos", []):
        _add_label_value(doc, item.get("label", ""), item.get("valor", ""))
    if add_page_break:
        doc.add_page_break()


def agregar_hoja_jurado(doc, data, add_page_break=True):
    if not data:
        return
    agregar_titulo_preliminar(doc, data.get("titulo", "HOJA DE REFERENCIA DEL JURADO Y APROBACION"))

    miembros = data.get("miembros", [])
    for miembro in miembros:
        rol = miembro.get("role", "")
        nombre = miembro.get("name", "")
        _add_label_value(doc, f"{rol}:", nombre)

    asesor = data.get("asesor")
    if asesor:
        _add_label_value(doc, "ASESOR:", asesor)

    acta = data.get("acta", {})
    if acta:
        _add_label_value(doc, "LIBRO:", acta.get("libro", ""))
        _add_label_value(doc, "ACTAS:", acta.get("actas", ""))
        _add_label_value(doc, "FOLIO:", acta.get("folio", ""))
        _add_label_value(doc, "FECHA:", acta.get("fecha", ""))
        _add_label_value(doc, "RESOLUCION:", acta.get("resolucion", ""))

    if add_page_break:
        doc.add_page_break()


def agregar_titulo_indice(doc, texto):
    if not texto:
        return
    h = doc.add_heading(texto, level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if h.runs:
        h.runs[0].font.name = 'Arial'
        h.runs[0].font.size = Pt(14)
        h.runs[0].bold = True
        h.runs[0].font.color.rgb = RGBColor(0, 0, 0)



def _strip_caption_prefix(label, texto):
    if not texto:
        return ""
    t = texto.strip()
    if t.lower().startswith(label.lower()):
        t = t[len(label):].lstrip()
        t = re.sub(r"^[0-9IVXLCDM]+([\.-][0-9]+)*[\.:\-]?\s*", "", t, flags=re.I)
    return t

def _infer_caption_label(texto):
    if texto and texto.strip().lower().startswith("figura"):
        return "Figura"
    return "Tabla"

def agregar_caption(doc, label, texto):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"{label} ")
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0, 0, 0)
    _add_fldSimple(p, f"SEQ {label} \\* ARABIC")
    if texto:
        p.add_run(". ")
        t_run = p.add_run(texto)
        t_run.font.name = "Arial"
        t_run.font.size = Pt(11)
        t_run.font.color.rgb = RGBColor(0, 0, 0)


def agregar_abreviaturas(doc, data, add_page_break=True):
    if not data:
        return
    agregar_titulo_indice(doc, data.get("titulo", "INDICE DE ABREVIATURAS"))
    ejemplo = data.get("ejemplo")
    if ejemplo:
        p = doc.add_paragraph(ejemplo)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    nota = data.get("nota")
    if nota:
        agregar_nota_estilizada(doc, nota)
    if add_page_break:
        doc.add_page_break()


def agregar_indices(doc, indices):
    if not indices:
        return
    agregar_titulo_indice(doc, indices.get("contenido", "INDICE DE CONTENIDO"))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run("Pag.")
    p2 = doc.add_paragraph()
    _add_fldSimple(p2, 'TOC \\o "1-3" \\h \\z \\u')
    doc.add_page_break()

    if indices.get("tablas"):
        agregar_titulo_indice(doc, indices.get("tablas"))
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.add_run("Pag.")
        p2 = doc.add_paragraph()
        _add_fldSimple(p2, 'TOC \\h \\z \\c "Tabla"')
        doc.add_page_break()

    if indices.get("figuras"):
        agregar_titulo_indice(doc, indices.get("figuras"))
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.add_run("Pag.")
        p2 = doc.add_paragraph()
        _add_fldSimple(p2, 'TOC \\h \\z \\c "Figura"')
        doc.add_page_break()


def agregar_preliminares_romanos(doc, data):
    p = data.get("preliminares", {})

    info = data.get("informacion_basica") or p.get("informacion_basica")
    hoja_jurado = p.get("hoja_jurado")
    blocks = []
    if info:
        blocks.append(("info", info))
    if hoja_jurado:
        blocks.append(("hoja_jurado", hoja_jurado))
    for sec in ["dedicatoria", "resumen", "agradecimientos"]:
        if sec in p:
            blocks.append((sec, p[sec]))

    for idx, (kind, payload) in enumerate(blocks):
        is_last = idx == len(blocks) - 1
        if kind == "info":
            agregar_informacion_basica(doc, payload, add_page_break=not is_last)
        elif kind == "hoja_jurado":
            agregar_hoja_jurado(doc, payload, add_page_break=not is_last)
        else:
            agregar_bloque(doc, payload.get("titulo", ""), negrita=True, tamano=14, despues=12)
            doc.add_paragraph(payload.get("texto", ""))
            if not is_last:
                doc.add_page_break()


def agregar_indices_y_introduccion(doc, data):
    p = data.get("preliminares", {})
    if "indices" in p:
        agregar_indices(doc, p.get("indices"))

    if "abreviaturas" in p:
        agregar_abreviaturas(doc, p.get("abreviaturas"))

    if "introduccion" in p:
        agregar_titulo_formal(doc, p["introduccion"].get("titulo", ""))
        agregar_nota_estilizada(doc, p["introduccion"].get("texto", ""))
        if data.get("cuerpo"):
            doc.add_page_break()


# ==========================================
# CUERPO
# ==========================================

def _agregar_imagenes(doc, imagenes):
    for img in imagenes or []:
        caption_raw = img.get("titulo") or "Figura"
        caption_text = _strip_caption_prefix("Figura", caption_raw)
        agregar_caption(doc, "Figura", caption_text)

        ruta = img.get("ruta")
        if not ruta or ruta == "placeholder":
            ruta = FALLBACK_FIGURE_PATH if os.path.exists(FALLBACK_FIGURE_PATH) else None
        if ruta:
            path = encontrar_recurso(ruta)
            if path:
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.add_run().add_picture(path, width=Cm(12.0))
            else:
                p = doc.add_paragraph("[IMAGEN NO ENCONTRADA]")
                p.runs[0].font.color.rgb = RGBColor(255, 0, 0)
        else:
            doc.add_paragraph("[IMAGEN]")

        if img.get("fuente"):
            agregar_nota_estilizada(doc, img.get("fuente"))


def agregar_cuerpo_dinamico(doc, data):
    for cap in data.get("cuerpo", []):
        agregar_titulo_formal(doc, cap.get("titulo", ""), espaciado_antes=10)
        if "nota_capitulo" in cap:
            agregar_nota_estilizada(doc, cap["nota_capitulo"])

        if "ejemplos_apa" in cap:
            imprimir_ejemplos_apa(doc, cap.get("ejemplos_apa"))

        for item in cap.get("contenido", []):
            if "texto" in item:
                sub = doc.add_heading(item.get("texto", ""), level=2)
                sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
                if sub.runs:
                    sub.runs[0].font.name = "Arial"
                    sub.runs[0].font.size = Pt(12)
                    sub.runs[0].font.color.rgb = RGBColor(0, 0, 0)

            if "nota" in item:
                agregar_nota_estilizada(doc, item.get("nota", ""))

            if "instruccion_detallada" in item:
                agregar_nota_estilizada(doc, item.get("instruccion_detallada", ""))

            if item.get("mostrar_matriz") and "matriz_consistencia" in data:
                crear_tabla_matriz_consistencia(doc, data["matriz_consistencia"], False)

            if "tablas_especiales" in item:
                for t_esp in item.get("tablas_especiales", []):
                    titulo = t_esp.get("titulo", "")
                    label = _infer_caption_label(titulo)
                    caption_text = _strip_caption_prefix(label, titulo)
                    agregar_caption(doc, label, caption_text)
                    crear_tabla_estilizada(doc, t_esp)

            if "tabla" in item:
                titulo_tabla = item.get("tabla_titulo", "")
                caption_text = _strip_caption_prefix("Tabla", titulo_tabla)
                agregar_caption(doc, "Tabla", caption_text)
                crear_tabla_estilizada(doc, item.get("tabla"))
                if item.get("tabla_nota"):
                    agregar_nota_estilizada(doc, item.get("tabla_nota"))

            if "imagenes" in item:
                _agregar_imagenes(doc, item.get("imagenes"))

            if "parrafos" in item:
                for par in item.get("parrafos", []):
                    doc.add_paragraph(par)

            doc.add_paragraph("")

        doc.add_page_break()


# ==========================================
# FINALES
# ==========================================

def agregar_finales_dinamico(doc, data):
    fin = data.get("finales", {})

    if "referencias" in fin:
        ref = fin.get("referencias", {})
        agregar_titulo_formal(doc, ref.get("titulo", "REFERENCIAS BIBLIOGRAFICAS"))
        if ref.get("nota"):
            agregar_nota_estilizada(doc, ref.get("nota"))
        if ref.get("ejemplos_apa"):
            imprimir_ejemplos_apa(doc, ref.get("ejemplos_apa"))
        elif ref.get("ejemplos"):
            for ejemplo in ref.get("ejemplos", []):
                doc.add_paragraph(ejemplo)
        doc.add_page_break()

    if "anexos" in fin:
        anexos = fin.get("anexos", {})
        agregar_titulo_formal(doc, anexos.get("titulo_seccion", "ANEXOS"))
        if anexos.get("nota"):
            agregar_nota_estilizada(doc, anexos.get("nota"))
        if "matriz_consistencia" in data:
            crear_tabla_matriz_consistencia(doc, data["matriz_consistencia"], False)
            doc.add_page_break()

        for anexo in anexos.get("lista", []):
            p = doc.add_paragraph(anexo.get("titulo", ""))
            if p.runs:
                p.runs[0].bold = True

            if anexo.get("nota"):
                agregar_nota_estilizada(doc, anexo.get("nota"))

            if anexo.get("tabla"):
                titulo_tabla = anexo.get("tabla_titulo", "")
                caption_text = _strip_caption_prefix("Tabla", titulo_tabla)
                agregar_caption(doc, "Tabla", caption_text)
                crear_tabla_estilizada(doc, anexo.get("tabla"))
                if anexo.get("tabla_nota"):
                    agregar_nota_estilizada(doc, anexo.get("tabla_nota"))

            if anexo.get("parrafos"):
                for par in anexo.get("parrafos", []):
                    doc.add_paragraph(par)

            doc.add_page_break()


# ==========================================
# EJECUCION
# ==========================================

def configurar_numeracion_maestria(doc):
    """Numeracion roman para respeto/preliminares y arabiga desde indice."""
    doc.sections[0].different_first_page_header_footer = True
    for i in range(min(len(doc.sections), 2)):
        doc.sections[i].footer.is_linked_to_previous = False

    # Seccion 2 (hoja de respeto): romanos iniciando en II
    if len(doc.sections) > 1:
        s = doc.sections[1]
        s.footer.is_linked_to_previous = False
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), "upperRoman")
        pg.set(qn("w:start"), "2")
        s._sectPr.append(pg)
        _insertar_n(s.footer)

    # Seccion 3 (preliminares): continuar romanos
    if len(doc.sections) > 2:
        s = doc.sections[2]
        s.footer.is_linked_to_previous = False
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), "upperRoman")
        s._sectPr.append(pg)
        _insertar_n(s.footer)

    # Seccion 4 (indices/cuerpo): arabigos desde 1
    if len(doc.sections) > 3:
        s = doc.sections[3]
        s.footer.is_linked_to_previous = False
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), "decimal")
        pg.set(qn("w:start"), "1")
        s._sectPr.append(pg)
        _insertar_n(s.footer)


def generar_documento_core(ruta_json, ruta_salida):
    data = cargar_contenido(ruta_json)
    doc = Document()
    configurar_estilos_base(doc)

    # 1. CARATULA
    configurar_seccion_unac(doc.sections[0])
    crear_caratula_dinamica(doc, data)

    # 2. HOJA DE RESPETO (BLANCA O CON NOTAS)
    doc.add_section(WD_SECTION.NEW_PAGE)
    configurar_seccion_unac(doc.sections[-1])
    respeto = data.get("pagina_respeto", {})
    notas = respeto.get("notas", []) if isinstance(respeto, dict) else []
    if notas:
        for nota in notas:
            doc.add_paragraph(nota.get("texto", ""))
    else:
        doc.add_paragraph("")

    # 3. PRELIMINARES (ROMANOS)
    doc.add_section(WD_SECTION.NEW_PAGE)
    configurar_seccion_unac(doc.sections[-1])
    agregar_preliminares_romanos(doc, data)

    # 4. INDICES + CUERPO + FINALES (ARABIGOS)
    doc.add_section(WD_SECTION.NEW_PAGE)
    configurar_seccion_unac(doc.sections[-1])
    agregar_indices_y_introduccion(doc, data)
    agregar_cuerpo_dinamico(doc, data)

    # 5. FINALES
    agregar_finales_dinamico(doc, data)

    # 6. CONFIGURACION FINAL
    configurar_numeracion_maestria(doc)
    doc.settings.element.append(OxmlElement("w:updateFields"))
    doc.save(ruta_salida)
    return ruta_salida


if __name__ == "__main__":
    if len(sys.argv) > 2:
        generar_documento_core(sys.argv[1], sys.argv[2])
