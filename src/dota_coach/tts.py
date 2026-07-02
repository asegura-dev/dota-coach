"""Text-to-speech for the coach, so advice is spoken, not just printed.

Uses Piper, a local neural TTS, with a Mexican Spanish voice (es_MX). Speech
runs on its own thread with a queue, so speaking never blocks the server or the
game. The engine sits behind `Speaker`, so it can be swapped without touching
the rest of the coach.
"""

import queue
import threading
from pathlib import Path

import sounddevice as sd
from piper import PiperVoice, SynthesisConfig

_VOICE_PATH = Path(__file__).resolve().parents[2] / "voices" / "en_US-lessac-high.onnx"


class Speaker:
    """Speaks text on a background thread, one line at a time, using Piper."""

    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def say(self, text: str) -> None:
        """Queue text to be spoken. Returns immediately."""
        if text.strip():
            self._queue.put(text)

    def _run(self) -> None:
        """Load the voice once, then speak each queued line to completion."""
        try:
            voice = PiperVoice.load(str(_VOICE_PATH))
        except Exception:
            # If the voice can't load, the coach still runs (just silent).
            return

        while True:
            text = self._queue.get()
            try:
                self._speak(voice, text)
            except Exception:
                # A speech failure should never crash the coach.
                pass

    def _speak(self, voice: "PiperVoice", text: str) -> None:
        """Synthesize one line with Piper and play it as a single, smooth clip."""
        import numpy as np

        parts = []
        sample_rate = 22050
        syn_config = SynthesisConfig(length_scale=0.85)
        for chunk in voice.synthesize(text, syn_config=syn_config):
            parts.append(chunk.audio_float_array)
            sample_rate = chunk.sample_rate
        if parts:
            audio = np.concatenate(parts)
            sd.play(audio, samplerate=sample_rate)
            sd.wait()