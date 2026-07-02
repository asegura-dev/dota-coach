# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffold with uv packaging, targeting Python 3.12.
- Ruff (lint and format) and mypy (strict) as development tooling.
- GSI ingestion server (Flask) with token authentication.
- Configuration loader that reads and validates the `.env` file.
- Entry point exposed as the `dota-coach` command.
- Dota 2 GSI `.cfg` to stream the live match state to the server.
- Project documentation (introduction, roadmap, this changelog).
- Serializer that trims the raw GSI payload into a compact coach state
  (clock, hero, items, abilities, economy, KDA, coarse map zone).
- Pytest test suite covering the serializer.
- Event detector that emits events on state changes (match started, hero
  died, level up, low health, high unspent gold, scouting reminder,
  starting-items check), each with its own cooldown.
- Pytest test suite covering the event detector.
- Coaching brain that turns events into short Spanish advice via a local
  Ollama model, configurable through `.env`.
- Background advice worker (queue + thread) so model calls never block the
  server or affect game performance.
- Colored console output (rich): events in yellow, advice in green, errors in
  red, a discreet heartbeat, and quiet Flask request logs.
- Real item data (dotaconstants) injected into the prompt so advice uses true
  item names, costs and effects.
- Real hero ability data (abilities, talents, facets) injected into the prompt
  so advice uses true ability names instead of guessing.
- Low-mana event with the same edge-detection logic as low health.
- Hero-kill event (kill count increase) that reminds the player to check
  health, mana, consumables and ready cooldowns after a kill.
- Manual match context: the coach reads role and draft from `context.json`.
- Context GUI (`dota-context`) with hero search to write the context file.
- Strategy-time event so the coach wakes up when the draft closes.
- Batch script (`start.bat`) that launches the coach and context GUI together.
- Spoken advice via Piper text-to-speech with a Mexican Spanish voice.
- The coach now thinks and replies in English, which removed the language
  drift to Chinese and improved instruction-following on the local model.
- Switched the voice to an English Piper voice (en_US-lessac-high).

### Fixed

- Level-up advice no longer suggests item-granted abilities (Aghanim's Shard or
  Scepter) the player does not own, by filtering hero abilities to those present
  in the live state.

### Changed

- Roadmap reworked to reflect that GSI only exposes the local player's data
  during a live match; the coach now focuses on the player's own game with
  manually provided draft and scouting context.
- The coach now replies in neutral Mexican Spanish, avoiding Iberian idioms.