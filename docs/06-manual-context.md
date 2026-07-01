# Step 6: Manual Context

GSI only exposes the local player's data. It never sends the allies' or
enemies' heroes, nor the draft. This step lets the player supply that missing
context - their role and the draft - so the coach can tailor its advice.

## Why it matters

Without context, the coach can only comment on the player's own hero. It does
not know whether the player is a carry or a support, nor which heroes it is up
against, so its buying and scouting advice stays generic. Given the role and
the enemy draft, the coach adapts: a support and a carry get different advice,
and scouting can point at real threats.

## Architecture

The context is shared through a file, `context.json`, not through direct calls.
This keeps two programs fully decoupled:

- The **coach** reads `context.json` when building each prompt.
- A separate **GUI** writes `context.json` when the player saves.

Neither knows about the other; the file is the only contract. A future voice
input would simply be a third writer of the same file, with no change to the
coach. The file is read fresh on every advice call, so edits mid-match take
effect without restarting anything.

`context.json` holds the player's role, the enemy heroes, and the ally heroes
(hero names in internal form, e.g. `crystal_maiden`). It is not committed
(it changes every match); `context.example.json` is the public template.

## The context GUI

A small CustomTkinter window (`dota-context`) writes the file without editing
JSON by hand:

- A role dropdown (carry, mid, offlane, support).
- A search box that filters heroes as you type, so you never scroll a list of
  all heroes. Each result has two buttons to send it to the enemy or ally team.
- The chosen teams are shown in full, each hero removable with a button.
- Enemies cap at five, allies at four (the player is the fifth ally); duplicates
  are rejected.
- Save writes `context.json`.

The GUI shows heroes by their display name (e.g. "Nature's Prophet") but stores
the internal name (`furion`), using the hero list from dotaconstants.

## Reproducing this step

Launch the coach as usual, and in a separate window run:
```
uv run dota-context
```
Pick the role and draft, save, and the coach will use them on its next advice.