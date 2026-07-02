# Step 7: Voice

The coach speaks its advice out loud, so the player can hear it without looking
away from the game.

## Why it matters

Reading advice in a console pulls the player's eyes off the screen. Spoken
advice reaches them while they keep playing, which is the point of a live coach.

## How it works

Text-to-speech runs behind a small `Speaker` class in `tts.py`. It keeps its
own queue and background thread, so speaking never blocks the server or the
game. When the advice worker produces a line, it prints it and also hands it to
the speaker, which says it aloud. Lines are spoken one after another, so several
events in a fight do not overlap.

The engine is Piper, a local neural text-to-speech system. It runs offline (no
internet, no cost) and uses a Mexican Spanish voice, so the advice sounds
natural and native. The engine sits behind `Speaker`, so it can be swapped
without touching the rest of the coach; an earlier version used the built-in
Windows voice.

## The voice model

Piper needs a voice model (two files, `.onnx` and `.onnx.json`). These are not
committed to the repository, since they are large and downloadable. They live
in a `voices/` folder, which is git-ignored. To fetch the Mexican voice:
```
uv run python -m piper.download_voices es_MX-ald-medium
```
Then move the two downloaded files into `voices/`. Speech rate is tuned with
`length_scale` in `tts.py` (lower is faster).

## Design decisions

- **Off the game's thread.** Speech runs on its own queue and thread, like the
  advice worker, so audio never affects frame rate.
- **Local and free.** Piper runs on the machine with no internet or cost, in
  keeping with the rest of the coach (Ollama is local too).
- **Engine behind an interface.** Swapping the TTS engine touches only `tts.py`.