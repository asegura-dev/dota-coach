"""A small CustomTkinter window to set the match context (role and draft).

Runs as a separate program from the coach. It writes context.json, which the
coach reads when building advice. This keeps the two decoupled: the GUI never
talks to the server, only to the file.
"""

import json
from pathlib import Path
from typing import Any

import customtkinter as ctk

from dota_coach.heroes_list import hero_name_map

_CONTEXT_PATH = Path(__file__).resolve().parents[2] / "context.json"
_ROLES = ["carry", "mid", "offlane", "support"]


def _load_existing() -> dict[str, Any]:
    """Load the current context.json if it exists, for pre-filling fields."""
    try:
        return dict(json.loads(_CONTEXT_PATH.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"role": "", "allies": [], "enemies": []}


class ContextApp(ctk.CTk):  # type: ignore[misc]
    """Window to pick role and draft, and save them to context.json."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Dota Coach — Contexto")
        self.geometry("420x640")

        self._heroes = hero_name_map()
        display_names = [""] + list(self._heroes.keys())
        existing = _load_existing()

        ctk.CTkLabel(self, text="Tu rol", anchor="w").pack(
            fill="x", padx=20, pady=(20, 4)
        )
        self._role = ctk.CTkComboBox(self, values=_ROLES)
        self._role.set(existing.get("role", "") or _ROLES[0])
        self._role.pack(fill="x", padx=20)

        # Enemies: 5 slots.
        ctk.CTkLabel(self, text="Enemigos", anchor="w").pack(
            fill="x", padx=20, pady=(16, 4)
        )
        self._enemy_boxes = self._make_hero_slots(display_names, 5)
        self._prefill(self._enemy_boxes, existing.get("enemies", []))

        # Allies: 4 slots (you are the fifth).
        ctk.CTkLabel(self, text="Aliados (sin contarte)", anchor="w").pack(
            fill="x", padx=20, pady=(16, 4)
        )
        self._ally_boxes = self._make_hero_slots(display_names, 4)
        self._prefill(self._ally_boxes, existing.get("allies", []))

        self._status = ctk.CTkLabel(self, text="")
        self._status.pack(pady=(12, 4))

        ctk.CTkButton(self, text="Guardar", command=self._save).pack(
            padx=20, pady=8, fill="x"
        )

    def _make_hero_slots(
        self, values: list[str], count: int
    ) -> list[ctk.CTkComboBox]:
        """Create `count` searchable hero comboboxes."""
        boxes: list[ctk.CTkComboBox] = []
        for _ in range(count):
            box = ctk.CTkComboBox(self, values=values)
            box.set("")
            box.pack(fill="x", padx=20, pady=3)
            boxes.append(box)
        return boxes

    def _prefill(
        self, boxes: list[ctk.CTkComboBox], internal_names: list[str]
    ) -> None:
        """Set existing internal names back to their display names in the boxes."""
        reverse = {v: k for k, v in self._heroes.items()}
        for box, internal in zip(boxes, internal_names, strict=False):
            box.set(reverse.get(internal, ""))

    def _collect(self, boxes: list[ctk.CTkComboBox]) -> list[str]:
        """Turn selected display names into internal names, skipping blanks."""
        result: list[str] = []
        for box in boxes:
            display = box.get().strip()
            internal = self._heroes.get(display)
            if internal:
                result.append(internal)
        return result

    def _save(self) -> None:
        """Write the current selections to context.json."""
        context = {
            "role": self._role.get().strip(),
            "allies": self._collect(self._ally_boxes),
            "enemies": self._collect(self._enemy_boxes),
        }
        _CONTEXT_PATH.write_text(
            json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._status.configure(text="Guardado ✓")


def main() -> None:
    ctk.set_appearance_mode("dark")
    app = ContextApp()
    app.mainloop()


if __name__ == "__main__":
    main()