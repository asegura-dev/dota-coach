"""Loads the manual match context (role and draft) the player provides.

GSI does not expose allies' or enemies' heroes, so the player supplies them
here. The coach reads this file when building advice, giving the model the
context it otherwise lacks.
"""

import json
from pathlib import Path
from typing import Any

_CONTEXT_PATH = Path(__file__).resolve().parents[3] / "context.json"


def load_context() -> dict[str, Any]:
    """Read the current match context, or return empty defaults if absent.

    Read fresh on every call so edits during a match take effect without
    restarting the coach.
    """
    try:
        raw = _CONTEXT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"role": "", "allies": [], "enemies": []}

    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        # A half-written file (being edited) should not crash the coach.
        return {"role": "", "allies": [], "enemies": []}

    return {
        "role": data.get("role", ""),
        "allies": data.get("allies", []),
        "enemies": data.get("enemies", []),
    }