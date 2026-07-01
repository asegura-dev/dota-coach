# Data

Static Dota 2 data used by the coach to reason with real item and ability
information instead of inventing it.

## Files

- `items.json` — item names, costs, and effects.
- `hero_abilities.json` — each hero's abilities, talents, and facets.
- `abilities.json` — per-ability details (name, description, cooldown, mana).
- `heroes.json` — hero list with localized names and base stats.

## Source and attribution

These files come from the [dotaconstants](https://github.com/odota/dotaconstants)
project by OpenDota, which extracts them from the Dota 2 game files. The
underlying game data is © Valve Corporation. They are included here for
convenience so the project works offline.

To refresh them after a Dota 2 patch, re-download the files from the
dotaconstants `build/` directory.