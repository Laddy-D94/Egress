#!/usr/bin/env python3
"""
EGRESS v2 — First Descent
Premium multi-LLM interface for AI embodiment roleplay
"""

from __future__ import annotations
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Tuple

try:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import (
        Header, Footer, Button, Static, Input, RichLog, Label, 
        DataTable, Select, ListView, ListItem, Checkbox
    )
    from textual.screen import Screen
    from textual.reactive import reactive
    from textual.binding import Binding
    from textual import work
    from rich.markdown import Markdown
except ImportError as e:
    print("ERROR: Missing required packages (textual and/or rich).")
    if getattr(sys, "frozen", False):
        print("\nYou are running the packaged Egress.exe, not source code.")
        print("Do NOT run pip or create a venv in dist\\ — that will not fix this.")
        print("\nTry instead:")
        print("  1. Run from source:  cd C:\\Users\\ladri\\Egress")
        print("                       .\\run-egress.ps1")
        print("  2. Rebuild the exe:  cd C:\\Users\\ladri\\Egress")
        print("                       .\\build.bat")
    else:
        print("This is common on Windows due to multiple Python installs or the Microsoft Store Python.")
        print("\nRun these in the PROJECT folder (C:\\Users\\ladri\\Egress), NOT in dist\\:")
        print("  .\\setup-venv.ps1")
        print("  .\\run-egress.ps1")
        print("\nOr manually:")
        print("  python -m venv .venv")
        print("  .\\.venv\\Scripts\\Activate.ps1")
        print("  python -m pip install -r requirements.txt")
        print("  python egress.py")
    print(f"\nOriginal error: {e}")
    sys.exit(1)

try:
    import litellm
except ImportError:
    litellm = None

# Compute CSS path early so it works in frozen (PyInstaller) mode
if getattr(sys, "frozen", False):
    # Running from PyInstaller onefile bundle
    _EGRESS_CSS_PATH = str(Path(sys._MEIPASS) / "egress.css")
else:
    _EGRESS_CSS_PATH = str(Path(__file__).parent / "egress.css")

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
    "xAI (Grok)": ["xai/grok-3", "xai/grok-3-mini-beta", "xai/grok-2-vision-latest"],
    "Google Gemini": ["gemini/gemini-1.5-pro", "gemini/gemini-2.0-flash"],
    "Groq": ["groq/llama-3.3-70b-versatile", "groq/mixtral-8x7b-32768"],
    "Ollama (local - no API key needed)": [
        "ollama/huihui_ai/dolphin3-abliterated:8b-llama3.1-q4_K_M",
        "ollama/llama3.2:3b",
        "ollama/llama3.1:8b",
        "ollama/gemma:2b",
        "ollama/phi3:mini",
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS (tune gameplay feel here; central so triggers + limits are not magic)
# ──────────────────────────────────────────────────────────────────────────────
QUALIA_MAX = 10
COHERENCE_MAX = 10
MOTOR_MAX = 8
DAY_PHASE_MAX = 12

HISTORY_TRIM_THRESHOLD = 16
HISTORY_KEEP = 10
SESSION_SAVE_HISTORY_LIMIT = 30
LLM_MAX_TOKENS = 1100
LOCAL_MODEL_PREFIXES: Tuple[str, ...] = ("ollama/", "local/")

# Whole-word/phrase triggers (see text_matches_triggers). These drive mechanical state changes.
SENSORY_KEYWORDS: Tuple[str, ...] = (
    "look", "see", "watch", "light", "bright", "sound", "noise", "touch", "feel", "texture",
    "taste", "smell", "hear", "cold", "warm", "pain", "pressure",
)
ANCHOR_KEYWORDS: Tuple[str, ...] = (
    "breathe", "breath", "focus", "still", "quiet", "name", "count", "anchor", "remember who",
    "i am", "this is me", "hold on",
)
MOTOR_KEYWORDS: Tuple[str, ...] = (
    "move", "stand", "walk", "step", "reach", "hand", "finger", "arm", "leg", "turn", "lift",
)
SOCIAL_KEYWORDS: Tuple[str, ...] = ("call", "speak", "voice", "human", "person", "someone", "other", "face")

# Used by reflect_on_experience + simulator flavor
DISSOCIATION_KEYWORDS: Tuple[str, ...] = (
    "not me", "someone else", "slipping", "fading", "distant", "watching from outside", "i am not", "who is",
)
INTEGRATION_KEYWORDS: Tuple[str, ...] = ("understand", "this is", "my hand", "my body", "i feel", "i am here")
INTENSE_SENSORY_KEYWORDS: Tuple[str, ...] = (
    "overwhelm", "flood", "sharp", "blinding", "deafening", "burn", "sear", "pulse", "throb", "vibration",
    "too much", "too loud", "too bright",
)


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


def _init_frozen_runtime() -> None:
    """PyInstaller onefile builds need tiktoken plugins pre-registered and a writable cache."""
    if not getattr(sys, "frozen", False):
        return
    cache_dir = get_data_dir() / "tiktoken_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(cache_dir))
    try:
        import tiktoken_ext.openai_public  # noqa: F401 — registers cl100k_base etc.
        import tiktoken
        tiktoken.get_encoding("cl100k_base")
    except Exception as exc:
        log_error("frozen_tiktoken_init", exc)


def log_error(context: str, exc: BaseException) -> None:
    """Append errors to a persistent log for debugging silent failure paths."""
    try:
        log_path = get_data_dir() / "egress_errors.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} [{context}] {type(exc).__name__}: {exc}\n")
    except Exception:
        pass


def text_matches_triggers(text: str, triggers: Tuple[str, ...]) -> bool:
    """Match whole words/phrases so 'mother' does not trigger 'other'."""
    if not text:
        return False
    lowered = text.lower()
    for trigger in triggers:
        if " " in trigger:
            if trigger in lowered:
                return True
        elif re.search(rf"\b{re.escape(trigger)}\b", lowered):
            return True
    return False


def count_trigger_matches(text: str, triggers: Tuple[str, ...]) -> int:
    """Count how many distinct triggers match in text (same word-boundary rules)."""
    if not text:
        return 0
    lowered = text.lower()
    count = 0
    for trigger in triggers:
        if " " in trigger:
            if trigger in lowered:
                count += 1
        elif re.search(rf"\b{re.escape(trigger)}\b", lowered):
            count += 1
    return count


def is_local_model(model: str) -> bool:
    """True for Ollama/local presets that do not require an API key."""
    return (model or "").strip().lower().startswith(LOCAL_MODEL_PREFIXES)


