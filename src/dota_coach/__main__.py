"""Entry point: python -m dota_coach (or the dota-coach command)."""

from dota_coach.config import Config
from dota_coach.server import create_app


def main() -> None:
    config = Config.load()
    app = create_app(config)
    print(f"Coach server listening on http://{config.host}:{config.port}")
    # threaded=True so the server does not block on rapid POSTs from Dota.
    app.run(host=config.host, port=config.port, threaded=True)


if __name__ == "__main__":
    main()