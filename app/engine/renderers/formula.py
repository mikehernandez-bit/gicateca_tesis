"""Render structured formula blocks as editable Word OMML equations."""

from __future__ import annotations

import re

from docx.document import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from app.engine.registry import register
from app.engine.types import Block


class FormulaConversionError(ValueError):
    """Raised when a formula cannot be represented safely as OMML."""


_GREEK = {
    "lambda": "λ",
    "mu": "μ",
    "sigma": "σ",
    "alpha": "α",
    "beta": "β",
    "Delta": "Δ",
    "theta": "θ",
}
_OPERATORS = {
    "cdot": "·",
    "times": "×",
    "sum": "∑",
    "ge": "≥",
    "geq": "≥",
    "le": "≤",
    "leq": "≤",
    "neq": "≠",
    "approx": "≈",
}


def _math_run(text: str):
    run = OxmlElement("m:r")
    props = OxmlElement("m:rPr")
    normal = OxmlElement("m:nor")
    props.append(normal)
    run.append(props)
    value = OxmlElement("m:t")
    value.text = text
    run.append(value)
    return run


def _group_content(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "{":
        raise FormulaConversionError("se esperaba un grupo entre llaves")
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : index], index + 1
    raise FormulaConversionError("grupo matematico sin cierre")


def _append_fraction(parent, numerator: str, denominator: str) -> None:
    fraction = OxmlElement("m:f")
    num = OxmlElement("m:num")
    _append_expression(num, numerator)
    den = OxmlElement("m:den")
    _append_expression(den, denominator)
    fraction.extend([num, den])
    parent.append(fraction)


def _append_radical(parent, radicand: str) -> None:
    radical = OxmlElement("m:rad")
    props = OxmlElement("m:radPr")
    hide_degree = OxmlElement("m:degHide")
    hide_degree.set(qn("m:val"), "1")
    props.append(hide_degree)
    radical.append(props)
    degree = OxmlElement("m:deg")
    radical.append(degree)
    element = OxmlElement("m:e")
    _append_expression(element, radicand)
    radical.append(element)
    parent.append(radical)


def _append_script(parent, base: str, sub: str | None, sup: str | None) -> None:
    tag = "m:sSubSup" if sub is not None and sup is not None else "m:sSub" if sub is not None else "m:sSup"
    script = OxmlElement(tag)
    element = OxmlElement("m:e")
    _append_expression(element, base)
    script.append(element)
    if sub is not None:
        sub_node = OxmlElement("m:sub")
        _append_expression(sub_node, sub)
        script.append(sub_node)
    if sup is not None:
        sup_node = OxmlElement("m:sup")
        _append_expression(sup_node, sup)
        script.append(sup_node)
    parent.append(script)


def _read_script(text: str, index: int) -> tuple[str, int]:
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        raise FormulaConversionError("subindice o exponente vacio")
    if text[index] == "{":
        return _group_content(text, index)
    if text[index] == "\\":
        match = re.match(r"\\([A-Za-z]+)", text[index:])
        if not match:
            raise FormulaConversionError("comando matematico invalido")
        return "\\" + match.group(1), index + len(match.group(0))
    return text[index], index + 1


def _append_expression(parent, source: str) -> None:
    text = source.strip().replace("\\left", "").replace("\\right", "")
    index = 0
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            parent.append(_math_run("".join(buffer)))
            buffer.clear()

    while index < len(text):
        if text.startswith("\\frac", index):
            flush()
            index += len("\\frac")
            numerator, index = _group_content(text, index)
            denominator, index = _group_content(text, index)
            _append_fraction(parent, numerator, denominator)
            continue
        if text.startswith("\\sqrt", index):
            flush()
            index += len("\\sqrt")
            radicand, index = _group_content(text, index)
            _append_radical(parent, radicand)
            continue
        if text[index] == "\\":
            match = re.match(r"\\([A-Za-z]+)", text[index:])
            if not match:
                raise FormulaConversionError(f"comando no reconocido cerca de {text[index:index+12]!r}")
            command = match.group(1)
            if command not in _GREEK and command not in _OPERATORS:
                raise FormulaConversionError(f"comando LaTeX no soportado: \\{command}")
            buffer.append(_GREEK.get(command, _OPERATORS.get(command, command)))
            index += len(match.group(0))
            continue

        # Attach a following sub/superscript to the last buffered atom.
        if text[index] in "_^":
            if not buffer:
                raise FormulaConversionError("subindice o exponente sin base")
            flush_text = "".join(buffer)
            buffer.clear()
            base_match = re.search(r"([A-Za-zΑ-ω∑]+|\d+)$", flush_text)
            if not base_match:
                raise FormulaConversionError("no se pudo identificar la base del indice")
            prefix = flush_text[: base_match.start()]
            if prefix:
                parent.append(_math_run(prefix))
            base = base_match.group(1)
            sub = sup = None
            marker = text[index]
            value, index = _read_script(text, index + 1)
            if marker == "_":
                sub = value
            else:
                sup = value
            while index < len(text) and text[index] in "_^":
                marker = text[index]
                value, index = _read_script(text, index + 1)
                if marker == "_":
                    sub = value
                else:
                    sup = value
            _append_script(parent, base, sub, sup)
            continue
        buffer.append(text[index])
        index += 1
    flush()


def build_omml(latex: str, fallback: str = ""):
    expression = str(latex or fallback or "").strip()
    expression = re.sub(r"^\$|\$$", "", expression).strip()
    if not expression:
        raise FormulaConversionError("la formula requiere una expresion no vacia")
    math = OxmlElement("m:oMath")
    _append_expression(math, expression)
    return math


@register("formula")
def render_formula(doc: Document, block: Block) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
    }.get(str(block.get("alignment") or "center").lower(), WD_ALIGN_PARAGRAPH.CENTER)
    paragraph._p.append(build_omml(str(block.get("latex") or ""), str(block.get("text") or "")))
    number = str(block.get("number") or "").strip()
    if number:
        paragraph.add_run(f"  {number}")
