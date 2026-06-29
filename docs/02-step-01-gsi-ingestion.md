# Step 1: GSI Ingestion

This step builds the data pipeline: Dota 2 sends the live match state, and a
Flask server receives, authenticates, and logs it.

## How it works

Dota 2 ships with Game State Integration (GSI). When a `.cfg` file is present in
its `gamestate_integration` folder, Dota sends the match state as JSON via HTTP
POST to the configured URL, roughly once per second.

The pipeline has two sides:

- **Dota side:** a `.cfg` file telling Dota where to send data, how often, and
  with which auth token.
- **Python side:** a Flask server that validates the token and reads the
  payload.

## Design decisions

- **Application factory.** `create_app(config)` builds the Flask app from an
  explicit configuration object instead of a global. This keeps the server
  testable with a fake config, without touching the real `.env`.
- **Fail loudly on missing config.** `Config.load()` raises if the auth token
  is absent, instead of assuming a default. A misconfigured run stops with a
  clear message.
- **Token authentication.** Every POST carries a shared token. The server
  rejects any payload whose token does not match, returning HTTP 403.
- **Non-blocking server.** Flask runs with `threaded=True` so rapid POSTs from
  Dota never queue up behind a slow request.

## Configuration

Two values live in a `.env` file (never committed) with `.env.example` as the
public template:

| Variable         | Purpose                                          |
| ---------------- | ------------------------------------------------ |
| `GSI_AUTH_TOKEN` | Shared secret; must match the Dota `.cfg` token. |
| `SERVER_HOST`    | Listen address (default `127.0.0.1`).            |
| `SERVER_PORT`    | Listen port (default `4000`).                    |

## Reproducing this step

1. Install dependencies:

```
   uv add flask python-dotenv
```

2. Create `.env` from the template and set `GSI_AUTH_TOKEN`.

3. Create the Dota GSI config at
   `<steam>/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/gamestate_integration_coach.cfg`.
   The `token` inside it must match `GSI_AUTH_TOKEN`. Set `allplayers` to `1` to
   receive data for all ten players.

4. Run the server:

```
   uv run dota-coach
```

5. Open `http://localhost:4000` in a browser. It should report that the server
   is running.

6. Restart Dota 2 (it reads GSI configs only at startup) and start a match.
   The server console should print incoming POSTs with the match state and an
   advancing clock.

## Known limitation

In a live match, Valve only sends full enemy item data for what your vision can
see. Complete enemy builds are available in replays and spectator mode. This
constrains the coaching logic and is addressed in later steps.