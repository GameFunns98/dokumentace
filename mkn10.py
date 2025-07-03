import json
from pathlib import Path

_data: dict[str, dict] = {}

def load_mkn10_data(path: str) -> dict:
    """Load MKN-10 codes from JSON file."""
    global _data
    with open(path, "r", encoding="utf-8") as fh:
        _data = json.load(fh)
    return _data

def get_description(code: str) -> str | None:
    """Return description for given code or ``None`` if not found."""
    item = _data.get(code.upper())
    if item:
        return item.get("d")
    return None

def get_all_codes() -> list[str]:
    """Return list of all MKN-10 codes."""
    return list(_data.keys())
