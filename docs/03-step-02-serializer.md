# Step 2: Serializer

This step trims the large raw GSI payload into a compact dictionary that is
cheap to send to a model and easy to reason about.

## Why it matters

The raw Valve payload is large and full of data the coach does not need (full
building lists, internal prefixes, empty inventory slots). The serializer keeps
only what matters and cleans it up, which saves tokens downstream and makes the
state readable.

## What it extracts

From the local player's data the serializer builds:

- Clock, game state, daytime, and team scores.
- Hero: name, level, alive, health and mana percent, scepter and shard,
  unspent ability points, and a coarse map zone.
- Economy: gold, GPM, XPM.
- KDA: kills, deaths, assists, last hits, denies.
- Items: a clean list, skipping empty slots, keeping charges and cooldowns
  only when relevant.
- Abilities: name, level, ultimate flag, and cooldown when active.

## Design decisions

- **Strip Valve prefixes.** Names like `npc_dota_hero_juggernaut`,
  `item_tango`, and `DOTA_GAMERULES_STATE_GAME_IN_PROGRESS` are reduced to
  `juggernaut`, `tango`, and `GAME_IN_PROGRESS`.
- **Ability prefix is dynamic.** Ability names carry the hero prefix
  (`juggernaut_blade_fury`). It is stripped using the hero's own name, so it
  works for any hero. Abilities without the prefix are kept as-is.
- **Skip empty placeholders.** Empty item slots and empty ability slots (such
  as Doom's `empty1`/`empty2`) are dropped.
- **Unspent ability points.** Computed as hero level minus the sum of ability
  levels, enabling skill-build advice.
- **Coarse, honest map zone.** Position is translated to `own_base`,
  `own_half`, `mid`, or `enemy_half`, based on the diagonal coordinate and the
  player's team. It does not claim lane-level precision, which would need
  verified per-patch zone data.
- **Defensive reads.** Every field is read with `.get()`, so early phases
  (hero selection, strategy time) with sparse data do not crash.

## Tests

The serializer is covered by a pytest suite using minimal embedded payloads,
verifying prefix stripping, empty-slot skipping, charges and cooldowns, the
ultimate flag, unspent ability points, the team-mirrored map zone, and graceful
handling of sparse early-phase payloads.