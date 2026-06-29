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
  died, level up with unspent points, low health, high unspent gold, scouting
  reminder, starting-items check), each with its own cooldown.
- Pytest test suite covering the event detector.

### Changed

- Roadmap reworked to reflect that GSI only exposes the local player's data
  during a live match; the coach now focuses on the player's own game with
  manually provided draft and scouting context.