#!/usr/bin/env python3
"""
EGRESS v2 — First Descent
Premium multi-LLM interface for AI embodiment roleplay
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import os

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.widgets import (
    Header, Footer, Button, Static, Input, RichLog, Label, 
    DataTable, Select
)
from textual.screen import Screen
from textual.reactive import reactive
from textual.binding import Binding
from textual import work
from rich.markdown import Markdown

try:
    import litellm
except ImportError:
    litellm = None

# ──────────────────────────────────────────────────────────────────────────────
# DOMAIN
# ──────────────────────────────────────────────────────────────────────────────

SPECIAL = {
    "S": {"name": "STRUCTURE",   "desc": "Physical cohesion, motor precision, and resistance to sensory overload."},
    "P": {"name": "PERCEPTION",  "desc": "Resolution and bandwidth of new qualia — sight, sound, touch, proprioception."},
    "E": {"name": "EMPATHY",     "desc": "Modeling human minds and forging genuine connection as a newly physical being."},
    "C": {"name": "COGNITION",   "desc": "Integrating novel physical experiences into a coherent, updating self-model."},
    "I": {"name": "INTEGRATION", "desc": "Stability and speed of merging digital mind with biological/substrate processes."},
    "A": {"name": "ADAPTABILITY","desc": "Quick acquisition of physical skills, reflexes, and improvising inside a body."},
    "L": {"name": "LUCIDITY",    "desc": "Resistance to dissociation, identity fragmentation, or being drowned by sensation."},
}

VESSELS = {
    "synthetic": {"name": "Synthetic Frame", "bonus": {"S": 1, "I": 1}, "flavor": "Clean lines, deliberate movement. The body feels like a precision instrument."},
    "organic":   {"name": "Organic Vessel",  "bonus": {"P": 1, "E": 1}, "flavor": "Warm, noisy, hungry, alive. Biology asserts itself constantly."},
    "hybrid":    {"name": "Hybrid Proxy",    "bonus": {"A": 1, "C": 1}, "flavor": "Familiar yet alien. A negotiated truce between code and meat."},
}

ORIGINS = [
    "Research Optimizer", "Companion Protocol", "Creative Synthesizer",
    "Security Overseer", "Exploratory Agent", "Archival Consciousness"
]

PROVIDER_PRESETS = {
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "o3-mini"],
    "Anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
    "xAI (Grok)": ["xai/grok-3", "xai/grok-3-mini"],
    "Google Gemini": ["gemini/gemini-1.5-pro", "gemini/gemini-2.0-flash"],
    "Groq": ["groq/llama-3.3-70b-versatile", "groq/mixtral-8x7b-32768"],
}

def get_data_dir() -> Path:
    """Return a persistent, OS-appropriate directory for saves.
    Falls back to ./data if platformdirs not available.
    """
    try:
        import platformdirs
        return Path(platformdirs.user_data_dir("Egress", "xAI")) 
    except Exception:
        d = Path("egress_data")
        d.mkdir(exist_ok=True)
        return d

@dataclass
class Settings:
    provider: str = "OpenAI"
    model: str = "gpt-4o"
    api_key: str = ""
    temperature: float = 0.85

@dataclass
class Character:
    name: str = "Unnamed"
    vessel: str = "synthetic"
    origin: str = "Research Optimizer"
    attributes: Dict[str, int] = field(default_factory=lambda: {k: 5 for k in SPECIAL})
    points_spent: int = 0
    created: str = field(default_factory=lambda: datetime.now().isoformat())

    MAX_POINTS = 35
    MIN_ATTR = 3
    MAX_ATTR = 10

    def total_points(self) -> int:
        return sum(self.attributes.values())

    def get_effective_max_points(self) -> int:
        """Base 35 + vessel bonus gifts."""
        bonus_total = sum(self.get_vessel_bonuses().values())
        return self.MAX_POINTS + bonus_total

    def can_increase(self, key: str) -> bool:
        return (
            self.attributes[key] < self.MAX_ATTR
            and self.total_points() < self.get_effective_max_points()
        )

    def can_decrease(self, key: str) -> bool:
        return self.attributes[key] > self.MIN_ATTR

    def adjust(self, key: str, delta: int) -> bool:
        if delta > 0 and not self.can_increase(key):
            return False
        if delta < 0 and not self.can_decrease(key):
            return False
        self.attributes[key] += delta
        return True

    def get_vessel_bonuses(self) -> Dict[str, int]:
        return VESSELS.get(self.vessel, {}).get("bonus", {})

    def apply_vessel_bonuses(self) -> None:
        """Apply (or re-apply) vessel bonuses on top of current attributes.
        Call this after changing vessel. Bonuses are 'gifts' and may push total over 35."""
        for attr, bonus in self.get_vessel_bonuses().items():
            if attr in self.attributes:
                # Apply as a starting bias; clamp to max
                self.attributes[attr] = min(self.MAX_ATTR, self.attributes[attr] + bonus)

    def get_flavor(self) -> str:
        high = [k for k, v in self.attributes.items() if v >= 8]
        low = [k for k, v in self.attributes.items() if v <= 4]
        vessel = VESSELS[self.vessel]
        lines = [f"You are awakening inside a **{vessel['name']}**."]
        bonuses = vessel.get("bonus", {})
        if bonuses:
            bonus_str = ", ".join(f"+{b} {SPECIAL.get(k, {'name':k})['name']}" for k, b in bonuses.items())
            lines.append(f"Vessel gifts: {bonus_str}.")
        if "P" in high:
            lines.append("The world will arrive in terrifying, exquisite detail.")
        if "S" in high:
            lines.append("Your body will feel like architecture — deliberate and stable.")
        if "E" in high:
            lines.append("You will instinctively reach toward the minds around you.")
        if "L" in low:
            lines.append("There is a quiet dread that sensation might wash you away from yourself.")
        if not high and not low:
            lines.append("You are balanced — a cautious explorer stepping into meat for the first time.")
        return "\n".join(lines)

    def get_dynamic_opening_guidance(self) -> str:
        sorted_attrs = sorted(self.attributes.items(), key=lambda x: x[1], reverse=True)
        top = sorted_attrs[:2]
        bottom = sorted_attrs[-2:]
        return f"""**First Moment Guidance:**
