"""Entry point: python -m dota_coach (or the dota-coach command)."""

import threading
import time

from dota_coach import console
from dota_coach.config import Config
from dota_coach.server import create_app

_HEARTBEAT_SECONDS = 60.0


def _heartbeat() -> None:
    """Print a discreet line periodically so it's clear the coach is alive."""
    while True:
        time.sleep(_HEARTBEAT_SECONDS)
        console.info("● coach activo, esperando eventos...")


def main() -> None:
    config = Config.load()
    app = create_app(config)

    console.info(f"Coach escuchando en http://{config.host}:{config.port}")
    console.info(f"Modelo: {config.ollama_model} · Ctrl+C para salir")

    heartbeat = threading.Thread(target=_heartbeat, daemon=True)
    heartbeat.start()

    # threaded=True so the server does not block on rapid POSTs from Dota.
    app.run(host=config.host, port=config.port, threaded=True)


if __name__ == "__main__":
    main()