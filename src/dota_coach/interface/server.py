"""Flask server that receives Game State Integration payloads from Dota 2."""

import logging
from typing import Any

from flask import Flask, request

from dota_coach import console
from dota_coach.config import Config
from dota_coach.detection.analyzer import EventDetector
from dota_coach.gamedata.serializer import serialize
from dota_coach.interface.worker import AdviceWorker
from dota_coach.mind.brain import Brain

# Silence Werkzeug's per-request logging; we print our own clean output.
logging.getLogger("werkzeug").setLevel(logging.ERROR)

def create_app(config: Config) -> Flask:
    """Build the Flask app. Using a factory keeps it testable."""
    app = Flask(__name__)
    detector = EventDetector()
    brain = Brain(config.ollama_model)
    worker = AdviceWorker(brain)
    worker.start()

    def is_authentic(payload: dict[str, Any]) -> bool:
        """Check that the POST comes from your Dota using the .cfg token."""
        auth = payload.get("auth", {})
        return bool(auth.get("token") == config.auth_token)

    @app.route("/", methods=["POST"])
    def receive_gsi() -> tuple[str, int]:
        payload: dict[str, Any] | None = request.get_json(force=True, silent=True)

        if payload is None:
            console.error("Received a POST without valid JSON.")
            return "", 400

        if not is_authentic(payload):
            console.error("Invalid token. POST ignored.")
            return "", 403

        # Serialize the raw payload, then detect noteworthy events.
        coach_state = serialize(payload)
        game_clock = coach_state.get("clock") or 0
        events = detector.detect(coach_state, game_clock)

        for event in events:
            data = f" {event.data}" if event.data else ""
            console.event(f"{event.type.value}{data}")
            worker.submit(event, coach_state)

        return "", 200

    @app.route("/", methods=["GET"])
    def alive() -> tuple[str, int]:
        return "Coach server running. Waiting for Dota 2 data (GSI).", 200

    return app