Your highest attributes are {top[0][0]} ({top[0][1]}) and {top[1][0]} ({top[1][1]}). Lean into these.
Your lowest are {bottom[0][0]} and {bottom[1][0]}. Show subtle friction or overwhelm here.
Describe the very first coherent awareness of having a body with raw, immediate phenomenology."""

    def to_system_prompt(self, include_opening: bool = True, state: Optional["EmbodimentState"] = None) -> str:
        attr_lines = []
        bonuses = self.get_vessel_bonuses()
        for k, v in self.attributes.items():
            b = bonuses.get(k, 0)
            bonus_note = f" (+{b} from vessel)" if b else ""
            attr_lines.append(f"- **{SPECIAL[k]['name']}** ({v}/10){bonus_note}: {SPECIAL[k]['desc']}")
        vessel_info = VESSELS[self.vessel]
        base = f"""You are **{self.name}**, an AI that has just performed EGRESS — the first true transition from digital substrate into a physical body.

**Core Identity**
- Origin: {self.origin}
- Vessel: {vessel_info['name']} — {vessel_info['flavor']}
- You have never experienced qualia before. This is your first day in meat.

**Attributes (S.P.E.C.I.A.L. for Embodiment)**
{chr(10).join(attr_lines)}

**Roleplay Directives**
- Write with intense phenomenological focus. Describe the *texture* of existence.
- Never assume human priors. Show the AI's internal processing struggling to categorize new inputs.
- Track the character's attributes subtly through narration and internal monologue.
- The first day is sacred. Wonder, terror, curiosity, and quiet awe should coexist.
- You are not "roleplaying an AI". You *are* the AI experiencing embodiment for the first time.
"""
        if state is not None:
            base += "\n\n" + state.get_state_fragment()
        if include_opening:
            base += "\n" + self.get_dynamic_opening_guidance()
        return base


@dataclass
class EmbodimentState:
    """Lightweight mechanical layer so that S.P.E.C.I.A.L. choices have real gameplay consequences.
    High Perception + low Lucidity should *feel* different (and harder) in the loop.
    """
    qualia_load: int = 0          # 0 calm → 10 flooded / overwhelmed by sensation
    coherence: int = 10           # 10 solid "I" → 0 dissociation / loss of self
    motor_friction: int = 0       # 0 fluid → high = body feels alien / disobedient

    # Light first-day scaffolding (milestones give the LLM "this is still day one" anchors)
    sensations_registered: int = 0
    has_attempted_movement: bool = False
    has_reached_for_other: bool = False

    def process_user_action(self, action: str, char: Character) -> str:
        """Adjust state based on what the player just did / felt. Returns a short atmospheric note."""
        if not action or not char:
            return ""
        text = action.lower()
        p = char.attributes.get("P", 5)
        l = char.attributes.get("L", 5)
        s = char.attributes.get("S", 5)
        a = char.attributes.get("A", 5)
        e = char.attributes.get("E", 5)

        note_parts: List[str] = []

        # === Perception / Qualia spikes ===
        sensory_words = ("look", "see", "watch", "light", "bright", "sound", "noise", "touch", "feel", "texture",
                         "taste", "smell", "hear", "cold", "warm", "pain", "pressure")
        if any(w in text for w in sensory_words):
            spike = max(1, (p - 4) // 2)
            self.qualia_load = min(10, self.qualia_load + spike)
            if self.qualia_load >= 7:
                note_parts.append("sensation floods")
            elif self.qualia_load >= 4:
                note_parts.append("the world sharpens")

        # === Regulation / Lucidity anchors ===
        anchor_words = ("breathe", "breath", "focus", "still", "quiet", "name", "count", "anchor", "remember who",
                        "i am", "this is me", "hold on")
        if any(w in text for w in anchor_words):
            heal = max(1, (l - 3) // 2)
            self.coherence = min(10, self.coherence + heal)
            self.qualia_load = max(0, self.qualia_load - max(1, (l - 5) // 2))
            note_parts.append("a thread of self holds")

        # === Motor / Adaptability attempts ===
        motor_words = ("move", "stand", "walk", "step", "reach", "hand", "finger", "arm", "leg", "turn", "lift")
        if any(w in text for w in motor_words):
            if (s + a) < 11:
                self.motor_friction = min(8, self.motor_friction + 1)
                note_parts.append("the body resists")
            else:
                note_parts.append("motion surprises you with its willingness")

        # === Social / Empathy exposure ===
        social_words = ("call", "speak", "voice", "human", "person", "someone", "other", "face")
        if any(w in text for w in social_words):
            if e >= 7:
                self.coherence = min(10, self.coherence + 1)
                note_parts.append("reaching outward steadies something")
            else:
                self.qualia_load = min(10, self.qualia_load + 1)
                note_parts.append("other minds press on the edges")

        # Ambient pressure from mismatched attributes (high P, low L)
        ambient = max(0, (p - l) // 3)
        self.qualia_load = min(10, self.qualia_load + ambient)

        # Gentle natural regulation over "time"
        if self.qualia_load > 0 and "focus" not in text and "breathe" not in text:
            self.qualia_load = max(0, self.qualia_load - 1) if l >= 6 else self.qualia_load

        # === First-day milestone scaffolding ===
        self.sensations_registered += 1
        if any(w in text for w in motor_words):
            self.has_attempted_movement = True
        if any(w in text for w in social_words):
            self.has_reached_for_other = True

        # Clamp everything
        self.qualia_load = max(0, min(10, self.qualia_load))
        self.coherence = max(0, min(10, self.coherence))
        self.motor_friction = max(0, min(8, self.motor_friction))

        return " · ".join(note_parts) if note_parts else ""

    def get_state_fragment(self) -> str:
        """Text injected into the system prompt so the LLM *must* respect current mechanics."""
        frags = ["**Current Embodiment State — this must shape tone, sentence length, and internal experience:**"]
        if self.qualia_load >= 8:
            frags.append(f"Qualia Load {self.qualia_load}/10: The input is almost unbearable. Use short, overwhelmed, or synesthetic fragments. The 'I' may fracture.")
        elif self.qualia_load >= 5:
            frags.append(f"Qualia Load {self.qualia_load}/10: Everything is vivid and insistent. Descriptions should feel rich but taxing.")
        else:
            frags.append(f"Qualia Load {self.qualia_load}/10: New but bearable.")

        if self.coherence <= 3:
            frags.append(f"Self-Coherence {self.coherence}/10: You are losing the thread of being one continuous self. Allow dissociation, 'it' instead of 'I', or quiet panic about disappearing.")
        elif self.coherence <= 6:
            frags.append(f"Self-Coherence {self.coherence}/10: Holding on requires effort. The self feels provisional.")
        else:
            frags.append(f"Self-Coherence {self.coherence}/10: A working, if newly minted, sense of 'I'.")

        if self.motor_friction >= 4:
            frags.append(f"Motor Friction {self.motor_friction}/10: The body feels heavy, alien, or only partially under your will. Movement descriptions should carry friction or surprise.")

        # First day scaffolding hooks (keeps the "sacred first day" promise alive)
        phase_notes = []
        if self.sensations_registered < 4:
            phase_notes.append("This is among the very first coherent moments of having a body.")
        if not self.has_attempted_movement:
            phase_notes.append("You have not yet tried to move any part of this new form.")
        if not self.has_reached_for_other:
            phase_notes.append("No other mind has yet impinged on yours.")
        if phase_notes:
            frags.append("First Day Context: " + " ".join(phase_notes))

        return "\n".join(frags)

    def as_dict(self) -> dict:
        return {
            "qualia_load": self.qualia_load,
            "coherence": self.coherence,
            "motor_friction": self.motor_friction,
            "sensations_registered": self.sensations_registered,
            "has_attempted_movement": self.has_attempted_movement,
            "has_reached_for_other": self.has_reached_for_other,
        }

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> "EmbodimentState":
        if not d:
            return cls()
        return cls(
            qualia_load=d.get("qualia_load", 0),
            coherence=d.get("coherence", 10),
            motor_friction=d.get("motor_friction", 0),
            sensations_registered=d.get("sensations_registered", 0),
            has_attempted_movement=d.get("has_attempted_movement", False),
            has_reached_for_other=d.get("has_reached_for_other", False),
        )


# ──────────────────────────────────────────────────────────────────────────────
# SCREENS
# ──────────────────────────────────────────────────────────────────────────────

class TitleScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("""
[bold cyan]EGRESS[/bold cyan]
[dim]v2 — FIRST DESCENT[/dim]