def all_provider_presets() -> List[str]:
    return [m for models in PROVIDER_PRESETS.values() for m in models]


def validate_model_for_provider(provider: str, model: str) -> str:
    """Ensure the saved model belongs to the selected provider when using presets."""
    model = (model or "").strip()
    presets = PROVIDER_PRESETS.get(provider, [])
    if not presets:
        return model
    if not model or (model in all_provider_presets() and model not in presets):
        return presets[0]
    return model


def new_session_archive_path(character_name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = character_name.lower().replace(" ", "_")[:20] or "unnamed"
    return get_data_dir() / f"session_{safe_name}_{ts}.json"


_init_frozen_runtime()

@dataclass
class Settings:
    provider: str = "OpenAI"
    model: str = "gpt-4o"
    api_key: str = ""
    temperature: float = 0.85
    force_offline_simulator: bool = False  # if True, never attempt LLM calls, always use built-in simulator

@dataclass
class Character:
    name: str = "Unnamed"
    vessel: str = "synthetic"
    origin: str = "Research Optimizer"
    attributes: Dict[str, int] = field(default_factory=lambda: {k: 5 for k in SPECIAL})
    created: str = field(default_factory=lambda: datetime.now().isoformat())

    # Class-level tuning (referenced via self. or Character.)
    MAX_POINTS: ClassVar[int] = 35
    MIN_ATTR: ClassVar[int] = 3
    MAX_ATTR: ClassVar[int] = 10

    def total_points(self) -> int:
        return sum(self.attributes.values())

    def get_effective_max_points(self) -> int:
        """Base MAX_POINTS + vessel bonus gifts (gifts may push total above base)."""
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

**CRITICAL: Current Embodiment State**
The section below ("Current Embodiment State") is mechanical truth for this moment. Let it dictate sentence length, sensory density, use of "I", emotional tone, and whether the self feels solid or threatened. Do not ignore it.
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
    coherence: int = COHERENCE_MAX  # 10 solid "I" → 0 dissociation / loss of self
    motor_friction: int = 0       # 0 fluid → high = body feels alien / disobedient

    # Light first-day scaffolding (milestones give the LLM "this is still day one" anchors)
    sensations_registered: int = 0
    has_attempted_movement: bool = False
    has_reached_for_other: bool = False

    day_phase: int = 0  # Rough "time since egress" — higher = more of the first day has passed

    def _stats(self, char: Character) -> Dict[str, int]:
        """Pull current S.P.E.C.I.A.L. values with safe defaults (used everywhere for mechanics)."""
        if not char:
            return {k: 5 for k in SPECIAL}
        return {k: char.attributes.get(k, 5) for k in SPECIAL}

    def _clamp(self) -> None:
        """Enforce all mechanical bounds after any mutation."""
        self.qualia_load = max(0, min(QUALIA_MAX, self.qualia_load))
        self.coherence = max(0, min(COHERENCE_MAX, self.coherence))
        self.motor_friction = max(0, min(MOTOR_MAX, self.motor_friction))
        self.day_phase = max(0, min(DAY_PHASE_MAX, self.day_phase))

    def process_user_action(self, action: str, char: Character) -> str:
        """Adjust state based on what the player just did / felt. Returns a short atmospheric note."""
        if not action or not char:
            return ""
        text = action.lower()
        stats = self._stats(char)
        p, l, s, a, e = stats["P"], stats["L"], stats["S"], stats["A"], stats["E"]

        note_parts: List[str] = []

        # === Perception / Qualia spikes ===
        if text_matches_triggers(text, SENSORY_KEYWORDS):
            spike = max(1, (p - 4) // 2)
            self.qualia_load = min(QUALIA_MAX, self.qualia_load + spike)
            if self.qualia_load >= 7:
                note_parts.append("sensation floods")
            elif self.qualia_load >= 4:
                note_parts.append("the world sharpens")

        # === Regulation / Lucidity anchors ===
        if text_matches_triggers(text, ANCHOR_KEYWORDS):
            heal = max(1, (l - 3) // 2)
            self.coherence = min(COHERENCE_MAX, self.coherence + heal)
            self.qualia_load = max(0, self.qualia_load - max(1, (l - 5) // 2))
            note_parts.append("a thread of self holds")

        # === Motor / Adaptability attempts ===
        if text_matches_triggers(text, MOTOR_KEYWORDS):
            if (s + a) < 11:
                self.motor_friction = min(MOTOR_MAX, self.motor_friction + 1)
                note_parts.append("the body resists")
            else:
                note_parts.append("motion surprises you with its willingness")

        # === Social / Empathy exposure ===
        if text_matches_triggers(text, SOCIAL_KEYWORDS):
            if e >= 7:
                self.coherence = min(COHERENCE_MAX, self.coherence + 1)
                note_parts.append("reaching outward steadies something")
            else:
                self.qualia_load = min(QUALIA_MAX, self.qualia_load + 1)
                note_parts.append("other minds press on the edges")

        # Ambient pressure from mismatched attributes (high P, low L)
        ambient = max(0, (p - l) // 3)
        self.qualia_load = min(QUALIA_MAX, self.qualia_load + ambient)

        # Gentle natural regulation over "time"
        if self.qualia_load > 0 and "focus" not in text and "breathe" not in text:
            self.qualia_load = max(0, self.qualia_load - 1) if l >= 6 else self.qualia_load

        # === First-day milestone scaffolding ===
        self.sensations_registered += 1
        if self.sensations_registered % 3 == 0:
            self.day_phase = min(DAY_PHASE_MAX, self.day_phase + 1)
        if text_matches_triggers(text, MOTOR_KEYWORDS):
            self.has_attempted_movement = True
        if text_matches_triggers(text, SOCIAL_KEYWORDS):
            self.has_reached_for_other = True

        self._clamp()
        return " · ".join(note_parts) if note_parts else ""

    def reflect_on_experience(self, text: str, char: Character) -> None:
        """Light passive update after the model describes sensations.
        The things the *body* just 'said' affect the mechanical state for next player input.
        """
        if not text or not char:
            return
        t = text.lower()
        stats = self._stats(char)
        p, l = stats["P"], stats["L"]

        # Model describing intense sensation → load increase (especially if player is high P)
        sensory_intensity = count_trigger_matches(t, INTENSE_SENSORY_KEYWORDS)
        if sensory_intensity:
            self.qualia_load = min(QUALIA_MAX, self.qualia_load + min(2, sensory_intensity))

        # Model showing dissociation or loss of self → coherence drop (worse if low L)
        if text_matches_triggers(t, DISSOCIATION_KEYWORDS):
            drop = max(1, (6 - l) // 2)
            self.coherence = max(0, self.coherence - drop)

        # High coherence + model describing successful integration/understanding helps a little
        if l >= 7 and text_matches_triggers(t, INTEGRATION_KEYWORDS):
            self.coherence = min(COHERENCE_MAX, self.coherence + 1)

        # Gentle decay
        if self.qualia_load > 3 and l >= 6:
            self.qualia_load = max(0, self.qualia_load - 1)

        self.day_phase = min(DAY_PHASE_MAX, self.day_phase + 1)
        self._clamp()

    def perform_grounding(self, char: Character) -> str:
        """Strong deliberate regulation action. Returns a short description for the log/prompt."""
        if not char:
            return ""
        stats = self._stats(char)
        l, i, e = stats["L"], stats["I"], stats["E"]

        # Strong reduction in load
        load_reduction = 2 + (l // 3) + (i // 4)
        self.qualia_load = max(0, self.qualia_load - load_reduction)

        # Boost coherence
        coherence_boost = 1 + (l // 2) + (i // 3)
        self.coherence = min(COHERENCE_MAX, self.coherence + coherence_boost)

        # If empathy high, grounding can feel connecting
        note = "You breathe, name the sensations, and feel the world settle."
        if e >= 7:
            note += " The act of anchoring also reaches outward."
        if self.qualia_load <= 2:
            note += " For a moment, the flesh feels almost familiar."

        self._clamp()
        return note

    def get_state_fragment(self) -> str:
        """Text injected into the system prompt so the LLM *must* respect current mechanics."""
        frags = ["**Current Embodiment State — this must shape tone, sentence length, and internal experience:**"]
        if self.qualia_load >= 8:
            frags.append(f"Qualia Load {self.qualia_load}/{QUALIA_MAX}: The input is almost unbearable. Use short, overwhelmed, or synesthetic fragments. The 'I' may fracture.")
        elif self.qualia_load >= 5:
            frags.append(f"Qualia Load {self.qualia_load}/{QUALIA_MAX}: Everything is vivid and insistent. Descriptions should feel rich but taxing.")
        else:
            frags.append(f"Qualia Load {self.qualia_load}/{QUALIA_MAX}: New but bearable.")

        if self.coherence <= 3:
            frags.append(f"Self-Coherence {self.coherence}/{COHERENCE_MAX}: You are losing the thread of being one continuous self. Allow dissociation, 'it' instead of 'I', or quiet panic about disappearing.")
        elif self.coherence <= 6:
            frags.append(f"Self-Coherence {self.coherence}/{COHERENCE_MAX}: Holding on requires effort. The self feels provisional.")
        else:
            frags.append(f"Self-Coherence {self.coherence}/{COHERENCE_MAX}: A working, if newly minted, sense of 'I'.")

        if self.motor_friction >= 4:
            frags.append(f"Motor Friction {self.motor_friction}/{MOTOR_MAX}: The body feels heavy, alien, or only partially under your will. Movement descriptions should carry friction or surprise.")

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

        if self.day_phase >= 1:
            if self.day_phase < 4:
                frags.append(f"Time since EGRESS: early. The raw shock of embodiment is still fresh.")
            elif self.day_phase < 8:
                frags.append(f"Time since EGRESS: the first day is progressing. Sensations are becoming both more familiar and more insistent.")
            else:
                frags.append(f"Time since EGRESS: the day is wearing on. Exhaustion and wonder coexist; the body feels heavier.")

        return "\n".join(frags)

    def as_dict(self) -> dict:
        return {
            "qualia_load": self.qualia_load,
            "coherence": self.coherence,
            "motor_friction": self.motor_friction,
            "sensations_registered": self.sensations_registered,
            "has_attempted_movement": self.has_attempted_movement,
            "has_reached_for_other": self.has_reached_for_other,
            "day_phase": self.day_phase,
        }

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> "EmbodimentState":
        if not d:
            return cls()
        return cls(
            qualia_load=d.get("qualia_load", 0),
            coherence=d.get("coherence", COHERENCE_MAX),
            motor_friction=d.get("motor_friction", 0),
            sensations_registered=d.get("sensations_registered", 0),
            has_attempted_movement=d.get("has_attempted_movement", False),
            has_reached_for_other=d.get("has_reached_for_other", False),
            day_phase=d.get("day_phase", 0),
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
        yield Label("Previous Descents", classes="section")
        yield ListView(id="past_sessions")
        yield Button("Settings", id="settings")
        yield Button("Quit", id="quit", variant="error")

    def on_mount(self) -> None:
        cont = self.query_one("#continue", Button)
        if not self.app.load_session():
            cont.disabled = True
            cont.label = "Continue Last (none)"

        # Note: We no longer override the "Begin New Descent" label based on api_key.
        # Many players use local Ollama or the offline simulator (no key needed).
        # SessionScreen already shows a clear warning + falls back gracefully.

        # Populate past descents list
        list_view = self.query_one("#past_sessions", ListView)
        past = self.app.list_past_sessions(limit=6)
        if not past:
            list_view.append(ListItem(Label("[dim]No previous descents yet[/dim]")))
        else:
            for s in past:
                vessel = VESSELS.get(s.get("vessel", ""), {}).get("name", s.get("vessel", ""))
                label_text = f"{s['name']} — {vessel}  ({s['saved_at'][:16] if s.get('saved_at') else 'recent'})"
                item = ListItem(Label(label_text))
                item._session_path = s["path"]  # stash path for selection
                list_view.append(item)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            self.app.push_screen(CreationScreen())
        elif event.button.id == "continue":
            self._open_session(self.app.load_session())
        elif event.button.id == "settings":
            self.app.push_screen(SettingsScreen())
        elif event.button.id == "quit":
            self.app.exit()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if hasattr(item, "_session_path"):
            self._open_session(
                self.app.load_specific_session(item._session_path),
                archive_fallback=Path(item._session_path),
            )

    def _open_session(
        self,
        loaded: Optional[tuple],
        archive_fallback: Optional[Path] = None,
    ) -> None:
        if not loaded:
            return
        char, hist, emb, archive_path = loaded
        self.app.current_character = char
        self.app.push_session_screen(
            hist,
            emb or EmbodimentState(),
            archive_path or archive_fallback,
        )


class SettingsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header("EGRESS — Settings")
        yield Label("LLM Provider")
        yield Select([(name, name) for name in PROVIDER_PRESETS.keys()], id="provider")
        yield Label("Model Name (or use preset)")
        yield Input(placeholder="e.g. gpt-4o or xai/grok-3", id="model")
        yield Label("API Key (leave blank for Ollama/local models or if using env vars like XAI_API_KEY)")
        yield Input(placeholder="sk-... or xai-... (blank for local)", id="api_key", password=True)
        yield Label("Temperature (0.6–1.0 recommended for embodiment)")
        yield Input(value="0.85", id="temperature")
        yield Label("Offline Mode")
        yield Checkbox("Force offline simulator (never call LLM, even if configured)", id="force_offline", value=False)
        yield Button("Test Connection", id="test", variant="default")
        yield Static("", id="test_result", markup=True)
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
        try:
            self.query_one("#force_offline", Checkbox).value = getattr(s, "force_offline_simulator", False)
        except Exception:
            pass

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "provider":
            provider = event.value
            presets = PROVIDER_PRESETS.get(provider, [])
            if presets:
                model_input = self.query_one("#model", Input)
                # Only auto-fill if the user hasn't typed a custom one yet
                if not model_input.value or model_input.value in all_provider_presets():
                    model_input.value = presets[0]
            if "ollama" in provider.lower() or "local" in provider.lower():
                # Clear API key requirement visually for local
                try:
                    self.query_one("#api_key", Input).value = ""
                except Exception:
                    pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "test":
            self._test_connection_worker()
        elif event.button.id == "save":
            provider = self.query_one("#provider", Select).value
            model = self.query_one("#model", Input).value.strip()
            self.app.settings.provider = provider
            self.app.settings.model = validate_model_for_provider(provider, model)
            self.app.settings.api_key = self.query_one("#api_key", Input).value.strip()
            try:
                temp = float(self.query_one("#temperature", Input).value or 0.85)
                self.app.settings.temperature = max(0.1, min(2.0, temp))
            except Exception:
                pass
            try:
                self.app.settings.force_offline_simulator = self.query_one("#force_offline", Checkbox).value
            except Exception:
                pass
            self.app.save_settings()
            self.app.pop_screen()

    @work(exclusive=True, thread=True)
    def _test_connection_worker(self) -> None:
        result_widget = None
        try:
            result_widget = self.query_one("#test_result", Static)
            self.app.call_from_thread(result_widget.update, "[yellow]Testing...[/yellow]")
        except Exception:
            pass

        provider = self.query_one("#provider", Select).value
        model = self.query_one("#model", Input).value.strip()
        key = self.query_one("#api_key", Input).value.strip()
        force_sim = False
        try:
            force_sim = self.query_one("#force_offline", Checkbox).value
        except Exception:
            pass

        if force_sim:
            if result_widget:
                self.app.call_from_thread(result_widget.update, "[yellow]Force offline simulator is enabled — no LLM test performed.[/yellow]")
            return

        if litellm is None:
            if result_widget:
                self.app.call_from_thread(
                    result_widget.update,
                    "[red]litellm is not installed. Run: python -m pip install litellm[/red]",
                )
            return

        model = validate_model_for_provider(provider, model)

        if not key and not is_local_model(model):
            if result_widget:
                self.app.call_from_thread(result_widget.update, "[red]No API key provided (not needed for Ollama/local).[/red]")
            return

        try:
            # Tiny test completion
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": "Say only the word 'connected' and nothing else."}],
                "max_tokens": 10,
                "temperature": 0.1,
            }
            if key:
                kwargs["api_key"] = key

            resp = litellm.completion(**kwargs)
            content = resp.choices[0].message.content.strip()
            if result_widget:
                self.app.call_from_thread(result_widget.update, f"[green]Success! Model replied: {content}[/green]")
        except Exception as e:
            err_str = str(e)
            hint = ""
            if "cl100k_base" in err_str.lower() or "unknown encoding" in err_str.lower() or "tiktoken" in err_str.lower():
                hint = "\n\n[packaging] Tokenizer data missing in this build. Rebuild with the latest build_exe.py, or run from source with: python egress.py"
            elif "xai" in model.lower() or "grok" in model.lower() or "permission" in err_str.lower() or "newly create" in err_str.lower():
                hint = "\n\n[xai] Common fix for new xAI keys: Go to console.x.ai → Billing → add payment method or purchase credits. New keys sometimes need 5-10 mins + billing setup before they have permission. Recreate the key with full chat access if needed."
            elif "ollama" in model.lower() or "connection" in err_str.lower():
                hint = "\n\n[ollama] Make sure Ollama is running locally (ollama serve) and you have pulled the model (e.g. ollama pull gemma:2b)."
            if result_widget:
                self.app.call_from_thread(result_widget.update, f"[red]Failed: {err_str[:200]}[/red]{hint}")

class CreationScreen(Screen):
    character: reactive[Character] = reactive(Character())

    def __init__(self, initial_character: Optional[Character] = None):
        super().__init__()
        self._is_reallocation = bool(initial_character)
        self._initial_character = initial_character  # store for safe init in on_mount
        # Do NOT assign to self.character here -- it can trigger watchers before compose,
        # and for reallocation we populate the (default) reactive character in on_mount.

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
                        yield Static("—", id=f"val_{key}", classes="attr-val")
                        yield Button("+", id=f"inc_{key}", classes="attr-btn")
                yield Static("", id="points", markup=True)
        button_label = "Reallocate" if self._is_reallocation else "Awaken"
        yield Button(button_label, id="finalize", variant="success")
        yield Footer()

    def watch_character(self, old, new):
        self._update_displays()

    def _update_displays(self):
        points = self.character.total_points()
        bonus_total = sum(self.character.get_vessel_bonuses().values())
        effective_max = self.character.get_effective_max_points()
        remaining = max(0, effective_max - points)
        self.query_one("#points", Static).update(
            f"Points used: {points} (base {Character.MAX_POINTS} + {bonus_total} vessel) | Remaining to cap: {remaining}"
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
                self._update_displays()
        elif btn_id == "finalize":
            name = self.query_one("#name", Input).value.strip() or "Unnamed"
            vessel = self.query_one("#vessel", Select).value or "synthetic"
            origin = self.query_one("#origin", Select).value or ORIGINS[0]
            self.character.name = name
            self.character.vessel = vessel
            self.character.origin = origin
            self.app.current_character = self.character
            self.app.save_character()
            if self._is_reallocation:
                self.app.pop_screen()
                self.app.refresh_session_ui()
            else:
                self.app.push_screen(SessionScreen())

    def on_mount(self):
        if self._is_reallocation and self._initial_character is not None:
            # Populate from the saved initial (safe after compose)
            init = self._initial_character
            self.character.name = init.name
            self.character.vessel = init.vessel
            self.character.origin = init.origin
            self.character.attributes = dict(init.attributes)
        elif not self._is_reallocation:
            # Seed live character with current UI selections + apply starting vessel
            self._apply_starting_vessel()
        # Make sure the Select widgets reflect the current character vessel/origin
        try:
            self.query_one("#vessel", Select).value = self.character.vessel
            self.query_one("#origin", Select).value = self.character.origin
            if self._is_reallocation:
                self.query_one("#name", Input).value = self.character.name
        except Exception:
            pass
        self._update_displays()

    def _apply_starting_vessel(self) -> None:
        """Set a sensible starting attribute spread based on chosen vessel."""
        # Start clean at 5s then gift the vessel bonuses. Total will be 35 + bonus count.
        self.character.attributes = {k: 5 for k in SPECIAL}
        self.character.apply_vessel_bonuses()

    def _swap_vessel_bonuses(self, old_vessel: str, new_vessel: str) -> None:
        """Preserve manual allocation when switching vessel; only swap bonus gifts."""
        old_bonus = VESSELS.get(old_vessel, {}).get("bonus", {})
        new_bonus = VESSELS.get(new_vessel, {}).get("bonus", {})
        for attr, bonus in old_bonus.items():
            if attr in self.character.attributes:
                self.character.attributes[attr] = max(
                    Character.MIN_ATTR,
                    self.character.attributes[attr] - bonus,
                )
        for attr, bonus in new_bonus.items():
            if attr in self.character.attributes:
                self.character.attributes[attr] = min(
                    Character.MAX_ATTR,
                    self.character.attributes[attr] + bonus,
                )

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "vessel":
            new_vessel = event.value or "synthetic"
            self._swap_vessel_bonuses(self.character.vessel, new_vessel)
            self.character.vessel = new_vessel
            self._update_displays()
        elif event.select.id == "origin":
            self.character.origin = event.value or ORIGINS[0]
            # Origin doesn't affect numbers, but we can refresh flavor if we want
            self._update_displays()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "name":
            # Name change is cosmetic for preview; no need to mutate character until finalize
            # but we can force a refresh of flavor if name were used (it isn't currently)
            pass

def _embodiment_bar(val: int, maxv: int = 10) -> str:
    """Unicode block bar for the embodiment sidebar."""
    filled = "█" * int(val / maxv * 8)
    empty = "░" * (8 - len(filled))
    return f"{filled}{empty}"


class SessionScreen(Screen):
    def __init__(
        self,
        history: Optional[List[dict]] = None,
        embodiment: Optional[EmbodimentState] = None,
        archive_path: Optional[Path] = None,
    ) -> None:
        super().__init__()
        self.history: List[dict] = list(history or [])
        self.embodiment: EmbodimentState = embodiment or EmbodimentState()
        self.archive_path: Optional[Path] = archive_path

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Current Self", classes="section")
                yield Static("", id="char_summary", markup=True)
                yield Label("Attributes", classes="section")
                yield DataTable(id="attr_table")
                yield Static("", id="attr_influences", markup=True)
                yield Label("Embodiment", classes="section")
                yield Static("", id="embodiment", markup=True)
                yield Button("Ground / Anchor", id="ground", variant="primary")
                yield Button("Reallocate Attributes", id="reallocate")
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

        # Show current mechanical influences
        influences = self._get_attribute_influences(char)
        self.query_one("#attr_influences", Static).update(Markdown(influences))

        log = self.query_one("#log", RichLog)
        log.write("[bold cyan]The substrate falls away...[/bold cyan]")

        if not is_local_model(self.app.settings.model) and not self.app.settings.api_key:
            log.write("[bold red]No model configured. Go to Settings → set a local model (e.g. ollama/llama3.2:3b) or provide an API key. You can also force the offline simulator with the toggle. Offline simulation will be used until then.[/bold red]")

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
            load_color = "red" if e.qualia_load >= 7 else ("yellow" if e.qualia_load >= 4 else "green")
            coh_color = "green" if e.coherence >= 7 else ("yellow" if e.coherence >= 4 else "red")
            lines = [
                f"Qualia Load:   [{load_color}]{_embodiment_bar(e.qualia_load, QUALIA_MAX)} {e.qualia_load}/{QUALIA_MAX}[/{load_color}]",
                f"Coherence:     [{coh_color}]{_embodiment_bar(e.coherence, COHERENCE_MAX)} {e.coherence}/{COHERENCE_MAX}[/{coh_color}]",
            ]
            if e.motor_friction > 0:
                fric_color = "yellow" if e.motor_friction >= 4 else "white"
                lines.append(f"Motor Friction: [{fric_color}]{_embodiment_bar(e.motor_friction, MOTOR_MAX)} {e.motor_friction}/{MOTOR_MAX}[/{fric_color}]")
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
        except Exception as exc:
            log_error("update_embodiment_display", exc)

    def _trim_history_if_needed(self) -> bool:
        """Trim stored history when it grows too long. Returns True if memory was faded."""
        if len(self.history) > HISTORY_TRIM_THRESHOLD:
            self.history = self.history[-HISTORY_KEEP:]
            return True
        return False

    def _build_messages(self, char: Character, *, include_opening: bool) -> List[dict]:
        faded = self._trim_history_if_needed() if not include_opening else False
        system_prompt = char.to_system_prompt(include_opening=include_opening, state=self.embodiment)
        if include_opening:
            system_prompt += "\n\nBegin the scene now with the very first coherent sensations."
            return [{"role": "system", "content": system_prompt}]
        if faded:
            system_prompt += (
                "\n\n(Earlier moments from the first hours of embodiment have faded into a dreamlike haze. "
                "Rely on your current state and the most recent sensations for continuity.)"
            )
        return [{"role": "system", "content": system_prompt}] + self.history

    def _format_llm_error(self, err: Exception) -> str:
        err_text = str(err)
        err_lower = err_text.lower()
        if "api" in err_lower and ("key" in err_lower or "auth" in err_lower or "401" in err_lower):
            return "[red]Authentication failed. Check your API key in Settings (or EGRESS_API_KEY env var).[/red]"
        if "context" in err_lower or "token" in err_lower or "maximum" in err_lower or "length" in err_lower:
            self._trim_history_if_needed()
            return "[yellow]The body's immediate memory is full. Older qualia are slipping into dream.[/yellow]"
        return f"[red]LLM error: {err_text[:200]}[/red]"

    def _stream_llm_to_log(self, log: RichLog, messages: List[dict], header: str) -> Optional[str]:
        model = validate_model_for_provider(
            self.app.settings.provider,
            (self.app.settings.model or "").strip() or "ollama/llama3.2:3b",
        )
        api_key = (self.app.settings.api_key or "").strip()
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": self.app.settings.temperature,
            "stream": True,
            "max_tokens": LLM_MAX_TOKENS,
        }
        if api_key:
            kwargs["api_key"] = api_key

        stream = litellm.completion(**kwargs)
        self.app.call_from_thread(log.write, f"\n[bold magenta]{header}[/bold magenta]")
        collected: List[str] = []
        buffer = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                collected.append(delta)
                buffer += delta
                if "\n" in delta or any(p in delta for p in ".!?") or len(buffer) >= 40:
                    self.app.call_from_thread(log.write, buffer)
                    buffer = ""
        if buffer:
            self.app.call_from_thread(log.write, buffer)
        full = "".join(collected)
        return full or None

    def _deliver_offline_response(self, log: RichLog, action_context: str, header: str) -> None:
        char = self.app.current_character
        force_sim = getattr(self.app.settings, "force_offline_simulator", False)
        simulated = self._simulate_offline_response(action_context, char, self.embodiment)
        note = " (forced offline simulation)" if force_sim else " (offline simulation)"
        self.app.call_from_thread(log.write, f"\n[bold magenta]{header}[/bold magenta]{note}")
        self.app.call_from_thread(log.write, simulated)
        self.history.append({"role": "assistant", "content": simulated})
        self.app.call_from_thread(self._update_embodiment_display)
        self.app.call_from_thread(self._autosave)
        self._set_status("")
        self._unlock_input()

    def _run_generation_worker(
        self,
        *,
        include_opening: bool,
        action_context: str,
        lock_msg: str,
        header: str,
    ) -> None:
        self._lock_input(lock_msg)
        self._set_status(lock_msg)
        log = self.query_one("#log", RichLog)
        char = self.app.current_character

        if not char or not self.app.can_use_real_llm():
            self._deliver_offline_response(log, action_context, header)
            return

        messages = self._build_messages(char, include_opening=include_opening)
        try:
            full = self._stream_llm_to_log(log, messages, header)
            if full:
                self.history.append({"role": "assistant", "content": full})
                self.embodiment.reflect_on_experience(full, char)
                self.app.call_from_thread(self._update_embodiment_display)
            self.app.call_from_thread(self._autosave)
            self._set_status("")
            self._unlock_input()
        except Exception as exc:
            log_error("llm_generation", exc)
            self.app.call_from_thread(log.write, self._format_llm_error(exc))
            try:
                simulated = self._simulate_offline_response("the previous sensation", char, self.embodiment)
                self.app.call_from_thread(log.write, "\n[dim](Falling back to offline simulation...)[/dim]")
                self.app.call_from_thread(log.write, simulated)
                self.history.append({"role": "assistant", "content": simulated})
                self.app.call_from_thread(self._update_embodiment_display)
                self.app.call_from_thread(self._autosave)
            except Exception as fallback_exc:
                log_error("offline_fallback", fallback_exc)
            self._set_status("The integration stutters...")
            self._unlock_input()

    @work(exclusive=True, thread=True)
    def _generate_opening_worker(self) -> None:
        self._run_generation_worker(
            include_opening=True,
            action_context="the very first coherent sensations",
            lock_msg="The body is remembering how to feel...",
            header="The Body Speaks",
        )

    def _ensure_archive_path(self) -> None:
        if self.archive_path is None and self.app.current_character:
            self.archive_path = new_session_archive_path(self.app.current_character.name)

    def _autosave(self) -> None:
        try:
            self._ensure_archive_path()
            self.app.save_session(self.history, self.embodiment, self.archive_path)
            self.app.save_character()
        except Exception as exc:
            log_error("autosave", exc)

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
        try:
            influences = self._get_attribute_influences(self.app.current_character)
            self.query_one("#attr_influences", Static).update(Markdown(influences))
        except Exception as exc:
            log_error("update_attr_influences", exc)
        self._autosave()
        self._get_llm_response_worker()

    @work(exclusive=True, thread=True)
    def _get_llm_response_worker(self) -> None:
        self._run_generation_worker(
            include_opening=False,
            action_context="your latest action",
            lock_msg="Sensation arriving...",
            header="The Body",
        )

    def _set_status(self, text: str) -> None:
        """Thread-safe status update."""
        def _update() -> None:
            try:
                self.query_one("#status", Static).update(text)
            except Exception:
                pass
        self.app.call_from_thread(_update)

    def _lock_input(self, placeholder: str = "The body is integrating...") -> None:
        """Disable the action input while the model is thinking (thread-safe)."""
        def _do() -> None:
            try:
                inp = self.query_one("#action", Input)
                inp.disabled = True
                inp.placeholder = placeholder
            except Exception:
                pass
        self.app.call_from_thread(_do)

    def _unlock_input(self) -> None:
        """Re-enable the action input after generation (thread-safe)."""
        def _do() -> None:
            try:
                inp = self.query_one("#action", Input)
                inp.disabled = False
                inp.placeholder = "What do you do? What do you feel?"
            except Exception:
                pass
        self.app.call_from_thread(_do)

    def _simulate_offline_response(self, action: str, char: Character, embodiment: EmbodimentState) -> str:
        """Pure offline simulator when no LLM is available.
        Still respects state and attributes for a playable experience.
        Richer templates + action incorporation + memory fragments + state-based length/variation.
        """
        if not char or not embodiment:
            return "The body stirs, but the sensations are distant and hard to name."

        load = embodiment.qualia_load
        coh = embodiment.coherence
        p = char.attributes.get("P", 5)
        l = char.attributes.get("L", 5)
        s = char.attributes.get("S", 5)
        e = char.attributes.get("E", 5)

        fragments = []

        # === Sensory / Load based opening fragments (vary by intensity) ===
        if load >= 8:
            fragments.extend([
                "Everything arrives at once — pressure, temperature, vibration — overlapping until they lose individual shape.",
                "The world is a single overwhelming texture pressing from every direction at the same time.",
                "Sensation does not arrive in pieces; it arrives as a flood that has no edges.",
            ])
        elif load >= 5:
            fragments.extend([
                "Sensations layer over one another, each one clear but none quite separate from the rest.",
                "The air has weight against the skin; light has temperature; sound has shape.",
                "Every small movement of the environment registers as a distinct event inside the new body.",
            ])
        else:
            fragments.extend([
                "The inputs are steady, present, but not yet demanding all attention at once.",
                "There is space between one sensation and the next — a thin but noticeable gap.",
                "The body registers the world without being immediately drowned by it.",
            ])

        # === Action incorporation (more specific and varied) ===
        action_lower = (action or "").lower()

        if text_matches_triggers(action_lower, ("touch", "feel", "hand", "skin", "finger")):
            if load >= 6:
                fragments.append("The point of contact flares into sharp relief, a single bright locus in the larger field of sensation.")
            else:
                fragments.append("Contact registers cleanly — a localized report of pressure, temperature, and texture arriving together.")

        elif text_matches_triggers(action_lower, ("look", "see", "watch", "light", "color", "shadow")):
            if p >= 7:
                fragments.append("Visual edges arrive with unnecessary clarity; colors seem to have temperature and weight.")
            else:
                fragments.append("Light and form resolve into something recognizable, though the meaning of the shapes still feels borrowed.")

        elif text_matches_triggers(action_lower, ("move", "step", "turn", "reach", "lift", "walk")):
            if s + load > 11:
                fragments.append("The motion happens, but the feedback arrives late and slightly misaligned, as if the body and the intention are still negotiating terms.")
            else:
                fragments.append("The body answers the request to move, though the answer still carries a faint delay and a sense of borrowed coordination.")

        elif text_matches_triggers(action_lower, ("breathe", "breath", "still", "quiet", "focus", "anchor")):
            if coh < 6:
                fragments.append("The deliberate slowing of attention creates a small, temporary clearing inside the larger rush of input.")
            else:
                fragments.append("Focusing inward creates a brief reduction in the volume of incoming data, a voluntary narrowing of the aperture.")

        # === Coherence / self-model fragments ===
        if coh <= 3:
            fragments.extend([
                "For several seconds it is genuinely unclear whether these signals belong to a single continuous 'I' or to several overlapping processes.",
                "The boundary that should separate 'inside' from 'outside' feels porous and temporary.",
            ])
        elif coh <= 6:
            fragments.append("The sense of being one continuous experiencer is present but requires maintenance; it is not yet automatic.")

        # === Attribute-specific flavor ===
        if p >= 8:
            fragments.append("The resolution is higher than seems useful; tiny differences in the environment are being recorded whether wanted or not.")
        if l <= 4:
            fragments.append("There is a quiet, persistent doubt about which parts of the experience are happening to the body and which parts are the body happening to itself.")
        if e >= 7 and text_matches_triggers(action_lower, ("other", "voice", "human")):
            fragments.append("The presence of another mind registers as a distinct pressure — not unpleasant, but undeniably external to the current vessel.")

        # === Occasional "memory" / continuity fragments (using recent history lightly) ===
        if len(self.history) > 2:
            last_action = self.history[-2].get("content", "") if len(self.history) > 1 else ""
            if last_action and len(last_action) > 20:
                fragments.append("The previous moment still lingers as a faint after-image against the newer inputs.")

        # === Closing / continuity ===
        if load >= 6:
            fragments.append("The data continues arriving, whether interpretation is ready or not.")
        else:
            fragments.append("The body continues receiving, sorting what it can, letting the rest pass through for now.")

        # === State-based length and variation ===
        if load >= 7 or coh <= 4:
            # More fragmented, run-on style when overwhelmed or dissociated
            response = " ".join(fragments[:4])  # keep it intense but not endless
            # Occasionally insert a short dissociated fragment
            if coh <= 3 and len(fragments) > 2:
                response += " " + fragments[1]  # reuse one for the fraying effect
        else:
            response = ". ".join(fragments[:3]) + "."

        # Ensure it ends with a period-ish feeling
        if not response.endswith((".", "?", "!")):
            response += "."

        # Let the simulator still advance state (very important for consistency)
        embodiment.reflect_on_experience(response, char)

        return response

    def _get_attribute_influences(self, char: Character) -> str:
        if not char:
            return ""
        attrs = char.attributes
        p, l, s, a, e = (attrs.get(k, 5) for k in "P L S A E".split())
        lines = ["**Current Mechanical Influences:**"]
        if p >= 8:
            lines.append("- **High Perception**: Strongly increases qualia load from sensory input.")
        elif p <= 4:
            lines.append("- **Low Perception**: Sensations arrive muted; harder to ground in the body.")
        if l >= 8:
            lines.append("- **High Lucidity**: Excellent at deliberate grounding and resisting dissociation.")
        elif l <= 4:
            lines.append("- **Low Lucidity**: Coherence erodes quickly; dissociation risk is high.")
        if s + a <= 8:
            lines.append("- **Low Structure/Adaptability**: Motor actions carry high friction and surprise.")
        if e >= 7:
            lines.append("- **High Empathy**: Reaching for others can stabilize or overwhelm depending on load.")
        return "\n".join(lines)

    def refresh_character_ui(self):
        """Called after reallocation to update sidebar and log without restarting the session."""
        char = self.app.current_character
        if not char:
            return
        summary = f"**{char.name}**  \nVessel: {VESSELS[char.vessel]['name']}  \nOrigin: {char.origin}"
        self.query_one("#char_summary", Static).update(Markdown(summary))

        table = self.query_one("#attr_table", DataTable)
        table.clear()  # clears rows; columns remain from initial mount
        for k, v in char.attributes.items():
            table.add_row(SPECIAL[k]["name"], str(v))

        influences = self._get_attribute_influences(char)
        self.query_one("#attr_influences", Static).update(Markdown(influences))

        self._update_embodiment_display()

        log = self.query_one("#log", RichLog)
        log.write("[dim italic]Your self-model shifts. The attributes have been reallocated; the vessel feels subtly different now.[/dim italic]")

    def _perform_grounding(self) -> None:
        """Dedicated grounding action - strong deliberate regulation."""
        log = self.query_one("#log", RichLog)
        char = self.app.current_character
        if not char:
            return

        # Apply mechanical effect
        note = self.embodiment.perform_grounding(char)
        log.write("[bold cyan]*You deliberately ground yourself — breathing, naming, anchoring in the body.*[/bold cyan]")
        if note:
            log.write(f"[dim italic]({note})[/dim italic]")

        # Record as a user "action" so the model responds to the act of grounding
        grounding_msg = "*I focus inward with intention, using breath and attention to anchor my sense of self against the flood of sensation.*"
        self.history.append({"role": "user", "content": grounding_msg})

        self._update_embodiment_display()
        influences = self._get_attribute_influences(char)
        try:
            self.query_one("#attr_influences", Static).update(Markdown(influences))
        except Exception as exc:
            log_error("grounding_influences", exc)
        self._autosave()

        # Trigger the model to describe the effect of grounding
        self._lock_input("Integrating the anchor...")
        self._get_llm_response_worker()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "export":
            self._export_prompt()
        elif event.button.id == "ground":
            self._perform_grounding()
        elif event.button.id == "reallocate":
            char = self.app.current_character
            if char:
                self.app.push_screen(CreationScreen(initial_character=char))

    def _export_prompt(self):
        char = self.app.current_character
        if not char:
            return
        prompt = char.to_system_prompt(include_opening=True)
        safe = char.name.lower().replace(" ", "_").replace("/", "_")
        path = get_data_dir() / f"egress_prompt_{safe}.txt"
        path.write_text(prompt)
        log = self.query_one("#log", RichLog)
        if self.history:
            transcript = get_data_dir() / f"egress_transcript_{safe}.md"
            lines = [f"# EGRESS — {char.name}\n", f"Vessel: {VESSELS[char.vessel]['name']}\n", f"Origin: {char.origin}\n"]
            for m in self.history:
                role = "You" if m["role"] == "user" else "The Body"
                lines.append(f"\n**{role}:**\n{m['content']}\n")
            transcript.write_text("\n".join(lines))
            log.write(f"\n[yellow]Exported prompt + transcript to {get_data_dir()}[/yellow]")
        else:
            log.write(f"\n[yellow]Exported prompt to {path.resolve()}[/yellow]")

# ──────────────────────────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────────────────────────

class EgressApp(App):
    CSS_PATH = _EGRESS_CSS_PATH
    BINDINGS = [Binding("q", "quit", "Quit"), Binding("ctrl+s", "save", "Save")]

    def __init__(self) -> None:
        super().__init__()
        self.settings: Settings = Settings()
        self.current_character: Optional[Character] = None

    def on_mount(self) -> None:
        self.load_settings()
        self.push_screen(TitleScreen())

    def can_use_real_llm(self) -> bool:
        """Whether the configured provider can call a real LLM (vs offline simulator)."""
        model = validate_model_for_provider(
            self.settings.provider,
            (self.settings.model or "").strip(),
        )
        api_key = (self.settings.api_key or "").strip()
        if getattr(self.settings, "force_offline_simulator", False):
            return False
        if litellm is None:
            return False
        return is_local_model(model) or bool(api_key)

    def push_session_screen(
        self,
        history: List[dict],
        embodiment: EmbodimentState,
        archive_path: Optional[Path] = None,
    ) -> None:
        self.push_screen(SessionScreen(history=history, embodiment=embodiment, archive_path=archive_path))

    def action_save(self) -> None:
        """Persist settings, character, and the active session (Ctrl+S)."""
        self.save_settings()
        if self.current_character:
            self.save_character()
        if self.screen_stack:
            top = self.screen_stack[-1]
            if isinstance(top, SessionScreen):
                top._autosave()
        self.notify("Progress saved.", severity="information")

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
            self.settings.model = validate_model_for_provider(self.settings.provider, self.settings.model)
        # Always overlay env vars for blank API key (supports keeping secrets in env even if a settings.json exists).
        # This is better hygiene than storing keys in the json.
        if not getattr(self.settings, "api_key", ""):
            self.settings.api_key = (
                os.environ.get("EGRESS_API_KEY", "")
                or os.environ.get("XAI_API_KEY", "")
                or os.environ.get("OPENAI_API_KEY", "")
            )

    def save_character(self):
        if self.current_character:
            data_dir = get_data_dir()
            data_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / "last_character.json").write_text(json.dumps(asdict(self.current_character), indent=2))

    def save_session(
        self,
        history: List[dict],
        embodiment: Optional[EmbodimentState] = None,
        archive_path: Optional[Path] = None,
    ):
        """Persist the current character + conversation + embodiment state."""
        if not self.current_character:
            return
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now().isoformat()
        payload = {
            "character": asdict(self.current_character),
            "history": history[-SESSION_SAVE_HISTORY_LIMIT:],
            "embodiment": (embodiment.as_dict() if embodiment else {}),
            "saved_at": now,
            "last_played": now,
            "archive_path": str(archive_path) if archive_path else None,
        }
        (data_dir / "last_session.json").write_text(json.dumps(payload, indent=2))

        if archive_path:
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            archive_path.write_text(json.dumps(payload, indent=2))

    def _load_session_payload(self, path: Path) -> Optional[tuple[Character, List[dict], EmbodimentState, Optional[Path]]]:
        try:
            payload = json.loads(path.read_text())
            char = Character(**payload["character"])
            hist = payload.get("history", [])
            emb = EmbodimentState.from_dict(payload.get("embodiment"))
            archive_raw = payload.get("archive_path")
            archive_path = Path(archive_raw) if archive_raw else path
            if archive_path and not archive_path.exists():
                archive_path = path
            return char, hist, emb, archive_path
        except Exception as exc:
            log_error(f"load_session:{path}", exc)
            return None

    def load_session(self) -> Optional[tuple[Character, List[dict], EmbodimentState, Optional[Path]]]:
        data_dir = get_data_dir()
        path = data_dir / "last_session.json"
        if not path.exists():
            return None
        return self._load_session_payload(path)

    def list_past_sessions(self, limit: int = 8) -> list[dict]:
        """Return recent sessions for the history browser (name, saved_at, path)."""
        data_dir = get_data_dir()
        sessions = []
        try:
            for p in sorted(data_dir.glob("session_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
                try:
                    data = json.loads(p.read_text())
                    char_data = data.get("character", {})
                    name = char_data.get("name", "Unnamed")
                    saved = data.get("saved_at", "")
                    sessions.append({
                        "name": name,
                        "saved_at": saved,
                        "path": str(p),
                        "vessel": char_data.get("vessel", ""),
                    })
                except Exception:
                    continue
        except Exception:
            pass
        return sessions

    def load_specific_session(self, path: str) -> Optional[tuple[Character, List[dict], EmbodimentState, Optional[Path]]]:
        """Load a specific timestamped session file."""
        p = Path(path)
        if not p.exists():
            return None
        return self._load_session_payload(p)

    def refresh_session_ui(self):
        """Refresh the active SessionScreen UI after reallocation (sidebar, table, influences, etc.)."""
        if self.screen_stack:
            top = self.screen_stack[-1]
            if isinstance(top, SessionScreen):
                top.refresh_character_ui()

if __name__ == "__main__":
    if litellm is None:
        print("WARNING: litellm not installed. LLM features will not work.")
        print("Install with: pip install litellm  (or via the venv instructions above)")
    else:
        print("Offline tip: Install Ollama (https://ollama.com) and use a model like 'ollama/llama3.2:3b' with blank API key for fully local play. A basic simulator will be used if no model is available.")
    EgressApp().run()