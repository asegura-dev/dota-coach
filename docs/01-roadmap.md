# Roadmap

The project is built in modular steps. Each step is completed and verified
before moving to the next.

## Steps

1. **GSI ingestion + Flask server** - _Done._
   Configure Dota's GSI `.cfg` and stand up a Flask server that receives,
   validates, and logs the raw match payload.

2. **Serializer** - _Pending._
   Trim the large Valve JSON into a compact dictionary: clock, your hero, and
   the items of all ten players, to save tokens downstream.

3. **State detection** - _Pending._
   Trigger analysis only on relevant changes: a greeting when a new match
   starts, and advice when something noteworthy is detected.

4. **Brain (Ollama)** - _Pending._
   Send the clean state to a local model. Patch knowledge (items, costs,
   builds) is provided in the prompt from a local file the user maintains.
   Business rules: warn about build anomalies, suggest abilities at the start.

5. **Audio (TTS)** - _Pending._
   Speak the advice from a queue on a background thread, without affecting
   frame rate.

6. **Integration and tuning** - _Pending._
   Wire everything together, tune advice cooldowns and throttling, and refine
   the coaching rules in real matches.

## Output and language

- Advice is delivered by voice only. There is no in-game overlay.
- The spoken advice is in Spanish, short (two sentences maximum), critical and
  direct. Everything else in the repository is in English.
