from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


MARKERS = ("\u00c3", "\u00c2", "\ufffd")


def _contains_marker(value: str) -> bool:
    return any(marker in value for marker in MARKERS)


def _fix_string(value: str) -> str:
    if not _contains_marker(value):
        return value

    best = value
    best_score = sum(value.count(marker) for marker in MARKERS)

    for enc in ("cp1252", "latin-1"):
        try:
            candidate = value.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        candidate_score = sum(candidate.count(marker) for marker in MARKERS)
        if candidate_score < best_score:
            best = candidate
            best_score = candidate_score

    return best


def _walk(node: Any) -> Any:
    if isinstance(node, str):
        return _fix_string(node)
    if isinstance(node, list):
        return [_walk(item) for item in node]
    if isinstance(node, dict):
        return {key: _walk(value) for key, value in node.items()}
    return node


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python scripts/fix_mojibake_json.py <file1.json> [file2.json ...]")
        return 1

    for raw in argv[1:]:
        path = Path(raw)
        if not path.exists():
            print(f"Skip (missing): {path}")
            continue

        data = json.loads(path.read_text(encoding="utf-8-sig"))
        fixed = _walk(data)
        path.write_text(json.dumps(fixed, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
