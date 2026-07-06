"""A CustomTkinter window to set the match context (role and draft).

Runs as a separate program from the coach. It writes context.json, which the
coach reads when building advice. The two stay decoupled: the GUI only writes
the file, never talks to the server. A future voice input would be just another
writer of the same file.

A single search box filters heroes as you type; each result can be sent to the
enemy or ally team. Enemies cap at 5, allies at 4 (you are the fifth ally).
Teams are shown in full (no scroll); search results appear only while typing.
"""

import json
from pathlib import Path
from typing import Any

import customtkinter as ctk

from dota_coach.gamedata.heroes_list import hero_name_map

_CONTEXT_PATH = Path(__file__).resolve().parents[3] / "context.json"
_ROLES = ["carry", "mid", "offlane", "support"]
_MAX_ENEMIES = 5
_MAX_ALLIES = 4
_MAX_RESULTS = 5  # how many filtered heroes to show at once
# Voice-toggle events: internal name (matches EventType.value) -> label shown.
_VOICE_EVENTS = [
    ("low_health", "Low health"),
    ("low_mana", "Low mana"),
    ("hero_died", "You died"),
    ("hero_kill", "You killed"),
    ("leveled_up", "Leveled up"),
    ("high_unspent_gold", "Unspent gold"),
    ("scouting_reminder", "Scout the map"),
    ("match_started", "Match started"),
    ("strategy_time", "Strategy time"),
    ("starting_items_check", "Starting items"),
]


