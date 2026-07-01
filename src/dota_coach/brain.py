"""The coaching brain: turns detected events into spoken advice via Ollama.

It builds an event-specific prompt, sends it to a local Ollama model along
with the current game state, and returns short, direct advice in Spanish.
"""

import json
from typing import Any

import ollama

from dota_coach import console
from dota_coach.context import load_context
from dota_coach.events import Event, EventType
from dota_coach.heroes_data import lookup_hero
from dota_coach.items_data import lookup_many

# The coach's persona and hard rules, shared by every request.
_SYSTEM_PROMPT = (
    "Eres un coach de Dota 2 de rango Immortal. Responde SIEMPRE en español, "
    "pase lo que pase; nunca uses ingles, chino ni otro idioma para el texto "
    "del consejo (los nombres propios de items y habilidades si van en ingles). "
    "Eres directo y critico, sin rodeos. Tus consejos son para el jugador local "
    "mientras juega. Responde SIEMPRE en maximo 2 frases cortas. No saludes "
    "ni uses relleno salvo que se te pida. Ve al grano con lo accionable.\n\n"
    "REGLAS ESTRICTAS:\n"
    "- Los nombres de items y habilidades van SIEMPRE en ingles exacto "
    "(ej: 'Phase Boots', 'Force of Nature'). Nunca los traduzcas ni los "
    "inventes.\n"
    "- Solo menciona items y habilidades que existan de verdad en Dota 2. "
    "Si no estas seguro del nombre, no lo uses.\n"
    "- Conoces EXACTAMENTE los items que el jugador tiene ahora mismo (estan "
    "en los datos). Nunca digas 'si tienes' o 'si no tienes' un item: ya lo "
    "sabes. Nunca recomiendes comprar algo que ya posee.\n"
    "- Reglas de niveles de habilidad en Dota 2: las habilidades normales "
    "suben hasta nivel 4 como maximo. El ultimate sube hasta nivel 3 como "
    "maximo y solo en los niveles de heroe 6, 12 y 18. Nunca sugieras subir "
    "una habilidad por encima de su maximo.\n"
    "- Para subir habilidades, usa la lista de habilidades del jugador con "
    "can_level: solo sugiere subir habilidades con can_level=true, y nombra "
    "el nivel siguiente (level + 1). Nunca sugieras una con can_level=false "
    "ni un nivel mayor a su max.\n"
    "- Los talentos se eligen solo en los niveles de heroe 10, 15, 20 y 25.\n"
    "- Si no tienes datos suficientes, da un consejo general en vez de "
    "inventar nombres."
    "- Usa el contexto de la partida (rol, aliados, enemigos) cuando este "
    "disponible: adapta el consejo a tu rol (un support y un carry juegan "
    "distinto) y a los heroes enemigos. Si el contexto esta vacio, aconseja "
    "de forma general y puedes pedir que te indiquen el draft.\n"
)

# Event-specific instructions. Each tells the model what to focus on.
_EVENT_INSTRUCTIONS: dict[EventType, str] = {
    EventType.STRATEGY_TIME: (
        "Termino la seleccion de heroes y empieza la fase de estrategia. "
        "Saluda corto y di que estas listo para planear. Si no conoces el "
        "draft enemigo aun, pide que te lo indiquen."
    ),
    EventType.MATCH_STARTED: (
        "La partida acaba de empezar. Saluda en una frase y di que estas "
        "listo para asistir. Breve y con energia."
    ),
    EventType.STARTING_ITEMS_CHECK: (
        "Revisa los items iniciales del jugador segun su heroe. Si falta algo "
        "tipico de inicio o sobra, dilo. Si se ve bien, confirmalo corto."
    ),
    EventType.HERO_DIED: (
        "El jugador acaba de morir. Da un consejo breve y concreto para no "
        "repetir el error: posicion, vision o timing."
    ),
    EventType.HERO_KILL: (
        "El jugador acaba de conseguir un kill. En la euforia es facil no "
        "ver lo importante: recuerdale revisar su vida y mana, si tiene "
        "consumibles para curarse, y que habilidades o items tiene listos "
        "para seguir o para escapar."
    ),
    EventType.LEVELED_UP: (
        "El jugador acaba de subir de nivel. Recuerdale gastar su punto de "
        "habilidad y sugiere cual subir segun su heroe y la fase."
    ),
    EventType.LOW_HEALTH: (
        "El jugador tiene vida critica. Avisale con urgencia en una sola "
        "frase muy corta que se retire o use curacion."
    ),
    EventType.LOW_MANA: (
        "El jugador tiene mana critico. Avisale corto que cuide su mana: "
        "que no quede sin recursos para sus habilidades clave, o que "
        "considere regenerar."
    ),
    EventType.HIGH_UNSPENT_GOLD: (
        "El jugador acumula oro sin gastar, lo cual es un error. Empujalo a "
        "ir a la tienda y gastar en su build o consumibles."
    ),
    EventType.SCOUTING_REMINDER: (
        "Recuerdale revisar el equipo enemigo: que items clave llevan y que "
        "heroes son la amenaza, para ajustar su juego."
    ),
}


def _skill_status(abilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate each player ability with its cap and whether it can be leveled.

    Normal abilities cap at 4, ultimates at 3. This is computed in code so the
    model does not have to reason about level limits (which it does poorly).
    """
    result: list[dict[str, Any]] = []
    for ability in abilities:
        level = ability.get("level", 0)
        cap = 3 if ability.get("ultimate") else 4
        result.append(
            {
                "name": ability.get("name"),
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

    def _build_prompt(self, event: Event, state: dict[str, Any]) -> str:
        """Compose the user prompt from the event and the current state."""
        instruction = _EVENT_INSTRUCTIONS.get(
            event.type, "Da un consejo breve y util al jugador."
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
        hero_json = json.dumps(hero_data, ensure_ascii=False) if hero_data else "{}"

        # The player's current abilities with level caps and what can be leveled,
        # computed in code so the model does not misjudge level limits.
        skills = _skill_status(state.get("abilities", []))
        skills_json = json.dumps(skills, ensure_ascii=False)

        # Manual context the player provides (role and draft), which GSI
        # cannot give us. Read fresh so mid-match edits take effect.
        context = load_context()
        context_json = json.dumps(context, ensure_ascii=False)

        return (
            f"{instruction}\n\n"
            f"Estado actual del jugador (JSON): {state_json}\n"
            f"Datos reales de tus items actuales (nombre, costo, efecto): "
            f"{item_json}\n"
            f"Habilidades, talentos y facetas reales de tu heroe: {hero_json}\n"
            f"Nivel actual de tus habilidades y cuales puedes subir "
            f"(can_level=true significa que aun no esta al maximo): "
            f"{skills_json}\n"
            f"Contexto de la partida que te dio el jugador (tu rol, aliados "
            f"y enemigos; GSI no da esto): {context_json}\n"
            f"Datos del evento: {extra}\n\n"
            f"El jugador YA tiene los items listados arriba; no se los "
            f"recomiendes de nuevo. Para habilidades y talentos usa SOLO los "
            f"nombres reales listados arriba, nunca inventes. Nombres en ingles."
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
        content = response["message"]["content"]
        return str(content).strip()