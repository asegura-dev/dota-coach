"""Background worker that turns events into advice without blocking the server.

The server enqueues (event, state) pairs and returns immediately. This worker
consumes them on its own thread, calls the brain (which talks to Ollama), and
prints the advice. Keeping it off the request thread protects the game's FPS.
"""

import queue
import threading
from typing import Any

from dota_coach import console
from dota_coach.brain import Brain
from dota_coach.events import Event


class AdviceWorker:
    """Consumes events from a queue and produces advice on a background thread."""

    def __init__(self, brain: Brain) -> None:
        self._brain = brain
        self._queue: queue.Queue[tuple[Event, dict[str, Any]]] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        """Start the background thread."""
        self._thread.start()

    def submit(self, event: Event, state: dict[str, Any]) -> None:
        """Enqueue an event for processing. Returns immediately."""
        self._queue.put((event, state))

    def _run(self) -> None:
        """Process events from the queue forever."""
        while True:
            event, state = self._queue.get()
            advice = self._brain.advise(event, state)
            if advice:
                console.advice(event.type.value, advice)
            self._queue.task_done()