"""Mutable render state shared across sequential DOCX renderers."""

from __future__ import annotations

import re

_CHAPTER_HEADING_RE = re.compile(r"^\s*([IVXLC]+|\d+)\s*[.)-]\s+")
_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}

_chapter_number = 0
_chapter_figure_number = 0
_chapter_table_number = 0


def reset_render_state() -> None:
    global _chapter_number, _chapter_figure_number, _chapter_table_number
    _chapter_number = 0
    _chapter_figure_number = 0
    _chapter_table_number = 0


def _roman_to_int(value: str) -> int:
    total = 0
    previous = 0
    for char in reversed(str(value or "").upper()):
        current = _ROMAN_VALUES.get(char, 0)
        if current < previous:
            total -= current
        else:
            total += current
            previous = current
    return total


def _heading_number(text: str) -> int | None:
    match = _CHAPTER_HEADING_RE.match(str(text or ""))
    if not match:
        return None
    token = match.group(1).upper()
    if token.isdigit():
        return int(token)
    parsed = _roman_to_int(token)
    return parsed if parsed > 0 else None


def register_heading(text: str, *, level: int) -> None:
    global _chapter_number, _chapter_figure_number, _chapter_table_number
    if level != 1:
        return
    parsed_number = _heading_number(str(text or ""))
    if parsed_number is None:
        return
    _chapter_number = parsed_number
    _chapter_figure_number = 0
    _chapter_table_number = 0


def next_figure_number() -> tuple[int | None, int, bool]:
    global _chapter_figure_number
    _chapter_figure_number += 1
    return (
        _chapter_number if _chapter_number > 0 else None,
        _chapter_figure_number,
        _chapter_figure_number == 1,
    )


def next_table_number() -> tuple[int | None, int, bool]:
    global _chapter_table_number
    _chapter_table_number += 1
    return (
        _chapter_number if _chapter_number > 0 else None,
        _chapter_table_number,
        _chapter_table_number == 1,
    )
