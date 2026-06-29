"""Loads Dota 2 item data and provides compact lookups for the brain.

The data comes from the dotaconstants project (which extracts it from the
game files). We load it once and expose only the fields the coach needs,
so the model reasons with real item names, costs and effects instead of
inventing them.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_ITEMS_PATH = Path(__file__).resolve().parents[2] / "data" / "items.json"


@lru_cache(maxsize=1)
def _load_items() -> dict[str, Any]:
    """Load the raw items.json once and cache it."""
    data: dict[str, Any] = json.loads(_ITEMS_PATH.read_text(encoding="utf-8"))
    return data


def _ability_text(item: dict[str, Any]) -> str:
    """Join an item's ability descriptions into a single short string."""
    abilities = item.get("abilities") or []
    parts = [a.get("description", "").strip() for a in abilities]
    text = " ".join(p for p in parts if p)
    # Keep it short to save tokens; the model only needs the gist.
    return text[:200]


def lookup(name: str) -> dict[str, Any] | None:
    """Return compact data for one item by its clean name, or None.

    The name matches the serializer's output (e.g. "tango", "blink"),
    which is the same key dotaconstants uses.
    """
    items = _load_items()
    item = items.get(name)
    if item is None:
        return None
    return {
        "name": item.get("dname", name),
        "cost": item.get("cost"),
        "effect": _ability_text(item),
    }


def lookup_many(names: list[str]) -> list[dict[str, Any]]:
    """Look up several items, skipping any that are not found."""
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        data = lookup(name)
        if data is not None:
            result.append(data)
    return result