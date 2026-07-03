# Dota Coach

A real-time Dota 2 coach that gives spoken advice while you play. It reads the
game state through Game State Integration, detects key moments, reasons with a
local LLM, and speaks short, actionable tips out loud.

## How it works

Dota 2 sends game state to a local Flask server (GSI). The state is cleaned,
events are detected (leveling up, low health, kills, and so on), and a local
Ollama model turns each event into a short piece of advice, using real patch
data for items and abilities. Advice is printed and spoken with Piper. A small
GUI lets the player provide the draft and role, which GSI does not expose.

The coach reasons and replies in English, which keeps a local model stable and
accurate.

## Requirements

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) running locally, with a model pulled
  (e.g. `ollama pull qwen2.5:14b`)
- Dota 2 with a GSI config file installed

## Setup

1. Clone the repo and install dependencies:
```
uv sync
```
2. Copy `.env.example` to `.env` and set your GSI auth token.
3. Install the GSI config in Dota 2 (see `docs/`), using the same token.
4. Download the voice model:
```
uv run python -m piper.download_voices en_US-lessac-high
```   
   Then move the two files into a `voices/` folder.

## Usage

Run both the coach and the context GUI:
```
start.bat
```
Set your role and the draft in the GUI, save, then launch Dota 2. The coach
will speak advice as you play.

## Documentation

Full documentation is in `docs/`, written as a book (compiled to
`docs/mdbook.html`), covering each step of the design.

## License

MIT