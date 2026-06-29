"""Tests for the GSI serializer."""

from typing import Any

from dota_coach.serializer import serialize


def _base_payload() -> dict[str, Any]:
    """A minimal in-progress payload with the fields the serializer reads."""
    return {
        "map": {
            "clock_time": 600,
            "game_state": "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
            "daytime": True,
            "radiant_score": 3,
            "dire_score": 5,
        },
        "player": {
            "team_name": "radiant",
            "gold": 1500,
            "gpm": 450,
            "xpm": 500,
            "kills": 2,
            "deaths": 1,
            "assists": 4,
            "last_hits": 80,
            "denies": 10,
        },
        "hero": {
            "name": "npc_dota_hero_juggernaut",
            "level": 7,
            "alive": True,
            "health_percent": 90,
            "mana_percent": 60,
            "aghanims_scepter": False,
            "aghanims_shard": True,
            "xpos": -6700,
            "ypos": -6700,
        },
        "items": {
            "slot0": {"name": "item_tango", "charges": 2},
            "slot1": {"name": "empty"},
            "slot2": {"name": "item_power_treads"},
            "teleport0": {"name": "item_tpscroll", "cooldown": 0},
        },
        "abilities": {
            "ability0": {"name": "juggernaut_blade_fury", "level": 4},
            "ability1": {"name": "juggernaut_healing_ward", "level": 1},
            "ability4": {
                "name": "juggernaut_omni_slash",
                "level": 2,
                "ultimate": True,
            },
        },
    }


def test_strips_hero_and_state_prefixes() -> None:
    result = serialize(_base_payload())
    assert result["hero"]["name"] == "juggernaut"
    assert result["game_state"] == "GAME_IN_PROGRESS"


def test_skips_empty_item_slots() -> None:
    result = serialize(_base_payload())
    names = [item["name"] for item in result["items"]]
    assert "empty" not in names
    assert "tango" in names
    assert "power_treads" in names


def test_keeps_charges_but_not_zero_cooldown() -> None:
    result = serialize(_base_payload())
    tango = next(i for i in result["items"] if i["name"] == "tango")
    tpscroll = next(i for i in result["items"] if i["name"] == "tpscroll")
    assert tango["charges"] == 2
    # Cooldown of 0 should be omitted, not included as 0.
    assert "cooldown" not in tpscroll


def test_strips_ability_hero_prefix() -> None:
    result = serialize(_base_payload())
    names = [ability["name"] for ability in result["abilities"]]
    assert "blade_fury" in names
    assert "omni_slash" in names


def test_marks_ultimate() -> None:
    result = serialize(_base_payload())
    omni = next(a for a in result["abilities"] if a["name"] == "omni_slash")
    assert omni["ultimate"] is True


def test_computes_unspent_ability_points() -> None:
    # Hero level 7, spent levels 4 + 1 + 2 = 7, so 0 unspent.
    result = serialize(_base_payload())
    assert result["hero"]["unspent_ability_points"] == 0


def test_unspent_points_when_level_exceeds_spent() -> None:
    payload = _base_payload()
    payload["hero"]["level"] = 8  # one more level than spent abilities
    result = serialize(payload)
    assert result["hero"]["unspent_ability_points"] == 1


def test_zone_own_base_for_radiant() -> None:
    result = serialize(_base_payload())
    assert result["hero"]["zone"] == "own_base"


def test_zone_none_without_position() -> None:
    payload = _base_payload()
    del payload["hero"]["xpos"]
    del payload["hero"]["ypos"]
    result = serialize(payload)
    assert result["hero"]["zone"] is None


def test_handles_empty_early_phase_payload() -> None:
    # Hero selection: hero is almost empty. Should not crash.
    payload: dict[str, Any] = {
        "map": {
            "clock_time": -74,
            "game_state": "DOTA_GAMERULES_STATE_HERO_SELECTION",
        },
        "player": {},
        "hero": {"id": 0},
        "items": {},
        "abilities": {},
    }
    result = serialize(payload)
    assert result["hero"]["name"] == ""
    assert result["items"] == []
    assert result["abilities"] == []


def test_dire_team_zone_is_mirrored() -> None:
    # Same deep-negative coords mean enemy_half for Dire, not own_base.
    payload = _base_payload()
    payload["player"]["team_name"] = "dire"
    result = serialize(payload)
    assert result["hero"]["zone"] == "enemy_half"

def test_skips_empty_ability_placeholders() -> None:
    # Some heroes (e.g. Doom) expose empty ability slots like "empty1".
    payload = _base_payload()
    payload["abilities"]["ability2"] = {"name": "empty1", "level": 0}
    payload["abilities"]["ability3"] = {"name": "empty2", "level": 0}
    result = serialize(payload)
    names = [ability["name"] for ability in result["abilities"]]
    assert not any(n.startswith("empty") for n in names)