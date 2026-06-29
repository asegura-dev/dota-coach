# Introduction

Dota Coach is a real-time coaching assistant for Dota 2. It analyzes the live match and delivers short, strategic voice advice while you play, without affecting your frame rate.

The system reads the match state through Valve's Game State Integration (GSI),
filters it down to what matters, sends it to a local language model for
analysis, and speaks the resulting advice out loud.

## Architecture

The application runs locally as a single process with three threads
communicating through queues:

1. **Capture (GSI):** Dota 2 sends a continuous JSON stream via HTTP POST.
2. **Ingestion (Flask):** A server receives and validates each payload.
3. **Serializer:** Trims the large Valve JSON into a compact dictionary.
4. **Brain (Ollama):** A local model analyzes the state and generates advice.
5. **Audio (TTS):** Advice is spoken from a queue on a background thread.

The Flask server answers Dota in milliseconds and never blocks; the heavy work
(analysis and speech) happens on background threads fed by queues.

## Design principles

- Strict type hints everywhere, checked with mypy.
- Fail loudly: missing configuration stops the program with a clear message
  instead of guessing a default.
- Keep it simple: no premature abstractions or unnecessary dependencies.