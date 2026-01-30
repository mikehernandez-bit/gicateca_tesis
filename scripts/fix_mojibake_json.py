#!/usr/bin/env python
"""
Fix mojibake in JSON files by attempting latin1->utf-8 recovery
on strings that contain typical mojibake markers (Ã, Â, �).

Usage:
  python scripts/fix_mojibake_json.py path/to/file.json [...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


MOJIBAKE_MARKERS = ("Ã", "Â", "�")


def _needs_fix(value: str) -> bool:
    return any(marker in value for marker in MOJIBAKE_MARKERS)


def _fix_string(value: str) -> str:
    if not _needs_fix(value):
        return value
    fixed = None

    # 1) Try latin1 and cp1252 directly
    for codec in ("latin1", "cp1252"):
        try:
            fixed = value.encode(codec).decode("utf-8")
            break
        except UnicodeError:
            continue

    # 2) Fallback: build bytes manually (handles smart quotes + control bytes)
    if fixed is None:
        mapped = bytearray()
        for ch in value:
            code = ord(ch)
            if code == 0x201C:  # “
                mapped.append(0x93)
            elif code == 0x201D:  # ”
                mapped.append(0x94)
            elif code == 0x2018:  # ‘
                mapped.append(0x91)
            elif code == 0x2019:  # ’
                mapped.append(0x92)
            elif 0 <= code <= 0xFF:
                mapped.append(code)
            else:
                mapped = None
                break
        if mapped is not None:
            try:
                fixed = bytes(mapped).decode("utf-8")
            except UnicodeError:
                fixed = None

    if fixed is None:
        return value
    # Only accept if it reduces mojibake markers.
    if sum(value.count(m) for m in MOJIBAKE_MARKERS) <= sum(fixed.count(m) for m in MOJIBAKE_MARKERS):
        return fixed
    return fixed


def _fix_value(value: Any) -> Any:
    if isinstance(value, str):
        return _fix_string(value)
    if isinstance(value, list):
        return [_fix_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _fix_value(val) for key, val in value.items()}
    return value


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python scripts/fix_mojibake_json.py <file1.json> [file2.json ...]")
        return 1

    for raw_path in argv[1:]:
        path = Path(raw_path)
        if not path.exists():
            print(f"Skip (not found): {path}")
            continue

        data = json.loads(path.read_text(encoding="utf-8-sig"))
        fixed = _fix_value(data)

        # Force placeholder on caratula if present.
        if isinstance(fixed, dict) and "caratula" in fixed and isinstance(fixed["caratula"], dict):
            fixed["caratula"]["titulo_placeholder"] = "[ESCRIBA AQUÍ EL TÍTULO DE LA TESIS]"

        path.write_text(json.dumps(fixed, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
