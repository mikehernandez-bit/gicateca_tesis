#!/usr/bin/env python
"""
Check for mojibake patterns in text files.
Exit with code 1 if suspicious patterns are found.
"""
from __future__ import annotations

import sys
from pathlib import Path


PATTERNS = (
    "Ã",
    "Â",
    "â€",
    "â€¢",
    "â€“",
    "â€”",
    "Ã¡",
    "Ã©",
    "Ã­",
    "Ã³",
    "Ãº",
    "Ã±",
    "Ã",
    "Ãš",
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


def _has_control_chars(line: str) -> bool:
    return any(0x80 <= ord(ch) <= 0x9F for ch in line)


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.parent.name == "scripts" and path.name in {"check_mojibake.py", "fix_to_utf8.py"}:
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        if path.name.endswith(".bak"):
            continue
        if "docs/CODE_DUMP" in path.as_posix():
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