def _load_existing() -> dict[str, Any]:
    """Load the current context.json if present, for pre-filling the window."""
    try:
        return dict(json.loads(_CONTEXT_PATH.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"role": "", "allies": [], "enemies": []}


class ContextApp(ctk.CTk):  # type: ignore[misc]
    """Search heroes, assign them to a team, and save to context.json."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Dota Coach - Context")
        self.geometry("460x1200")

        self._heroes = hero_name_map()
        self._reverse = {v: k for k, v in self._heroes.items()}

        self._enemies: list[str] = []
        self._allies: list[str] = []

        existing = _load_existing()

        # --- Save button: anchored to the bottom first, always visible ---
        ctk.CTkButton(self, text="Save", command=self._save).pack(
            side="bottom", padx=20, pady=(6, 12), fill="x"
        )
        self._status = ctk.CTkLabel(self, text="")
        self._status.pack(side="bottom", pady=(4, 0))

        # --- Role: fixed on top ---------------------------------------
        ctk.CTkLabel(self, text="Your role", anchor="w").pack(
            side="top", fill="x", padx=20, pady=(20, 4)
        )
        self._role = ctk.CTkComboBox(self, values=_ROLES)
        self._role.set(existing.get("role", "") or _ROLES[0])
        self._role.pack(side="top", fill="x", padx=20)

        # --- Search box -----------------------------------------------
        ctk.CTkLabel(self, text="Search hero", anchor="w").pack(
            side="top", fill="x", padx=20, pady=(16, 4)
        )
        self._search = ctk.CTkEntry(self, placeholder_text="type: phantom...")
        self._search.pack(side="top", fill="x", padx=20)
        self._search.bind("<KeyRelease>", self._on_search)

        # Results: only takes space when there are matches (no reserved gap).
        self._results = ctk.CTkFrame(self, fg_color="transparent")
        self._results.pack(side="top", fill="x", padx=20, pady=6)

        # --- Teams: shown in full, no scroll --------------------------
        self._enemy_label = ctk.CTkLabel(self, text="", anchor="w")
        self._enemy_label.pack(side="top", fill="x", padx=20, pady=(6, 2))
        self._enemy_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._enemy_frame.pack(side="top", fill="x", padx=20)

        self._ally_label = ctk.CTkLabel(self, text="", anchor="w")
        self._ally_label.pack(side="top", fill="x", padx=20, pady=(10, 2))
        self._ally_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._ally_frame.pack(side="top", fill="x", padx=20)

        # Pre-fill teams from an existing context, then draw everything.
        for name in existing.get("allies", [])[:_MAX_ALLIES]:
            if name in self._reverse:
                self._allies.append(name)
        self._render_teams()

        # --- Voice toggles: which events are spoken -------------------
        ctk.CTkLabel(self, text="Spoken events", anchor="w").pack(
            side="top", fill="x", padx=20, pady=(14, 4)
        )
        voice_frame = ctk.CTkFrame(self, fg_color="transparent")
        voice_frame.pack(side="top", fill="x", padx=20)
        saved_voice = existing.get("voice", {})
        self._voice_vars: dict[str, Any] = {}
        for index, (name, label) in enumerate(_VOICE_EVENTS):
            var = ctk.BooleanVar(value=bool(saved_voice.get(name, True)))
            self._voice_vars[name] = var
            ctk.CTkCheckBox(voice_frame, text=label, variable=var).grid(
                row=index // 2, column=index % 2, sticky="w", padx=4, pady=3
            )


    # -- Search ---------------------------------------------------------
    def _on_search(self, _event: Any = None) -> None:
        """Filter heroes by the current query and show matching rows."""
        for child in self._results.winfo_children():
            child.destroy()
        query = self._search.get().strip().lower()
        if not query:
            return
        matches = [d for d in self._heroes if query in d.lower()][:_MAX_RESULTS]
        for display in matches:
            self._make_result_row(display)

    def _make_result_row(self, display: str) -> None:
        """One result: the hero name and two buttons to assign a team."""
        row = ctk.CTkFrame(self._results, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=display, anchor="w").pack(
            side="left", fill="x", expand=True
        )
        ctk.CTkButton(
            row, text="-> Enemy", width=90,
            command=lambda d=display: self._add(d, "enemy"),
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            row, text="-> Ally", width=90,
            command=lambda d=display: self._add(d, "ally"),
        ).pack(side="left", padx=2)

    # -- Team management ------------------------------------------------
    def _add(self, display: str, team: str) -> None:
        """Add a hero to a team, respecting caps and duplicates."""
        internal = self._heroes.get(display)
        if internal is None:
            return
        if internal in self._enemies or internal in self._allies:
            self._status.configure(text=f"{display} is already on a team")
            return
        if team == "enemy":
            if len(self._enemies) >= _MAX_ENEMIES:
                self._status.configure(text="You already have 5 enemies")
                return
            self._enemies.append(internal)
        else:
            if len(self._allies) >= _MAX_ALLIES:
                self._status.configure(text="You already have 4 allies")
                return
            self._allies.append(internal)
        self._status.configure(text="")
        self._render_teams()

    def _remove(self, internal: str, team: str) -> None:
        """Remove a hero from a team."""
        target = self._enemies if team == "enemy" else self._allies
        if internal in target:
            target.remove(internal)
        self._render_teams()

    def _render_teams(self) -> None:
        """Redraw team chip rows and their counters."""
        self._enemy_label.configure(
            text=f"Enemies ({len(self._enemies)}/{_MAX_ENEMIES})"
        )
        self._ally_label.configure(
            text=f"Allies ({len(self._allies)}/{_MAX_ALLIES})"
        )
        self._render_chips(self._enemy_frame, self._enemies, "enemy")
        self._render_chips(self._ally_frame, self._allies, "ally")

    def _render_chips(
        self, frame: ctk.CTkFrame, names: list[str], team: str
    ) -> None:
        """Draw one removable chip per chosen hero."""
        for child in frame.winfo_children():
            child.destroy()
        for internal in names:
            display = self._reverse.get(internal, internal)
            chip = ctk.CTkFrame(frame)
            chip.pack(fill="x", pady=2)
            ctk.CTkLabel(chip, text=display, anchor="w").pack(
                side="left", fill="x", expand=True, padx=6
            )
            ctk.CTkButton(
                chip, text="x", width=28,
                command=lambda n=internal: self._remove(n, team),
            ).pack(side="right", padx=4)

    # -- Save -----------------------------------------------------------
    def _save(self) -> None:
        """Write the current role and teams to context.json."""
        context = {
            "role": self._role.get().strip(),
            "allies": self._allies,
            "enemies": self._enemies,
            "voice": {
                name: var.get() for name, var in self._voice_vars.items()
            },
        }
        _CONTEXT_PATH.write_text(
            json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._status.configure(text="Saved")


def main() -> None:
    ctk.set_appearance_mode("dark")
    app = ContextApp()
    app.mainloop()


if __name__ == "__main__":
    main()
