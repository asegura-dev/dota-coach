"""Tests for AdviceMemory: repetition is dropped only once the player acts."""

from typing import Any

from dota_coach.memory import AdviceMemory

# Display map used across tests: internal name -> display name.
_NAMES = {
    "maledict": "Maledict",
    "paralyzing_cask": "Paralyzing Cask",
    "blink": "Blink Dagger",
}


def _state(
    *,
    abilities: list[dict[str, Any]] | None = None,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {"abilities": abilities or [], "items": items or []}


def test_ability_fulfilled_when_level_rises() -> None:
    memory = AdviceMemory()
    state = _state(abilities=[{"name": "maledict", "level": 2}])
    memory.record("Level up Maledict for control.", state, _NAMES)

    later = _state(abilities=[{"name": "maledict", "level": 3}])
    assert memory.fulfilled(later, _NAMES) == ["Maledict"]


def test_ability_not_fulfilled_when_level_unchanged() -> None:
    memory = AdviceMemory()
    state = _state(abilities=[{"name": "maledict", "level": 2}])
    memory.record("Level up Maledict for control.", state, _NAMES)

    same = _state(abilities=[{"name": "maledict", "level": 2}])
    assert memory.fulfilled(same, _NAMES) == []


def test_item_fulfilled_when_bought() -> None:
    memory = AdviceMemory()
    state = _state(items=[{"name": "tango"}])
    memory.record("Buy a Blink Dagger to initiate.", state, _NAMES)

    later = _state(items=[{"name": "tango"}, {"name": "blink"}])
    assert memory.fulfilled(later, _NAMES) == ["Blink Dagger"]


def test_item_not_fulfilled_when_still_missing() -> None:
    memory = AdviceMemory()
    state = _state(items=[{"name": "tango"}])
    memory.record("Buy a Blink Dagger to initiate.", state, _NAMES)

    same = _state(items=[{"name": "tango"}])
    assert memory.fulfilled(same, _NAMES) == []


def test_generic_advice_records_nothing() -> None:
    memory = AdviceMemory()
    state = _state(abilities=[{"name": "maledict", "level": 2}])
    memory.record("Retreat now and hold your position.", state, _NAMES)

    later = _state(abilities=[{"name": "maledict", "level": 3}])
    assert memory.fulfilled(later, _NAMES) == []


def test_expired_entry_is_dropped() -> None:
    memory = AdviceMemory(ttl_seconds=0.0)
    state = _state(abilities=[{"name": "maledict", "level": 2}])
    memory.record("Level up Maledict.", state, _NAMES)

    later = _state(abilities=[{"name": "maledict", "level": 3}])
    # With a zero TTL the entry has already expired, so nothing is reported.
    assert memory.fulfilled(later, _NAMES) == []