# Step 5: Brain

This step turns detected events into spoken advice using a local language model
through Ollama. It is the first step where the coach actually talks.

## Why it matters

Steps 1 to 3 decide *when* to react. The brain decides *what to say*. It takes
an event and the current state, asks a local model for advice, and returns a
short, direct message in Spanish.

## How it works

- **Local model via Ollama.** The brain calls a model running locally (default
  `llama3.1:8b`, configurable in `.env`). Running locally keeps it private and
  free, and the machine's GPU keeps responses fast.
- **Event-specific prompts.** A shared system prompt sets the coach persona
  (Immortal-level, Spanish, two sentences, direct). Each event type adds its own
  instruction, so a death, a level-up, or low health each get focused advice.
- **Background worker.** Calls to the model take seconds, so they run on a
  separate thread fed by a queue. The server enqueues an event and returns
  immediately, which protects the game's frame rate.

## Design decisions

- **Separation of duties.** The detector reports what changed; the brain decides
  what to say. They are independent modules.
- **Fail safe.** If the model call fails, the brain logs the error and returns
  an empty string instead of crashing the server.
- **Console first.** Advice is printed to the console for now. Speaking it aloud
  (text-to-speech) is a later step; swapping print for speech will be trivial.
- **Only real abilities.** The hero's ability list is filtered to those the
  player currently has in the live state, so item-granted abilities (Aghanim's
  Shard or Scepter) are never suggested for leveling until actually acquired.

## Current limitation

Without patch data (step 4) and player context such as role and draft (step 6),
the model reasons from its own training knowledge. It can give generic or even
invented item names. This is expected and improves once those steps are added.

## Tuning

The model is set in `.env` via `OLLAMA_MODEL`. A larger model gives better
advice but uses more VRAM, which competes with the game; the default balances
quality and performance.