"""Provides the sorted list of heroes (display name -> internal name) for the GUI."""

import json
from functools import lru_cache
from pathlib import Path

_HEROES_PATH = Path(__file__).resolve().parents[2] / "data" / "heroes.json"

_HERO_PREFIX = "npc_dota_hero_"


@lru_cache(maxsize=1)
def hero_name_map() -> dict[str, str]:
    """Return {display_name: internal_name}, sorted by display name."""
    raw = json.loads(_HEROES_PATH.read_text(encoding="utf-8"))
    pairs = []
    for hero in raw.values():
        display = hero.get("localized_name")
        internal = hero.get("name", "").replace(_HERO_PREFIX, "")
        if display and internal:
            pairs.append((display, internal))
    pairs.sort(key=lambda p: p[0])
    return dict(pairs)