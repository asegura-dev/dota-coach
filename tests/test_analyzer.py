"""Tests for the event detector."""

from typing import Any

from dota_coach.detection.analyzer import EventDetector
from dota_coach.detection.events import EventType


def _state(
    *,
    game_state: str = "GAME_IN_PROGRESS",
    alive: bool = True,
    health_percent: int = 100,
    mana_percent: int = 100,
    level: int = 1,
    gold: int = 0,
    kills: int = 0,
) -> dict[str, Any]:
    """Build a minimal coach state for the detector."""
    return {
        "game_state": game_state,
        "hero": {
            "alive": alive,
            "health_percent": health_percent,
            "mana_percent": mana_percent,
            "level": level,
        },
        "economy": {"gold": gold},
        "kda": {"kills": kills},
    }


def _types(events: list[Any]) -> list[EventType]:
    return [event.type for event in events]


def test_match_started_fires_once() -> None:
    detector = EventDetector()
    first = detector.detect(_state(), clock=0)
    second = detector.detect(_state(), clock=1)
    assert EventType.MATCH_STARTED in _types(first)
    assert EventType.MATCH_STARTED not in _types(second)


def test_hero_death_detected_on_transition() -> None:
    detector = EventDetector()
    detector.detect(_state(alive=True), clock=0)
    events = detector.detect(_state(alive=False), clock=1)
    assert EventType.HERO_DIED in _types(events)


def test_no_death_while_staying_dead() -> None:
    detector = EventDetector()
    detector.detect(_state(alive=True), clock=0)
    detector.detect(_state(alive=False), clock=1)
    events = detector.detect(_state(alive=False), clock=2)
    assert EventType.HERO_DIED not in _types(events)


def test_low_health_fires_on_crossing() -> None:
    detector = EventDetector()
    detector.detect(_state(health_percent=100), clock=0)
    events = detector.detect(_state(health_percent=15), clock=1)
    assert EventType.LOW_HEALTH in _types(events)


def test_low_health_does_not_repeat_while_low() -> None:
    detector = EventDetector()
    detector.detect(_state(health_percent=100), clock=0)
    detector.detect(_state(health_percent=15), clock=1)
    # Still low, within cooldown: should not fire again.
    events = detector.detect(_state(health_percent=10), clock=5)
    assert EventType.LOW_HEALTH not in _types(events)


def test_low_health_rearms_after_recovery() -> None:
    detector = EventDetector()
    detector.detect(_state(health_percent=100), clock=0)
    detector.detect(_state(health_percent=15), clock=1)
    detector.detect(_state(health_percent=80), clock=30)  # recovered, re-armed
    events = detector.detect(_state(health_percent=15), clock=60)
    assert EventType.LOW_HEALTH in _types(events)


def test_high_unspent_gold_fires() -> None:
    detector = EventDetector()
    events = detector.detect(_state(gold=1500), clock=0)
    assert EventType.HIGH_UNSPENT_GOLD in _types(events)


def test_high_gold_respects_cooldown() -> None:
    detector = EventDetector()
    detector.detect(_state(gold=1500), clock=0)
    events = detector.detect(_state(gold=1600), clock=30)  # within 60s cooldown
    assert EventType.HIGH_UNSPENT_GOLD not in _types(events)


def test_leveled_up_fires_on_level_increase() -> None:
    detector = EventDetector()
    detector.detect(_state(level=1), clock=0)
    events = detector.detect(_state(level=2), clock=1)
    assert EventType.LEVELED_UP in _types(events)


def test_no_level_up_when_level_unchanged() -> None:
    detector = EventDetector()
    detector.detect(_state(level=3), clock=0)
    events = detector.detect(_state(level=3), clock=1)
    assert EventType.LEVELED_UP not in _types(events)


def test_scouting_reminder_is_periodic() -> None:
    detector = EventDetector()
    # First tick starts the match; scouting should fire after start.
    detector.detect(_state(), clock=0)
    # Within 180s: no new reminder.
    early = detector.detect(_state(), clock=100)
    # After 180s: reminder fires again.
    late = detector.detect(_state(), clock=200)
    assert EventType.SCOUTING_REMINDER not in _types(early)
    assert EventType.SCOUTING_REMINDER in _types(late)


def test_no_events_in_hero_selection() -> None:
    detector = EventDetector()
    events = detector.detect(_state(game_state="HERO_SELECTION"), clock=-74)
    assert events == []

def test_starting_items_check_fires_in_pre_game() -> None:
    detector = EventDetector()
    state = _state(game_state="PRE_GAME")
    state["hero"]["name"] = "juggernaut"
    events = detector.detect(state, clock=-80)
    assert EventType.STARTING_ITEMS_CHECK in _types(events)


def test_starting_items_check_fires_once() -> None:
    detector = EventDetector()
    state = _state(game_state="PRE_GAME")
    state["hero"]["name"] = "juggernaut"
    detector.detect(state, clock=-80)
    second = detector.detect(state, clock=-79)
    assert EventType.STARTING_ITEMS_CHECK not in _types(second)


def test_starting_items_check_needs_a_hero() -> None:
    # In hero selection there is no hero name yet, so it must not fire.
    detector = EventDetector()
    state = _state(game_state="PRE_GAME")
    state["hero"]["name"] = ""
    events = detector.detect(state, clock=-80)
    assert EventType.STARTING_ITEMS_CHECK not in _types(events)


def test_low_mana_fires_on_crossing() -> None:
    detector = EventDetector()
    detector.detect(_state(mana_percent=100), clock=0)
    events = detector.detect(_state(mana_percent=15), clock=1)
    assert EventType.LOW_MANA in _types(events)


def test_low_mana_does_not_repeat_while_low() -> None:
    detector = EventDetector()
    detector.detect(_state(mana_percent=100), clock=0)
    detector.detect(_state(mana_percent=15), clock=1)
    events = detector.detect(_state(mana_percent=10), clock=5)
    assert EventType.LOW_MANA not in _types(events)


def test_low_mana_rearms_after_recovery() -> None:
    detector = EventDetector()
    detector.detect(_state(mana_percent=100), clock=0)
    detector.detect(_state(mana_percent=15), clock=1)
    detector.detect(_state(mana_percent=80), clock=40)  # recovered, re-armed
    events = detector.detect(_state(mana_percent=15), clock=80)
    assert EventType.LOW_MANA in _types(events)


def test_hero_kill_fires_on_kill_increase() -> None:
    detector = EventDetector()
    detector.detect(_state(kills=0), clock=0)
    events = detector.detect(_state(kills=1), clock=1)
    assert EventType.HERO_KILL in _types(events)


def test_hero_kill_respects_cooldown() -> None:
    detector = EventDetector()
    detector.detect(_state(kills=0), clock=0)
    detector.detect(_state(kills=1), clock=1)
    events = detector.detect(_state(kills=2), clock=20)  # within 45s cooldown
    assert EventType.HERO_KILL not in _types(events)


def test_no_kill_event_when_kills_unchanged() -> None:
    detector = EventDetector()
    detector.detect(_state(kills=3), clock=0)
    events = detector.detect(_state(kills=3), clock=1)
    assert EventType.HERO_KILL not in _types(events)


def test_strategy_time_fires_once() -> None:
    detector = EventDetector()
    first = detector.detect(_state(game_state="STRATEGY_TIME"), clock=-29)
    second = detector.detect(_state(game_state="STRATEGY_TIME"), clock=-28)
    assert EventType.STRATEGY_TIME in _types(first)
    assert EventType.STRATEGY_TIME not in _types(second)