"""Loads Dota 2 hero ability data and provides compact lookups for the brain.

Combines two dotaconstants files: hero_abilities.json (which abilities,
talents and facets each hero has) and abilities.json (what each ability
does). Exposes only what the coach needs, with real in-game names.
"""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_HERO_ABILITIES_PATH = _DATA_DIR / "hero_abilities.json"
_ABILITIES_PATH = _DATA_DIR / "abilities.json"

_HERO_PREFIX = "npc_dota_hero_"


@lru_cache(maxsize=1)
def _load_hero_abilities() -> dict[str, Any]:
    """Load the hero -> abilities/talents/facets mapping, once."""
    data: dict[str, Any] = json.loads(
        _HERO_ABILITIES_PATH.read_text(encoding="utf-8")
    )
    return data


@lru_cache(maxsize=1)
def _load_abilities() -> dict[str, Any]:
    """Load the per-ability detail file, once."""
    data: dict[str, Any] = json.loads(
        _ABILITIES_PATH.read_text(encoding="utf-8")
    )
    return data


def _ability_detail(ability_name: str) -> dict[str, Any] | None:
    """Compact detail for one ability: real name, description, cd, mana."""
    abilities = _load_abilities()
    ability = abilities.get(ability_name)
    if ability is None:
        return None
    desc = (ability.get("desc") or "").strip()
    return {
        "name": ability.get("dname", ability_name),
        "effect": desc[:200],
        "cooldown": ability.get("cd"),
        "mana": ability.get("mc"),
    }


def _clean_talent_name(name: str) -> str:
    """Remove unfilled dotaconstants placeholders like {s:bonus_x} from a name."""
    cleaned = re.sub(r"\{[^}]*\}", "", name)
    # Collapse leftover double spaces and stray signs from removed numbers.
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def lookup_hero(hero_name: str) -> dict[str, Any] | None:
    """Return a hero's real abilities, talents and facets, or None.

    The hero name matches the serializer's output (e.g. "furion"); the
    "npc_dota_hero_" prefix is added to match the data file's key.
    """
    if not hero_name:
        return None
    hero_abilities = _load_hero_abilities()
    key = f"{_HERO_PREFIX}{hero_name}"
    hero = hero_abilities.get(key)
    if hero is None:
        return None

    # Real, described abilities (skip talents, which start with special_bonus).
    # Each keeps its clean internal key so callers can match it against the
    # abilities the player actually has in the live state.
    hero_prefix = f"{hero_name}_"
    abilities: list[dict[str, Any]] = []
    for ability_name in hero.get("abilities", []):
        if ability_name.startswith("special_bonus"):
            continue
        detail = _ability_detail(ability_name)
        if detail is not None:
            detail["key"] = ability_name.replace(hero_prefix, "")
            abilities.append(detail)

    # Facets: name and short description.
    facets: list[dict[str, Any]] = []
    for facet in hero.get("facets", []):
        facets.append(
            {
                "name": facet.get("title", facet.get("name", "")),
                "effect": (facet.get("description") or "")[:150],
            }
        )

    # Talents: level and readable name, with unfilled placeholders removed.
    talents: list[dict[str, Any]] = []
    for talent in hero.get("talents", []):
        detail = _ability_detail(talent.get("name", ""))
        raw_name = detail["name"] if detail else talent.get("name", "")
        talents.append(
            {
                "level": talent.get("level"),
                "name": _clean_talent_name(raw_name),
            }
        )

    return {"abilities": abilities, "facets": facets, "talents": talents}