"""Detects noteworthy events by comparing successive game states.

The analyzer holds memory between ticks: the previous state, the last time
each event fired (for cooldowns), and which threshold events are "armed".
It does not decide what to say; it only reports what changed.
"""

from typing import Any

from dota_coach.events import Event, EventType

# Thresholds (tunable).
_LOW_HEALTH_PERCENT = 20
_LOW_MANA_PERCENT = 20
_HIGH_UNSPENT_GOLD = 1000

# Cooldowns in seconds, per event type. Absent means "no cooldown".
_COOLDOWNS: dict[EventType, float] = {
    EventType.LEVELED_UP: 30.0,
    EventType.LOW_HEALTH: 20.0,
    EventType.LOW_MANA: 30.0,
    EventType.HIGH_UNSPENT_GOLD: 60.0,
    EventType.SCOUTING_REMINDER: 180.0,
    EventType.HERO_KILL: 45.0,
}


class EventDetector:
    """Stateful detector that emits events as the game state evolves."""

    def __init__(self) -> None:
        self._prev: dict[str, Any] | None = None
        self._match_started_fired = False
        self._starting_items_fired = False
        self._last_fired: dict[EventType, float] = {}
        # Threshold events are "armed" until they fire, then re-arm on recovery.
        self._low_health_armed = True
        self._low_mana_armed = True

    def _on_cooldown(self, event_type: EventType, clock: float) -> bool:
        """True if the event fired too recently to fire again."""
        cooldown = _COOLDOWNS.get(event_type)
        if cooldown is None:
            return False
        last = self._last_fired.get(event_type)
        return last is not None and (clock - last) < cooldown

    def _fire(self, event_type: EventType, clock: float) -> None:
        """Record that an event fired, for cooldown tracking."""
        self._last_fired[event_type] = clock

    def detect(self, state: dict[str, Any], clock: float) -> list[Event]:
        """Compare the new state to the previous one and return new events."""
        events: list[Event] = []
        hero = state.get("hero", {})
        economy = state.get("economy", {})
        in_progress = state.get("game_state") == "GAME_IN_PROGRESS"

        # Match started: fire once when we first see an in-progress game.
        if not self._match_started_fired and in_progress:
            events.append(Event(EventType.MATCH_STARTED))
            self._match_started_fired = True

        # Starting items check: fire once during pre-game, when the hero exists.
        if (
            not self._starting_items_fired
            and state.get("game_state") == "PRE_GAME"
            and hero.get("name")
        ):
            events.append(Event(EventType.STARTING_ITEMS_CHECK))
            self._starting_items_fired = True

        # Hero died: alive -> not alive transition.
        if self._prev is not None:
            was_alive = self._prev.get("hero", {}).get("alive")
            is_alive = hero.get("alive")
            if was_alive and is_alive is False:
                events.append(Event(EventType.HERO_DIED))

        # Hero kill: the player's kill count increased since the last tick.
        if in_progress and self._prev is not None:
            prev_kills = self._prev.get("kda", {}).get("kills") or 0
            kills = state.get("kda", {}).get("kills") or 0
            if kills > prev_kills and not self._on_cooldown(
                EventType.HERO_KILL, clock
            ):
                events.append(Event(EventType.HERO_KILL, {"kills": kills}))
                self._fire(EventType.HERO_KILL, clock)

        # Leveled up: hero level increased since the previous tick.
        level = hero.get("level", 0)
        if in_progress and self._prev is not None:
            prev_level = self._prev.get("hero", {}).get("level", 0)
            if level > prev_level and not self._on_cooldown(
                EventType.LEVELED_UP, clock
            ):
                events.append(Event(EventType.LEVELED_UP, {"level": level}))
                self._fire(EventType.LEVELED_UP, clock)

        # Low health: fire when crossing below the threshold; re-arm on recovery.
        hp = hero.get("health_percent")
        if in_progress and hp is not None and hero.get("alive"):
            if (
                hp < _LOW_HEALTH_PERCENT
                and self._low_health_armed
                and not self._on_cooldown(EventType.LOW_HEALTH, clock)
            ):
                events.append(Event(EventType.LOW_HEALTH, {"hp": hp}))
                self._fire(EventType.LOW_HEALTH, clock)
                self._low_health_armed = False
            elif hp >= _LOW_HEALTH_PERCENT:
                self._low_health_armed = True

        # Low mana: same edge-detection logic as low health.
        mp = hero.get("mana_percent")
        if in_progress and mp is not None and hero.get("alive"):
            if (
                mp < _LOW_MANA_PERCENT
                and self._low_mana_armed
                and not self._on_cooldown(EventType.LOW_MANA, clock)
            ):
                events.append(Event(EventType.LOW_MANA, {"mana": mp}))
                self._fire(EventType.LOW_MANA, clock)
                self._low_mana_armed = False
            elif mp >= _LOW_MANA_PERCENT:
                self._low_mana_armed = True

        # High unspent gold.
        gold = economy.get("gold")
        if (
            in_progress
            and gold is not None
            and gold > _HIGH_UNSPENT_GOLD
            and not self._on_cooldown(EventType.HIGH_UNSPENT_GOLD, clock)
        ):
            events.append(Event(EventType.HIGH_UNSPENT_GOLD, {"gold": gold}))
            self._fire(EventType.HIGH_UNSPENT_GOLD, clock)

        # Scouting reminder: periodic, only after the match has started.
        if (
            in_progress
            and self._match_started_fired
            and not self._on_cooldown(EventType.SCOUTING_REMINDER, clock)
        ):
            events.append(Event(EventType.SCOUTING_REMINDER))
            self._fire(EventType.SCOUTING_REMINDER, clock)

        self._prev = state
        return events