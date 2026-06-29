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

[Unreleased]: https://github.com/asegura-dev/dota-coach/commits/main