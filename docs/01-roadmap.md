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

3. **State detection** - _Pending._
   Trigger analysis only on relevant changes: a greeting when a new match
   starts, and advice when something noteworthy is detected. Configurable
   scouting reminders to check the enemy team.

4. **Patch data extraction** - _Pending._
   Extract real item and ability data from the installed game files, so the
   model reasons with accurate costs and effects for the current patch.

5. **Brain (Ollama)** - _Pending._
   Send the clean state plus the player's context (role, hero, dictated draft)
   to a local model. The model reasons advice for the player's situation:
   build direction, ability order, gold needed for an item, next purchase.

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