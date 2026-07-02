"""Text-to-speech for the coach, so advice is spoken, not just printed.

Uses the local Windows voice via pyttsx3 as a first, zero-setup engine (the
Mexican "Sabina" voice when available). Speech runs on its own thread with a
queue, so speaking never blocks the server or the game. The engine is a detail
behind `Speaker`, so it can later be swapped for a better one (e.g. Piper)
without touching the rest of the coach.
"""

import queue
import threading

import pyttsx3

# Prefer a Mexican Spanish voice; fall back to any Spanish, then the default.
_PREFERRED_HINTS = ("es-mx", "sabina", "spanish (mexico)")


def _pick_voice(engine: "pyttsx3.Engine") -> str | None:
    """Return the id of the best available Spanish voice, or None."""
    voices = engine.getProperty("voices")
    for voice in voices:
        haystack = f"{voice.id} {voice.name}".lower()
        if any(hint in haystack for hint in _PREFERRED_HINTS):
            return str(voice.id)
    # Fall back to any voice whose id mentions Spanish.
    for voice in voices:
        if "es-" in voice.id.lower() or "spanish" in voice.name.lower():
            return str(voice.id)
    return None


class Speaker:
    """Speaks text on a background thread, one line at a time."""

    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def say(self, text: str) -> None:
        """Queue text to be spoken. Returns immediately."""
        if text.strip():
            self._queue.put(text)

    def _run(self) -> None:
        """Consume the queue and speak each line.

        The engine is created inside the thread because pyttsx3 is not safe to
        share across threads. Each line is spoken to completion before the next.
        """
        engine = pyttsx3.init()
        voice_id = _pick_voice(engine)
        if voice_id:
            engine.setProperty("voice", voice_id)
        engine.setProperty("rate", 170)  # a touch faster than default

        while True:
            text = self._queue.get()
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception:
                # A speech failure should never crash the coach.
                pass