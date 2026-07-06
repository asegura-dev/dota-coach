"""Tracks recent advice so the coach avoids repeating tips the player acted on.

The idea is not to ban repetition, but to drop it once it no longer helps. When
advice mentions a known ability or item, that entity is remembered with the
state it had at the time (an ability's level, or that an item was not owned yet).
On the next advice, entities whose state has since changed (the ability leveled
up, the item was bought) count as fulfilled: the player acted on the tip, so the
coach should move on. Entities that have not changed are still fair to mention.
"""

import time
from typing import Any


class AdviceMemory:
    """Remembers advised abilities and items, and tells which were acted on."""

    def __init__(self, ttl_seconds: float = 150.0) -> None:
        # display name -> (kind, marker, timestamp)
        #   kind "ability": marker is the level when advised.
        #   kind "item":    marker is the internal item name (to match inventory).
        self._advised: dict[str, tuple[str, Any, float]] = {}
        self._ttl = ttl_seconds

    def record(
        self,
        advice: str,
        state: dict[str, Any],
        display_names: dict[str, str],
    ) -> None:
        """Store which known abilities or items the advice mentioned."""
        now = time.monotonic()
        text = advice.lower()

        # Abilities: remember the level at advice time.
        advised_abilities = set()
        for ability in state.get("abilities", []):
            internal = ability.get("name", "")
            display = display_names.get(internal, "")
            if display and display.lower() in text:
                self._advised[display] = ("ability", ability.get("level", 0), now)
                advised_abilities.add(display)

        # Items: remember the internal name, only for items not owned yet.
        owned = {item.get("name", "") for item in state.get("items", [])}
        for internal, display in display_names.items():
            if display in advised_abilities:
                continue  # already handled as an ability
            if display.lower() in text and internal not in owned:
                self._advised[display] = ("item", internal, now)

    def fulfilled(
        self,
        state: dict[str, Any],
        display_names: dict[str, str],
    ) -> list[str]:
        """Return advised entities the player has since acted on."""
        now = time.monotonic()
        current_levels = {
            display_names.get(a.get("name", ""), ""): a.get("level", 0)
            for a in state.get("abilities", [])
        }
        owned = {item.get("name", "") for item in state.get("items", [])}

        done: list[str] = []
        for name, (kind, marker, ts) in list(self._advised.items()):
            if now - ts >= self._ttl:
                del self._advised[name]
                continue
            if kind == "item":
                if marker in owned:
                    done.append(name)
                    self._advised.pop(name, None)
            else:
                if current_levels.get(name, marker) > marker:
                    done.append(name)
                    self._advised.pop(name, None)
        return done
    

    def recently_advised(self, cooldown: float = 60.0) -> list[str]:
        """Return entities advised within the last `cooldown` seconds.

        These were mentioned so recently that repeating them would be spam,
        whether or not the player has acted on them yet. The caller uses this
        to tell the model not to bring them up again for now.
        """
        now = time.monotonic()
        return [
            name
            for name, (_kind, _marker, ts) in self._advised.items()
            if now - ts < cooldown
        ]