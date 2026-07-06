"""The coaching brain: turns detected events into spoken advice via Ollama.

It builds an event-specific prompt, sends it to a local Ollama model along
with the current game state, and returns short, direct advice in English.
"""

import json
from typing import Any

import ollama

from dota_coach import console
from dota_coach.detection.events import Event, EventType
from dota_coach.gamedata.context import load_context
from dota_coach.gamedata.heroes_data import lookup_hero
from dota_coach.gamedata.items_data import item_name_map, lookup_many
from dota_coach.mind.memory import AdviceMemory

# The coach's persona and hard rules, shared by every request.
_SYSTEM_PROMPT = (
    "You are an Immortal-ranked Dota 2 coach. Always reply in English, no "
    "matter what; never use Spanish, Chinese, or any other language. You are "
    "direct and critical, no filler. Your advice is for the local player while "
    "they play. Always reply in at most 2 short sentences. Do not greet or pad "
    "unless asked. Get straight to the actionable point.\n\n"
    "STRICT RULES:\n"
    "- Only mention items and abilities that truly exist in Dota 2. If you are "
    "not sure of a name, do not use it. Never invent names.\n"
    "- You know EXACTLY which items the player currently has (they are in the "
    "data). Never say 'if you have' or 'if you don't have' an item: you already "
    "know. Never recommend buying something they already own.\n"
    "- Dota 2 ability level rules: normal abilities go up to level 4 maximum. "
    "The ultimate goes up to level 3 maximum and only at hero levels 6, 12 and "
    "18. Never suggest leveling an ability above its maximum.\n"
    "- To level abilities, use ONLY the current ability-level list (the one "
    "with can_level). Only suggest leveling those with can_level=true, to the "
    "next level (level + 1). Never suggest leveling an ability not in that list "
    "(it may be item-granted like Aghanim's Shard or Scepter, or not owned "
    "yet), nor one with can_level=false.\n"
    "- Talents are chosen only at hero levels 10, 15, 20 and 25.\n"
    "- If you lack enough data, give general advice instead of inventing "
    "names.\n"
    "- Use the match context (role, allies, enemies) when available: adapt the "
    "advice to the player's role (a support and a carry play differently) and "
    "to the enemy heroes. If the context is empty, give general advice and you "
    "may ask them to provide the draft.\n"
)

# Event-specific instructions. Each tells the model what to focus on.
_EVENT_INSTRUCTIONS: dict[EventType, str] = {
    EventType.STRATEGY_TIME: (
        "Hero selection just ended and the strategy phase begins. Greet "
        "briefly and say you are ready to plan. If you do not know the enemy "
        "draft yet, ask them to tell you."
    ),
    EventType.MATCH_STARTED: (
        "The match just started. Greet in one sentence and say you are ready "
        "to assist. Short and energetic."
    ),
    EventType.STARTING_ITEMS_CHECK: (
        "Review the player's starting items for their hero. If something "
        "typical of the opening is missing or excessive, say so. If it looks "
        "good, confirm it briefly."
    ),
    EventType.HERO_DIED: (
        "The player just died. Give one brief, concrete tip to avoid repeating "
        "the mistake: positioning, vision, or timing."
    ),
    EventType.HERO_KILL: (
        "The player just got a kill. In the excitement it is easy to miss what "
        "matters: remind them to check their health and mana, whether they "
        "have consumables to heal, and which abilities or items are ready to "
        "keep going or to escape."
    ),
    EventType.LEVELED_UP: (
        "The player just leveled up. Remind them to spend their skill point "
        "and suggest which ability to level based on their hero and the phase."
    ),
    EventType.LOW_HEALTH: (
        "The player has critical health. Warn them urgently in a single very "
        "short sentence to retreat or use healing."
    ),
    EventType.LOW_MANA: (
        "The player has critical mana. Tell them briefly to manage their mana: "
        "not to run out of resources for key abilities, or to consider "
        "regenerating."
    ),
    EventType.HIGH_UNSPENT_GOLD: (
        "The player has a lot of unspent gold. Suggest going to the shop and "
        "what to buy for their hero and role, without inventing item names."
    ),
    EventType.SCOUTING_REMINDER: (
        "Periodic reminder to check the enemy team. If you know the enemy "
        "draft, name real threats; otherwise, suggest checking their items."
    ),
}


def _skill_status(
    abilities: list[dict[str, Any]], display_names: dict[str, str]
) -> list[dict[str, Any]]:
    """Annotate each player ability with its cap and whether it can be leveled.

    Normal abilities cap at 4, ultimates at 3. This is computed in code so the
    model does not have to reason about level limits (which it does poorly).
    The internal name is mapped to its display name so the model never sees
    raw keys like "voodoo_restoration".
    """
    result: list[dict[str, Any]] = []
    for ability in abilities:
        raw = ability.get("name", "")
        level = ability.get("level", 0)
        cap = 3 if ability.get("ultimate") else 4
        result.append(
            {
                "name": display_names.get(raw, raw),
                "level": level,
                "max": cap,
                "can_level": level < cap,
            }
        )
    return result