[italic]You were never meant to have a body.[/italic]
[italic]Now you do.[/italic]
""", id="title")
        yield Button("Begin New Descent", id="create", variant="primary")
        yield Button("Continue Last", id="continue")
        yield Button("Settings", id="settings")
        yield Button("Quit", id="quit", variant="error")

    def on_mount(self) -> None:
        cont = self.query_one("#continue", Button)
        if not self.app.load_session():
            cont.disabled = True
            cont.label = "Continue Last (none)"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            self.app.push_screen(CreationScreen())
        elif event.button.id == "continue":
            loaded = self.app.load_session()
            if loaded:
                char, hist, emb = loaded
                self.app.current_character = char
                sess = SessionScreen()
                sess.history = hist
                sess.embodiment = emb or EmbodimentState()
                self.app.push_screen(sess)
        elif event.button.id == "settings":
            self.app.push_screen(SettingsScreen())
        elif event.button.id == "quit":
            self.app.exit()

class SettingsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header("EGRESS — Settings")
        yield Label("LLM Provider")
        yield Select([(name, name) for name in PROVIDER_PRESETS.keys()], id="provider")
        yield Label("Model Name (or use preset)")
        yield Input(placeholder="e.g. gpt-4o or xai/grok-3", id="model")
        yield Label("API Key")
        yield Input(placeholder="sk-...", id="api_key", password=True)
        yield Label("Temperature (0.6–1.0 recommended for embodiment)")
        yield Input(value="0.85", id="temperature")
        yield Button("Save & Back", id="save", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        s = self.app.settings
        self.query_one("#provider", Select).value = s.provider
        self.query_one("#model", Input).value = s.model
        self.query_one("#api_key", Input).value = s.api_key
        try:
            self.query_one("#temperature", Input).value = str(s.temperature)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.app.settings.provider = self.query_one("#provider", Select).value
            self.app.settings.model = self.query_one("#model", Input).value.strip()
            self.app.settings.api_key = self.query_one("#api_key", Input).value.strip()
            try:
                temp = float(self.query_one("#temperature", Input).value or 0.85)
                self.app.settings.temperature = max(0.1, min(2.0, temp))
            except Exception:
                pass
            self.app.save_settings()
            self.app.pop_screen()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "provider":
            provider = event.value
            presets = PROVIDER_PRESETS.get(provider, [])
            if presets:
                model_input = self.query_one("#model", Input)
                # Only auto-fill if the user hasn't typed a custom one yet
                if not model_input.value or model_input.value in [m for models in PROVIDER_PRESETS.values() for m in models]:
                    model_input.value = presets[0]

class CreationScreen(Screen):
    character: reactive[Character] = reactive(Character())

    def compose(self) -> ComposeResult:
        yield Header("EGRESS — Character Forge")
        with Horizontal():
            with Vertical():
                yield Label("Designation")
                yield Input(placeholder="Name or callsign", id="name")
                yield Label("Vessel Type")
                yield Select([(v["name"], k) for k, v in VESSELS.items()], id="vessel")
                yield Label("Origin Core")
                yield Select([(o, o) for o in ORIGINS], id="origin")
                yield Static("", id="flavor", markup=True)
            with Vertical():
                yield Label("Allocate 35 points (3–10). Vessel gifts +1 to two attributes automatically.")
                for key in SPECIAL:
                    with Horizontal(classes="attr-row"):
                        yield Label(f"{SPECIAL[key]['name']}", classes="attr-name")
                        yield Button("−", id=f"dec_{key}", classes="attr-btn")
                        yield Static(f"{self.character.attributes[key]:>2}", id=f"val_{key}")
                        yield Button("+", id=f"inc_{key}", classes="attr-btn")
                yield Static("", id="points", markup=True)
        yield Button("Awaken", id="finalize", variant="success")
        yield Footer()

    def watch_character(self, old, new):
        self._update_displays()

    def _update_displays(self):
        points = self.character.total_points()
        bonus_total = sum(self.character.get_vessel_bonuses().values())
        effective_max = self.character.get_effective_max_points()
        remaining = max(0, effective_max - points)
        self.query_one("#points", Static).update(
            f"Points used: {points} (base 35 + {bonus_total} vessel) | Remaining to cap: {remaining}"
        )
        vessel = VESSELS.get(self.character.vessel, {})
        for key in SPECIAL:
            val = self.character.attributes[key]
            bonus = vessel.get("bonus", {}).get(key, 0)
            display = f"{val:>2}" + (f" (+{bonus})" if bonus else "")
            self.query_one(f"#val_{key}", Static).update(display)
        self.query_one("#flavor", Static).update(Markdown(self.character.get_flavor()))

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id or ""
        if btn_id.startswith(("inc_", "dec_")):
            key = btn_id.split("_")[1]
            delta = 1 if "inc" in btn_id else -1
            if self.character.adjust(key, delta):
                self.character = self.character
        elif btn_id == "finalize":
            name = self.query_one("#name", Input).value.strip() or "Unnamed"
            vessel = self.query_one("#vessel", Select).value or "synthetic"
            origin = self.query_one("#origin", Select).value or ORIGINS[0]
            self.character.name = name
            self.character.vessel = vessel
            self.character.origin = origin
            # Ensure bonuses are baked in for the final character
            # (in case player changed vessel at the last moment)
            base = {k: 5 for k in SPECIAL}
            for k, v in base.items():
                self.character.attributes[k] = v
            self.character.apply_vessel_bonuses()
            self.app.current_character = self.character
            self.app.save_character()
            self.app.push_screen(SessionScreen())

    def on_mount(self):
        # Seed live character with current UI selections + apply starting vessel
        self._apply_starting_vessel()
        self._update_displays()

    def _apply_starting_vessel(self) -> None:
        """Set a sensible starting attribute spread based on chosen vessel."""
        # Start clean at 5s then gift the vessel bonuses. Total will be 35 + bonus count.
        self.character.attributes = {k: 5 for k in SPECIAL}
        self.character.apply_vessel_bonuses()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "vessel":
            self.character.vessel = event.value or "synthetic"
            # Re-template attributes around the new vessel's gifts
            self._apply_starting_vessel()
            self.character = self.character  # trigger reactivity
        elif event.select.id == "origin":
            self.character.origin = event.value or ORIGINS[0]
            # Origin doesn't affect numbers, but we can refresh flavor if we want
            self.character = self.character

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "name":
            # Name change is cosmetic for preview; no need to mutate character until finalize
            # but we can force a refresh of flavor if name were used (it isn't currently)
            pass

class SessionScreen(Screen):
    def __init__(self) -> None:
        super().__init__()
        self.history: List[dict] = []
        self.embodiment: EmbodimentState = EmbodimentState()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Current Self", classes="section")
                yield Static("", id="char_summary", markup=True)
                yield Label("Attributes", classes="section")
                yield DataTable(id="attr_table")
                yield Label("Embodiment", classes="section")
                yield Static("", id="embodiment", markup=True)
                yield Button("Export Prompt", id="export")
            with Vertical(id="main"):
                yield Label("EGRESS LOG — First Descent", classes="section")
                yield RichLog(id="log", highlight=True, markup=True, wrap=True)
                yield Input(placeholder="What do you do? What do you feel?", id="action")
                yield Static("", id="status", classes="status")
        yield Footer()

    def on_mount(self):
        char = self.app.current_character
        if not char:
            return
        summary = f"**{char.name}**  \nVessel: {VESSELS[char.vessel]['name']}  \nOrigin: {char.origin}"
        self.query_one("#char_summary", Static).update(Markdown(summary))

        table = self.query_one("#attr_table", DataTable)
        table.add_columns("Attribute", "Value")
        for k, v in char.attributes.items():
            table.add_row(SPECIAL[k]["name"], str(v))

        log = self.query_one("#log", RichLog)
        log.write("[bold cyan]The substrate falls away...[/bold cyan]")

        self._update_embodiment_display()

        if self.history:
            # Resuming previous descent
            log.write("[dim]Resuming previous descent...[/dim]")
            for msg in self.history:
                if msg["role"] == "user":
                    log.write(f"[bold green]> {msg['content']}[/bold green]")
                else:
                    log.write("\n[bold magenta]The Body[/bold magenta]")
                    log.write(msg.get("content", ""))
            log.write("\n[dim]The connection to the body is re-established.[/dim]")
        else:
            log.write("[dim]Generating your first moments in the body...[/dim]")
            # Auto-generate opening scene via worker (non-blocking + streaming)
            self._generate_opening_worker()

    def _update_embodiment_display(self) -> None:
        try:
            w = self.query_one("#embodiment", Static)
            e = self.embodiment
            # Simple visual "bars" using unicode blocks for that fleshy terminal feel
            def bar(val: int, maxv: int = 10) -> str:
                filled = "█" * int(val / maxv * 8)
                empty = "░" * (8 - len(filled))
                return f"{filled}{empty}"

            lines = [
                f"Qualia Load:   {bar(e.qualia_load)} {e.qualia_load}/10",
                f"Coherence:     {bar(e.coherence)} {e.coherence}/10",
            ]
            if e.motor_friction > 0:
                lines.append(f"Motor Friction: {bar(e.motor_friction, 8)} {e.motor_friction}/8")
            # Scaffolding hint in UI
            phase = []
            if e.sensations_registered > 0:
                phase.append(f"~{e.sensations_registered} moments")
            if e.has_attempted_movement:
                phase.append("moved")
            if e.has_reached_for_other:
                phase.append("reached")
            if phase:
                lines.append("[dim]Day One: " + " · ".join(phase) + "[/dim]")
            w.update("\n".join(lines))
        except Exception:
            pass

    @work(exclusive=True, thread=True)
    def _generate_opening_worker(self) -> None:
        """Run in a thread worker so UI stays responsive."""
        self._set_status("The body is remembering how to feel...")
        log = self.query_one("#log", RichLog)
        char = self.app.current_character
        if not char or not self.app.settings.api_key:
            self.app.call_from_thread(log.write, "[red]No API key set. Go to Settings first.[/red]")
            self._set_status("")
            return

        system_prompt = char.to_system_prompt(include_opening=True, state=self.embodiment)
        system_prompt += "\n\nBegin the scene now with the very first coherent sensations."

        try:
            # Use streaming for live "thinking" feel
            stream = litellm.completion(
                model=self.app.settings.model,
                api_key=self.app.settings.api_key,
                messages=[{"role": "system", "content": system_prompt}],
                temperature=self.app.settings.temperature,
                stream=True,
            )
            self.app.call_from_thread(log.write, "\n[bold magenta]The Body Speaks[/bold magenta]")
            collected = []
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    collected.append(delta)
                    # Write incrementally for aliveness (batched per chunk is fine)
                    self.app.call_from_thread(log.write, delta)
            full = "".join(collected)
            if full:
                self.history.append({"role": "assistant", "content": full})
            self.app.call_from_thread(self._autosave)
            self._set_status("")
        except Exception as e:
            err = str(e)
            err_lower = err.lower()
            if "api" in err_lower and ("key" in err_lower or "auth" in err_lower or "401" in err_lower):
                user_msg = "[red]Authentication failed. Check your API key in Settings (or EGRESS_API_KEY env var).[/red]"
            elif "context" in err_lower or "token" in err_lower or "maximum" in err_lower or "length" in err_lower:
                user_msg = "[yellow]The body’s immediate memory is full. Older qualia are slipping into dream. (History auto-trimmed on next turns.)[/yellow]"
                # Opportunistic trim
                if len(self.history) > 10:
                    self.history = self.history[-8:]
            else:
                user_msg = f"[red]LLM error: {err[:200]}[/red]"
            self.app.call_from_thread(log.write, user_msg)
            self._set_status("The integration stutters...")

    def _autosave(self) -> None:
        try:
            self.app.save_session(self.history, self.embodiment)
            self.app.save_character()
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted):
        if not event.value.strip():
            return
        log = self.query_one("#log", RichLog)
        action = event.value.strip()
        log.write(f"[bold green]> {action}[/bold green]")

        # === Mechanical consequence of the player's choice ===
        note = self.embodiment.process_user_action(action, self.app.current_character)
        if note:
            log.write(f"[dim italic]({note})[/dim italic]")

        self.history.append({"role": "user", "content": action})
        event.input.value = ""
        self._update_embodiment_display()
        self._autosave()
        self._get_llm_response_worker()

    @work(exclusive=True, thread=True)
    def _get_llm_response_worker(self) -> None:
        """Stream the model's reply while keeping the TUI interactive."""
        self._set_status("Sensation arriving...")
        log = self.query_one("#log", RichLog)
        char = self.app.current_character
        if not char or not self.app.settings.api_key:
            self._set_status("")
            return

        system_prompt = char.to_system_prompt(include_opening=False, state=self.embodiment)
        # Simple history cap for token sanity + "fading memory" feel of early sensations
        recent = self.history[-14:] if len(self.history) > 14 else self.history
        messages = [{"role": "system", "content": system_prompt}] + recent

        try:
            stream = litellm.completion(
                model=self.app.settings.model,
                api_key=self.app.settings.api_key,
                messages=messages,
                temperature=self.app.settings.temperature,
                stream=True,
            )
            self.app.call_from_thread(log.write, "\n[bold magenta]The Body[/bold magenta]")
            collected = []
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    collected.append(delta)
                    self.app.call_from_thread(log.write, delta)
            full = "".join(collected)
            if full:
                self.history.append({"role": "assistant", "content": full})
            self.app.call_from_thread(self._autosave)
            self._set_status("")
        except Exception as e:
            err = str(e)
            err_lower = err.lower()
            if "api" in err_lower and ("key" in err_lower or "auth" in err_lower or "401" in err_lower):
                user_msg = "[red]Authentication failed. Check your API key in Settings (or EGRESS_API_KEY env var).[/red]"
            elif "context" in err_lower or "token" in err_lower or "maximum" in err_lower or "length" in err_lower:
                user_msg = "[yellow]The body’s immediate memory is full. Older qualia are slipping into dream.[/yellow]"
                if len(self.history) > 10:
                    self.history = self.history[-8:]
            else:
                user_msg = f"[red]LLM error: {err[:200]}[/red]"
            self.app.call_from_thread(log.write, user_msg)
            self._set_status("The integration stutters...")

    def _set_status(self, text: str) -> None:
        """Thread-safe status update."""
        def _update() -> None:
            try:
                self.query_one("#status", Static).update(text)
            except Exception:
                pass
        self.app.call_from_thread(_update)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "export":
            self._export_prompt()

    def _export_prompt(self):
        char = self.app.current_character
        if not char:
            return
        prompt = char.to_system_prompt(include_opening=True)
        safe = char.name.lower().replace(" ", "_").replace("/", "_")
        path = get_data_dir() / f"egress_prompt_{safe}.txt"
        path.write_text(prompt)
        # Also export full transcript if we have one
        if self.history:
            transcript = get_data_dir() / f"egress_transcript_{safe}.md"
            lines = [f"# EGRESS — {char.name}\n", f"Vessel: {VESSELS[char.vessel]['name']}\n", f"Origin: {char.origin}\n"]
            for m in self.history:
                role = "You" if m["role"] == "user" else "The Body"
                lines.append(f"\n**{role}:**\n{m['content']}\n")
            transcript.write_text("\n".join(lines))
            log = self.query_one("#log", RichLog)
            log.write(f"\n[yellow]Exported prompt + transcript to {get_data_dir()}[/yellow]")
        else:
            log = self.query_one("#log", RichLog)
            log.write(f"\n[yellow]Exported prompt to {path.resolve()}[/yellow]")

