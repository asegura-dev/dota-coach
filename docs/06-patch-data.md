# Step 4: Patch Data

The coach must talk about real items and abilities, with their true names, so
it does not invent things that do not exist. This step loads real Dota 2 data
and makes it available to the brain when building advice.

## Why it matters

A language model left to its own memory will misname items, invent abilities,
or suggest builds that are not real. Feeding it the actual item and ability
data for the player's current hero anchors its advice in what truly exists in
the game, which sharply reduces hallucinated names.

## The data

Four JSON files live in `data/`, taken from the dotaconstants project (which
packages Valve's game data):

- `items.json` - item names, costs, and effects.
- `abilities.json` - per-ability details (name, description, cooldown, mana).
- `hero_abilities.json` - each hero's abilities, talents, and facets.
- `heroes.json` - the hero list with localized names and base stats.

Because they come from dotaconstants, the data tracks the live patch for items
and heroes, though patch notes themselves can lag behind.

## How it is loaded

Two small modules read the files and expose clean lookups, each cached so the
files are parsed only once:

- `items_data.py`: `lookup(name)` returns one item's display name, cost, and a
  trimmed effect; `lookup_many(names)` does the same for a list, skipping
  duplicates and unknown names.
- `heroes_data.py`: `lookup_hero(hero_name)` rebuilds the internal hero name and
  returns its abilities (name, effect, cooldown, mana), facets, and talents.

The brain calls these when building the prompt, so the model sees the player's
real items and their hero's real abilities instead of guessing.

## Design decisions

- **Cache on load.** Each file is read once and cached, since patch data does
  not change during a match.
- **Clean talent names.** Many talents carry unfilled placeholders like
  `{s:bonus_value}` in the data. These are stripped so the talent reads as
  plain text, accepting that the exact number is not shown.
- **Skip noise.** Unknown or duplicate item names are dropped rather than
  passed on as empty entries.
- **Names in, data out.** The modules take the clean names the serializer
  produces and return only the fields the coach needs, keeping the prompt small.

## Known limitation

The data reflects the patch for items and heroes, but is only as current as the
installed dotaconstants version. After a new patch, the data files should be
refreshed to pick up changes.