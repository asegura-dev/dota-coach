# Roadmap v2

Version 1 delivered a complete live coach: GSI ingestion, event detection,
patch data, an LLM brain, manual draft context, and English voice. Version 2
focuses on making the advice smarter and less repetitive, and on richer item
recommendations. Each step is built and verified before the next, as in v1.

## Steps

1. **Match memory** - _Pending._
   Remember recent advice so the coach stops repeating itself (e.g. suggesting
   the same skill or item every level). Foundation for smarter, non-repetitive
   coaching.

2. **Voice filtering** - _Pending._
   In fights, speak only urgent advice (low health, deaths) and print the rest.
   Drop stale advice from the queue so the coach never says a tip that no longer
   applies. Keeps the spoken output clean.

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

8. **More events** - _Pending._
   Detect towers falling, Roshan timing, day/night, and death streaks, widening
   coverage of key moments.

9. **Post-match summary** - _Pending._
   At the end, review the player's game: deaths from overextending, gold spent,
   ability usage. Turns the coach from reactive into formative.

10. **Adjustable personality** - _Pending._
    Let the player choose the coach's tone (harsh and critical, or calm and
    encouraging), via a simple prompt parameter.

## Maintenance (not a feature)

- Split `src/` into domain folders (data, detection, brain, infra, voice) now
  that the project has grown, done with `git mv` and a test run.

## Deferred to later or experiments

These are large or experimental; each is a project in itself, not a quick step.

- On-screen overlay (HUD) with advice and simple indicators.
- Real-time state view in the GUI (health, mana, cooldowns, items, gold).
- Plugin system for build, draft, vision, economy or combat analyzers.
- Draft coach: pick and ban suggestions, synergies, counterpicks.
- Streamer mode: shorter advice with humor and caster-style reactions.
- Voice input to dictate the draft (speech-to-text).
- Swappable model profiles to compare Qwen, Llama and others.
- Dynamic aggression based on the score (push when ahead, defend when behind).
- Model fine-tuned on replays or pro guides (research-scale effort).
- Multimodal reasoning with vision (positioning, spacing, fight review).