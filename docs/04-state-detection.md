# Step 3: State Detection

This step decides *when* the coach should react. Instead of analyzing every
payload (about one per second), it watches for meaningful changes and emits
discrete events.

## Why it matters

Sending every tick to a language model would be slow, expensive, and would make
the coach talk non-stop. The detector acts as a filter: it compares the current
state to the previous one and reports only what is worth reacting to. It decides
what changed, not what to say; the advice itself is the brain's job.

## Events

The detector emits these events, each with its own cooldown:

- **match_started** - first time the game reaches in-progress (the greeting).
- **starting_items_check** - once during pre-game, to review the opening build.
- **hero_died** - on the alive-to-dead transition.
- **hero_kill** - the player's kill count increased.
- **leveled_up** - hero level increased since the previous tick.
- **low_health** - health crosses below the threshold.
- **low_mana** - mana crosses below the threshold.
- **high_unspent_gold** - gold accumulates above the threshold.
- **scouting_reminder** - periodic reminder to check the enemy team.

## Design decisions

- **Stateful detector.** `EventDetector` keeps memory between ticks: the
  previous state, when each event last fired, and which threshold events are
  armed. It lives for the whole match, created once in the server.
- **Per-event cooldowns.** Each event type has its own cooldown, so an urgent
  alert is never blocked by an unrelated informational one.
- **Edge detection for thresholds.** Low health and low mana fire when crossing
  the threshold downward and re-arm on recovery, so they warn on each dangerous
  drop without nagging while the value stays low.
- **In-progress guard.** Hero events (level, health, gold) only fire during the
  live game, not in pre-game. The starting-items check is the deliberate
  exception, firing in pre-game.
- **Game clock, not wall clock.** Cooldowns use the in-game clock from the
  state, so they behave correctly even if the game is paused.

## Tunable thresholds

Low health and low mana at 20 percent, high unspent gold above 1000, scouting
reminder every three minutes. These are starting values and are expected to be
tuned.

## Tests

The detector is covered by a pytest suite that simulates sequences of states and
verifies each event fires (and does not fire) when expected, including the
edge-detection and cooldown behavior.