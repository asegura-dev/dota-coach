# Roadmap

The project is built in modular steps. Each step is completed and verified
before moving to the next.

## Scope and data reality

Game State Integration only exposes the **local player's** data during a live
match. It does not send allies' or enemies' heroes, items, or positions while
playing (that data is only available when spectating). GSI is also read-only:
it cannot control the game or read planned purchases.

The coach therefore focuses on the player's own game, enriched with context the
player provides manually (the draft, and optional enemy scouting). Spoken advice
is in Spanish, short and direct; everything in the repository is in English.

## Steps

1. **GSI ingestion + Flask server** - _Done._
   Configure Dota's GSI `.cfg` and stand up a Flask server that receives,
   validates, and logs the raw match payload.

2. **Serializer** - _Done._
   Trim the large Valve JSON into a compact dictionary: clock, the player's
   hero, items, abilities, economy, KDA, and a coarse map zone.

3. **State detection** - _Done._
   Event detector that compares successive states and emits events (match
   started, hero died, level up, low health, high unspent gold, periodic
   scouting reminder, starting-items check), each with its own cooldown. It
   reports what changed; it does not decide what to say. 

4. **Patch data extraction** - _In progress._
   Real item and hero-ability data (names, costs, effects, cooldowns, mana,
   talents, facets) loaded from dotaconstants and injected into the prompt.
   The data is in place; tuning remains so the model reliably uses real names
   and stops inventing items or misjudging which ability is the ultimate.

5. **Brain (Ollama)** - _Done._
   A background worker sends each detected event and the current state to a
   local Ollama model, which returns short Spanish advice. Runs on its own
   thread via a queue, so it never blocks the server or the game. The model is
   configurable via `.env`. Advice quality is limited until patch data (step 4)
   and player context (step 6) are added.

6. **Manual context input** - _Pending._
   Let the player dictate the draft and report enemy scouting, by voice or
   text. The architecture supports both input methods.

7. **Audio (TTS)** - _Pending._
   Speak the advice from a queue on a background thread, without affecting
   frame rate.

8. **Integration and tuning** - _Pending._
   Wire everything together, tune advice cooldowns and throttling, and refine
   the coaching rules in real matches.

## Notes and future ideas

- Map zone is approximate. Only `own_base` and central positions are well
  calibrated; lane-level detection would need verified per-patch zone data.
- Courier data: to verify whether GSI exposes it at all.
- "Gold needed for item X" and "suggested next purchase" depend on patch data
  (step 4) and the brain (step 5), not on the serializer.