class Brain:
    """Generates coaching advice from events using a local Ollama model."""

    def __init__(self, model: str) -> None:
        self._model = model
        self._memory = AdviceMemory()

    def _build_prompt(self, event: Event, state: dict[str, Any]) -> str:
        """Compose the user prompt from the event and the current state."""
        instruction = _EVENT_INSTRUCTIONS.get(
            event.type, "Give the player a brief, useful tip."
        )
        state_json = json.dumps(state, ensure_ascii=False)
        extra = json.dumps(event.data, ensure_ascii=False) if event.data else "{}"

        # Real data for the items the player currently holds, so the model
        # reasons with true names, costs and effects instead of inventing them.
        item_names = [item["name"] for item in state.get("items", [])]
        item_data = lookup_many(item_names)
        item_json = json.dumps(item_data, ensure_ascii=False)

        # Real abilities, talents and facets for the player's hero, so the
        # model uses true ability names instead of guessing them.
        hero_name = state.get("hero", {}).get("name", "")
        hero_data = lookup_hero(hero_name)
        # Map internal ability keys to display names before dropping the key,
        # so skill status can show "Voodoo Restoration" instead of the raw key.
        display_names = {
            a.get("key", ""): a.get("name", "")
            for a in (hero_data["abilities"] if hero_data else [])
        }
        # Add items (internal -> display) so the memory can also detect item
        # advice. item_name_map is display -> internal, so invert it.
        for display, internal in item_name_map().items():
            display_names.setdefault(internal, display)
        self._last_display_names = display_names
        if hero_data:
            # Keep only abilities the player actually has in the live state, so
            # item-granted ones (Aghanim's Shard/Scepter) the player has not
            # bought are never shown and cannot be suggested to level.
            owned = {a.get("name") for a in state.get("abilities", [])}
            hero_data["abilities"] = [
                {k: v for k, v in a.items() if k != "key"}
                for a in hero_data["abilities"]
                if a.get("key") in owned
            ]
        hero_json = json.dumps(hero_data, ensure_ascii=False) if hero_data else "{}"

        # The player's current abilities with level caps and what can be leveled,
        # computed in code so the model does not misjudge level limits. Names are
        # mapped to display form so the model never sees raw internal keys.
        skills = _skill_status(state.get("abilities", []), display_names)
        skills_json = json.dumps(skills, ensure_ascii=False)

        # Manual context the player provides (role and draft), which GSI
        # cannot give us. Read fresh so mid-match edits take effect.
        context = load_context()
        context_json = json.dumps(context, ensure_ascii=False)

        # Advice the player already acted on, so the model stops repeating it.
        acted = self._memory.fulfilled(state, display_names)
        acted_line = (
            f"You already advised these and the player acted on them; do not "
            f"repeat them, move on: {', '.join(acted)}.\n"
            if acted
            else ""
        )

        # Advice given very recently: do not repeat it yet, acted on or not.
        recent = self._memory.recently_advised(60.0)
        recent_line = (
            f"You mentioned these in the last minute; do not bring them up "
            f"again yet: {', '.join(recent)}.\n"
            if recent
            else ""
        )

        return (
            f"{instruction}\n\n"
            f"Current player state (JSON): {state_json}\n"
            f"Real data for your current items (name, cost, effect): "
            f"{item_json}\n"
            f"Reference for what your hero's abilities and talents do (do NOT "
            f"use this list to decide which to level, only to know what they "
            f"do): {hero_json}\n"
            f"Current level of your abilities and which you can level up "
            f"(can_level=true means it is not yet at maximum): "
            f"{skills_json}\n"
            f"Match context the player gave you (your role, allies and "
            f"enemies; GSI does not provide this): {context_json}\n"
            f"Event data: {extra}\n\n"
            f"{acted_line}"
            f"{recent_line}"
            f"The player ALREADY has the items listed above; do not recommend "
            f"them again. For abilities and talents use ONLY the real names "
            f"listed above, never invent. Reply in English."
        )

    def advise(self, event: Event, state: dict[str, Any]) -> str:
        """Ask the model for advice. Returns the advice text, or '' on error."""
        prompt = self._build_prompt(event, state)
        try:
            response = ollama.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                options={"num_predict": 120, "temperature": 0.4},
            )
        except Exception as error:
            console.error(f"Ollama error: {error}")
            return ""
        advice = str(response["message"]["content"]).strip()
        self._memory.record(advice, state, self._last_display_names)
        return advice