"""Deterministic academic diagrams for structured GICA figure blocks."""

from __future__ import annotations

import tempfile
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _wrapped(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: Any) -> None:
    x1, y1, x2, y2 = box
    width_chars = max(10, int((x2 - x1) / max(8, getattr(font, "size", 18) * 0.55)))
    lines = textwrap.wrap(str(text), width=width_chars) or [str(text)]
    line_height = max(18, getattr(font, "size", 18) + 4)
    y = y1 + max(8, ((y2 - y1) - len(lines) * line_height) // 2)
    for line in lines:
        bounds = draw.textbbox((0, 0), line, font=font)
        draw.text((x1 + ((x2 - x1) - (bounds[2] - bounds[0])) / 2, y), line, fill="#16324F", font=font)
        y += line_height


def _flow(draw: ImageDraw.ImageDraw, labels: list[str], *, width: int, height: int) -> None:
    count = max(1, len(labels))
    margin, gap = 80, 28
    box_width = max(150, int((width - 2 * margin - gap * (count - 1)) / count))
    y1, y2 = 290, 520
    font = _font(23, bold=True)
    for index, label in enumerate(labels):
        x1 = margin + index * (box_width + gap)
        x2 = x1 + box_width
        draw.rounded_rectangle((x1, y1, x2, y2), radius=20, fill="#EAF2F8", outline="#2874A6", width=4)
        _wrapped(draw, (x1 + 10, y1 + 10, x2 - 10, y2 - 10), label, font)
        if index < count - 1:
            start, end = (x2 + 4, (y1 + y2) // 2), (x2 + gap - 5, (y1 + y2) // 2)
            draw.line((start, end), fill="#2874A6", width=5)
            draw.polygon(((end[0], end[1]), (end[0] - 14, end[1] - 9), (end[0] - 14, end[1] + 9)), fill="#2874A6")


def _ishikawa(draw: ImageDraw.ImageDraw, labels: list[str], *, width: int, height: int) -> None:
    center_y = height // 2
    draw.line((180, center_y, width - 230, center_y), fill="#2874A6", width=7)
    draw.polygon(((width - 230, center_y), (width - 285, center_y - 32), (width - 285, center_y + 32)), fill="#2874A6")
    font = _font(24, bold=True)
    for index, label in enumerate(labels[:6]):
        upper = index % 2 == 0
        x = 300 + (index // 2) * 330
        end_y = center_y - 190 if upper else center_y + 190
        draw.line((x, center_y, x - 120, end_y), fill="#5D6D7E", width=5)
        box = (x - 230, end_y - 55 if upper else end_y, x + 45, end_y if upper else end_y + 55)
        draw.rounded_rectangle(box, radius=15, fill="#F8F9F9", outline="#5D6D7E", width=3)
        _wrapped(draw, box, label, font)
    effect_box = (width - 310, center_y - 80, width - 30, center_y + 80)
    draw.rounded_rectangle(effect_box, radius=18, fill="#D6EAF8", outline="#1B4F72", width=4)
    _wrapped(draw, effect_box, "Problema analizado", font)


def generate_diagram_png(diagram_type: str, diagram_data: dict[str, Any] | None, title: str) -> str:
    data = diagram_data if isinstance(diagram_data, dict) else {}
    labels = [str(item).strip() for item in data.get("labels", []) if str(item).strip()]
    if not labels:
        labels = [title or "Esquema técnico"]
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(34, bold=True)
    draw.text((80, 55), title or "Esquema técnico", fill="#12344D", font=title_font)
    draw.line((80, 110, width - 80, 110), fill="#2874A6", width=4)
    if str(diagram_type).lower() == "ishikawa":
        _ishikawa(draw, labels, width=width, height=height)
    else:
        _flow(draw, labels, width=width, height=height)
    disclaimer = str(data.get("disclaimer") or "").strip()
    if disclaimer:
        draw.text((80, height - 65), disclaimer, fill="#566573", font=_font(20))
    handle = tempfile.NamedTemporaryFile(prefix="gica_diagram_", suffix=".png", delete=False)
    handle.close()
    image.save(handle.name, "PNG", optimize=True)
    return handle.name
