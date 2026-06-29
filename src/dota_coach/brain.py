"""The coaching brain: turns detected events into spoken advice via Ollama.

It builds an event-specific prompt, sends it to a local Ollama model along
with the current game state, and returns short, direct advice in Spanish.
"""

import json
from typing import Any

import ollama

from dota_coach.events import Event, EventType

# The coach's persona and hard rules, shared by every request.
_SYSTEM_PROMPT = (
    "Eres un coach de Dota 2 de rango Immortal. Hablas en español, eres "
    "directo y critico, sin rodeos. Tus consejos son para el jugador local "
    "mientras juega. Responde SIEMPRE en maximo 2 frases cortas. No saludes "
    "ni uses relleno salvo que se te pida. Ve al grano con lo accionable."
)

# Event-specific instructions. Each tells the model what to focus on.
_EVENT_INSTRUCTIONS: dict[EventType, str] = {
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
    EventType.LEVELED_UP: (
        "El jugador acaba de subir de nivel. Recuerdale gastar su punto de "
        "habilidad y sugiere cual subir segun su heroe y la fase."
    ),
    EventType.LOW_HEALTH: (
        "El jugador tiene vida critica. Avisale con urgencia en una sola "
        "frase muy corta que se retire o use curacion."
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
        return (
            f"{instruction}\n\n"
            f"Estado actual del jugador (JSON): {state_json}\n"
            f"Datos del evento: {extra}"
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
            )
        except Exception as error:
            print(f"[!] Ollama error: {error}")
            return ""
        content = response["message"]["content"]
        return str(content).strip()