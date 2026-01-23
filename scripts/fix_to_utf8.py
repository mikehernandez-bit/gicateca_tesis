#!/usr/bin/env python
"""
Fix text files to UTF-8 when decoding or mojibake issues are detected.
Creates .bak backups before rewriting.
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


def _has_control_chars(text: str) -> bool:
    return any(0x80 <= ord(ch) <= 0x9F for ch in text)


def _mojibake_score(text: str) -> int:
    score = sum(text.count(token) for token in PATTERNS)
    score += sum(1 for ch in text if 0x80 <= ord(ch) <= 0x9F)
    return score


def _fix_mojibake(text: str) -> str | None:
    for enc in ("cp1252", "latin-1"):
        try:
            return text.encode(enc).decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    return None


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


def _decode_bytes(data: bytes) -> tuple[str, str] | None:
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    for enc in ("cp1252", "latin-1"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return None


def main() -> int:
    root = Path(".").resolve()
    converted: list[str] = []

    for path in _iter_files(root):
        data = path.read_bytes()
        decoded = _decode_bytes(data)
        if not decoded:
            continue
        text, encoding = decoded

        bom = "\ufeff" if text.startswith("\ufeff") else ""
        body = text.lstrip("\ufeff")

        needs_rewrite = encoding != "utf-8"
        before_score = _mojibake_score(body)

        fixed_body = body
        if before_score > 0 or _has_control_chars(body):
            candidate = _fix_mojibake(body)
            if candidate is not None:
                after_score = _mojibake_score(candidate)
                if after_score < before_score:
                    fixed_body = candidate
                    needs_rewrite = True

        if not needs_rewrite:
            continue

        backup = path.with_suffix(path.suffix + ".bak")
        if not backup.exists():
            backup.write_bytes(data)

        path.write_text(bom + fixed_body, encoding="utf-8")
        converted.append(f"{path} (from {encoding})")

    if converted:
        print("Archivos convertidos a UTF-8:")
        for item in converted:
            print(f"- {item}")
    else:
        print("No se requirio conversion.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