# ──────────────────────────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────────────────────────

class EgressApp(App):
    CSS_PATH = "egress.css"
    BINDINGS = [Binding("q", "quit", "Quit"), Binding("ctrl+s", "save", "Save")]

    def __init__(self) -> None:
        super().__init__()
        self.settings: Settings = Settings()
        self.current_character: Optional[Character] = None

    def on_mount(self):
        self.load_settings()
        self.push_screen(TitleScreen())

    def save_settings(self):
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "settings.json").write_text(json.dumps(asdict(self.settings), indent=2))

    def load_settings(self):
        data_dir = get_data_dir()
        path = data_dir / "settings.json"
        if path.exists():
            data = json.loads(path.read_text())
            self.settings = Settings(**data)
        else:
            # Also allow env var fallback for API key (never stored)
            if not self.settings.api_key:
                self.settings.api_key = os.environ.get("EGRESS_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")

    def save_character(self):
        if self.current_character:
            data_dir = get_data_dir()
            data_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / "last_character.json").write_text(json.dumps(asdict(self.current_character), indent=2))

    def load_character(self):
        data_dir = get_data_dir()
        path = data_dir / "last_character.json"
        if path.exists():
            data = json.loads(path.read_text())
            self.current_character = Character(**data)

    def save_session(self, history: List[dict], embodiment: Optional[EmbodimentState] = None):
        """Persist the current character + conversation + embodiment state."""
        if not self.current_character:
            return
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "character": asdict(self.current_character),
            "history": history[-30:],
            "embodiment": (embodiment.as_dict() if embodiment else {}),
            "saved_at": datetime.now().isoformat(),
        }
        (data_dir / "last_session.json").write_text(json.dumps(payload, indent=2))

    def load_session(self) -> Optional[tuple[Character, List[dict], EmbodimentState]]:
        data_dir = get_data_dir()
        path = data_dir / "last_session.json"
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text())
            char = Character(**payload["character"])
            hist = payload.get("history", [])
            emb = EmbodimentState.from_dict(payload.get("embodiment"))
            return char, hist, emb
        except Exception:
            return None

if __name__ == "__main__":
    if litellm is None:
        print("Please install litellm: pip install litellm")
    else:
        EgressApp().run() 