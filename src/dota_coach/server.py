"""Flask server that receives Game State Integration payloads from Dota 2."""

from datetime import datetime
from typing import Any

from flask import Flask, request

from dota_coach.analyzer import EventDetector
from dota_coach.config import Config
from dota_coach.serializer import serialize


def create_app(config: Config) -> Flask:
    """Build the Flask app. Using a factory keeps it testable."""
    app = Flask(__name__)
    detector = EventDetector()

    def is_authentic(payload: dict[str, Any]) -> bool:
        """Check that the POST comes from your Dota using the .cfg token."""
        auth = payload.get("auth", {})
        return bool(auth.get("token") == config.auth_token)

    @app.route("/", methods=["POST"])
    def receive_gsi() -> tuple[str, int]:
        payload: dict[str, Any] | None = request.get_json(force=True, silent=True)

        if payload is None:
            print("[!] Received a POST without valid JSON.")
            return "", 400

        if not is_authentic(payload):
            print("[!] Invalid token. POST ignored.")
            return "", 403

        timestamp = datetime.now().strftime("%H:%M:%S")
        game_map: dict[str, Any] = payload.get("map", {})
        state = game_map.get("game_state", "unknown")
        clock = game_map.get("clock_time")

        print(f"[{timestamp}] POST received | state: {state} | clock: {clock}")

        # Serialize the raw payload into the compact coach state and show it.
        coach_state = serialize(payload)
        game_clock = coach_state.get("clock") or 0
        events = detector.detect(coach_state, game_clock)

        for event in events:
            print(f"[{timestamp}] EVENT: {event.type.value} {event.data}")

        return "", 200

    @app.route("/", methods=["GET"])
    def alive() -> tuple[str, int]:
        return "Coach server running. Waiting for Dota 2 data (GSI).", 200

    return app