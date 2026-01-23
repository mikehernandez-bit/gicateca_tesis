#!/usr/bin/env python
"""
Check for mojibake patterns in text files.
Exit with code 1 if suspicious patterns are found.
"""
from __future__ import annotations

import sys
from pathlib import Path


PATTERNS = (
    "\u00c3",          # Ã
    "\u00c2",          # Â
    "\u00e2\u0080\u00a2",  # â€¢
    "\u00e2\u0080\u0093",  # â€“
    "\u00e2\u0080\u0094",  # â€”
    "\ufffd",          # Replacement char
    "Educaci?n",
    "Psicolog?a",
    "a?o",
    "sangr?a",
)

TEXT_EXTS = {".py", ".js", ".html", ".json", ".md", ".txt"}
EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
}
SCAN_DIRS = (
    "app/data",
    "app/templates",
    "app/static",
)


def _has_control_chars(line: str) -> bool:
    return any(0x80 <= ord(ch) <= 0x9F for ch in line)


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for scan_dir in SCAN_DIRS:
        base = root / scan_dir
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_dir():
                continue
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in TEXT_EXTS:
                continue
            if path.name.endswith(".bak"):
                continue
            files.append(path)
    return files


def _safe_preview(line: str) -> str:
    return line.encode("unicode_escape").decode("ascii")


def main() -> int:
    root = Path(".").resolve()
    issues = []

    for path in _iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            issues.append((path, 0, f"DECODE_ERROR: {exc}"))
            continue

        for idx, line in enumerate(text.splitlines(), start=1):
            if any(token in line for token in PATTERNS) or _has_control_chars(line):
                issues.append((path, idx, _safe_preview(line.strip())))

    if issues:
        print("Mojibake detectado:")
        for path, line_no, detail in issues:
            print(f"- {path}:{line_no}: {detail}")
        return 1

    print("OK: No se encontraron patrones de mojibake.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
