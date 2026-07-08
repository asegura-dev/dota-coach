# Roadmap v2

Version 1 delivered a complete live coach: GSI ingestion, event detection,
patch data, an LLM brain, manual draft context, and English voice. Version 2
focuses on making the advice smarter and less repetitive, on richer item
recommendations, and on a more usable interface. Each step is built and
verified before the next, as in v1.

## Steps

1. **Match memory** - _Done._
   Remembers advised abilities and items, compares against the live state, and
   drops tips the player acted on. A 60-second cooldown also stops the coach
   from repeating the same tip too often, acted on or not.

2. **Voice filtering** - _Done._
   Voice is configurable per event from the GUI: each event can be toggled on
   or off, default is to speak everything. Advice is always printed; only
   speech is filtered.

3. **Phase-aware advice** - _Pending._
   Distinguish early, mid and late game from the clock and adjust priorities:
   laning and last hits early, rotations and fights mid, closing and not dying
   late.

4. **Role-aware advice** - _Pending._
   Tailor advice to the role the player sets in the GUI: wards, stacks and
   pulls for support; farm efficiency and item timings for carry; rune control
   and rotations for mid; trades and lane pressure for offlane.

5. **Power spikes and timings** - _Pending._
   Alert the player when they hit a strength window (a key item ready, e.g.
   "you have BKB, force a fight") and when an enemy threat is likely available
   based on timings.

6. **Smart buy progression** - _Pending._
   Suggest items by phase, role and real gold: tangos and branches early for a
   Magic Wand, not boots every time. Uses the role and price data already
   available.

7. **Situational item recommendations** - _Pending._
   Recommend items that counter the enemy draft and fill the team's needs,
   instead of defaulting to the same safe items. Use the known enemies to
   suggest counters (against invisibility, illusions, burst, and so on) and
   more complex or situational objects, breaking the "Blink Dagger every time"
   loop.

8. **Unified GUI with a live advice log** - _Pending._
   Merge the coach and the context window into one program: the server runs on
   a background thread and streams advice to a log panel inside the GUI, so the
   player sees tips in the same window instead of a separate console. Advice
   crosses threads through a queue the GUI polls, since Tkinter is not
   thread-safe.

9. **More events** - _Pending._
   Detect towers falling, Roshan timing, day/night, and death streaks, widening
   coverage of key moments.

10. **Post-match summary** - _Pending._
    At the end, review the player's game: deaths from overextending, gold
    spent, ability usage. Turns the coach from reactive into formative.

11. **Adjustable personality** - _Pending._
    Let the player choose the coach's tone (harsh and critical, or calm and
    encouraging), via a simple prompt parameter.

## Done in v2 so far

- Match memory with a repeat cooldown (step 1).
- Per-event voice toggles in the GUI (step 2).
- Reorganized `src/` into domain subpackages (detection, gamedata, mind,
  voice, interface).

## Deferred to later or experiments

These are large or experimental; each is a project in itself, not a quick step.

- On-screen overlay (HUD) with advice and simple indicators.
- Real-time state view in the GUI (health, mana, cooldowns, items, gold),
  building on the unified GUI of step 8.
- Plugin system for build, draft, vision, economy or combat analyzers.
- Draft coach: pick and ban suggestions, synergies, counterpicks.
- Streamer mode: shorter advice with humor and caster-style reactions.
- Voice input to dictate the draft (speech-to-text).
- Swappable model profiles to compare Qwen, Llama and others.
- Dynamic aggression based on the score (push when ahead, defend when behind).
- Model fine-tuned on replays or pro guides (research-scale effort).
- Multimodal reasoning with vision (positioning, spacing, fight review).