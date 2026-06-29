"""Trims the large Valve GSI payload into a compact dictionary.

GSI only exposes the local player's data during a live game, so this
serializer focuses on the player's own hero, items, abilities and economy.
"""

from typing import Any

# Prefixes Valve uses internally that we strip to save tokens and read better.
_HERO_PREFIX = "npc_dota_hero_"
_ITEM_PREFIX = "item_"
_STATE_PREFIX = "DOTA_GAMERULES_STATE_"

# Item slots we care about: main inventory, backpack, neutral and teleport.
_RELEVANT_ITEM_SLOTS = (
    "slot0", "slot1", "slot2", "slot3", "slot4", "slot5",
    "slot6", "slot7", "slot8",
    "neutral0", "neutral1",
    "teleport0",
)

# The map is split diagonally by the river around the origin (0, 0).
# Radiant base sits deep in the negative corner, Dire in the positive corner.
# We classify position by the diagonal coordinate sum, flipped per team.
_BASE_THRESHOLD = 10000
_HALF_THRESHOLD = 2000


def _strip(name: str, prefix: str) -> str:
    """Remove a known Valve prefix from a name, if present."""
    return name[len(prefix):] if name.startswith(prefix) else name


def _map_zone(
    xpos: float | None,
    ypos: float | None,
    team: str | None,
) -> str | None:
    """Translate raw coordinates into a coarse, honest map zone.

    Returns one of: own_base, own_half, mid, enemy_half. Returns None when
    position or team is unknown. Does not attempt to identify lanes, since
    that needs verified per-patch zone data we do not have.
    """
    if xpos is None or ypos is None or team not in ("radiant", "dire"):
        return None

    # Diagonal coordinate: negative toward Radiant corner, positive toward Dire.
    diagonal = xpos + ypos
    # Normalize so that "negative" always means "toward own base".
    if team == "dire":
        diagonal = -diagonal

    if diagonal <= -_BASE_THRESHOLD:
        return "own_base"
    if diagonal < -_HALF_THRESHOLD:
        return "own_half"
    if diagonal <= _HALF_THRESHOLD:
        return "mid"
    return "enemy_half"


def _serialize_items(items: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a compact list of the player's items, skipping empty slots."""
    result: list[dict[str, Any]] = []
    for slot in _RELEVANT_ITEM_SLOTS:
        item = items.get(slot)
        if not item or item.get("name") in (None, "empty"):
            continue

        entry: dict[str, Any] = {"name": _strip(item["name"], _ITEM_PREFIX)}

        charges = item.get("charges")
        if charges:
            entry["charges"] = charges

        cooldown = item.get("cooldown")
        if cooldown:
            entry["cooldown"] = cooldown

        result.append(entry)
    return result


def _serialize_abilities(
    abilities: dict[str, Any],
    hero_name: str,
) -> tuple[list[dict[str, Any]], int]:
    """Build a compact ability list and sum their levels.

    The hero name is used to strip the hero-specific prefix from each
    ability (e.g. "juggernaut_blade_fury" -> "blade_fury"). Abilities
    without that prefix are kept as-is.
    """
    ability_prefix = f"{hero_name}_" if hero_name else ""
    result: list[dict[str, Any]] = []
    spent_levels = 0
    for ability in abilities.values():
        name = ability.get("name")
        if not name or name.startswith("empty"):
            continue

        level = ability.get("level", 0)
        spent_levels += level

        clean_name = _strip(name, ability_prefix) if ability_prefix else name
        entry: dict[str, Any] = {"name": clean_name, "level": level}

        if ability.get("ultimate"):
            entry["ultimate"] = True

        cooldown = ability.get("cooldown")
        if cooldown:
            entry["cooldown"] = cooldown

        result.append(entry)
    return result, spent_levels


def serialize(payload: dict[str, Any]) -> dict[str, Any]:
    """Turn a raw GSI payload into the compact coach state dictionary."""
    game_map: dict[str, Any] = payload.get("map", {})
    player: dict[str, Any] = payload.get("player", {})
    hero: dict[str, Any] = payload.get("hero", {})
    items: dict[str, Any] = payload.get("items", {})
    abilities: dict[str, Any] = payload.get("abilities", {})

    hero_name = _strip(hero.get("name", ""), _HERO_PREFIX)
    ability_list, spent_levels = _serialize_abilities(abilities, hero_name)

    hero_level = hero.get("level", 0)
    unspent_points = max(0, hero_level - spent_levels)

    state = _strip(game_map.get("game_state", ""), _STATE_PREFIX)
    zone = _map_zone(hero.get("xpos"), hero.get("ypos"), player.get("team_name"))

    return {
        "clock": game_map.get("clock_time"),
        "game_state": state,
        "daytime": game_map.get("daytime"),
        "score": {
            "radiant": game_map.get("radiant_score"),
            "dire": game_map.get("dire_score"),
        },
        "hero": {
            "name": hero_name,
            "level": hero_level,
            "alive": hero.get("alive"),
            "health_percent": hero.get("health_percent"),
            "mana_percent": hero.get("mana_percent"),
            "has_scepter": hero.get("aghanims_scepter"),
            "has_shard": hero.get("aghanims_shard"),
            "unspent_ability_points": unspent_points,
            "zone": zone,
        },
        "economy": {
            "gold": player.get("gold"),
            "gpm": player.get("gpm"),
            "xpm": player.get("xpm"),
        },
        "kda": {
            "kills": player.get("kills"),
            "deaths": player.get("deaths"),
            "assists": player.get("assists"),
            "last_hits": player.get("last_hits"),
            "denies": player.get("denies"),
        },
        "items": _serialize_items(items),
        "abilities": ability_list,
    }