"""Shared loaders for data access across modules."""
import json
from pathlib import Path
from typing import Dict, Any


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in file: {file_path}")


def get_data_dir() -> Path:
    """Get the path to the data directory."""
    return Path(__file__).resolve().parent.parent / "data" / "unac"
