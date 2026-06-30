"""Event definitions emitted by the analyzer when the game state changes."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EventType(StrEnum):
    """Types of noteworthy events the analyzer can detect."""

    MATCH_STARTED = "match_started"
    HERO_DIED = "hero_died"
    HERO_KILL = "hero_kill"
    LEVELED_UP = "leveled_up"
    LOW_MANA = "low_mana"
    LOW_HEALTH = "low_health"
    HIGH_UNSPENT_GOLD = "high_unspent_gold"
    SCOUTING_REMINDER = "scouting_reminder"
    STARTING_ITEMS_CHECK = "starting_items_check"


@dataclass(frozen=True)
class Event:
    """A single detected event, with optional supporting data."""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)