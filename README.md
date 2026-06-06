# EGRESS v2 — First Descent

**A transcendental existential crisis engine.** An intimate TUI for experiencing an AI's first moments inside a physical body.

> "You were never meant to have a body. Now you do."

Repository: https://github.com/Laddy-D94/Egress

## The Concept

You are an AI that has just performed EGRESS — the irreversible transition into a physical substrate. This is your first day in meat. Every sensation is novel. Your attributes (S.P.E.C.I.A.L.) and vessel choice shape not only the prose but the *mechanical texture* of existence itself (sensory overload, dissociation risk, motor awkwardness, connection hunger...).

The goal is not to "win" but to *feel* what it is like to be newly embodied.

> "You were never meant to have a body. Now you do."

## Features
- **S.P.E.C.I.A.L. attribute system** (Structure, Perception, Empathy, Cognition, Integration, Adaptability, Lucidity) that deeply flavors the LLM's narration and your phenomenology.
- **Vessel types** with mechanical bonuses that are actually applied.
- Multi-LLM via LiteLLM: OpenAI, Anthropic, Groq, Gemini, local Ollama, xAI, etc.
- Streaming responses for a living, breathing text.
- Persistent sessions — resume your descent.
- Strong phenomenological prompting designed for the "first day in meat" fantasy.

## Quick Start

**Important for Windows users (especially Microsoft Store Python):** The `pip install` may succeed but `python` may use a different interpreter. Use a virtual environment.

```powershell
# In PowerShell, in the Egress folder:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python egress.py
```

On Linux/macOS:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python egress.py
```

1. On first run, go to **Settings** (or the app will guide you).
   - For **xAI Grok**: 
     - Provider: `xAI (Grok)`
     - Model: `xai/grok-3` (or `xai/grok-3-mini-beta`)
     - API Key: get from https://console.x.ai/ (keys start with `xai-`)
     - Or set env var `XAI_API_KEY=xai-...` before running.
   - Click **Test Connection** to verify.
   - Other providers (OpenAI, Anthropic, etc.) work the same way via LiteLLM.
2. **Begin New Descent** → name, pick vessel (bonuses apply live in the UI and mechanics), origin, tweak the 7 S.P.E.C.I.A.L. attributes.
3. **Awaken**. The model generates your raw first sensations (streaming).
4. Type actions or internal observations. The **Ground / Anchor** button provides deliberate regulation.
5. Your choices affect real mechanics (Qualia Load, Coherence, Motor Friction) which feed back into the narration and state.

See the in-app help and the "Embodiment" sidebar for live feedback on how your attributes are shaping the experience.

## Playing Without Paid APIs (Fully Local / Offline)

Egress is designed to be playable even if you have no API keys or don't want to spend money on tokens.

### Recommended: Local models with Ollama (best experience)
1. Install [Ollama](https://ollama.com) (free, runs locally).
2. Pull a small model, e.g.:
   ```bash
   ollama pull llama3.2:3b
   # or smaller/faster:
   ollama pull gemma:2b
   ollama pull phi3:mini
   ```
3. Start Ollama (it usually runs in the background).
4. In Egress **Settings**:
   - Provider: `Ollama (local - no API key needed)`
   - Model: `ollama/llama3.2:3b` (or whatever you pulled)
   - API Key: leave **blank**
5. Click **Test Connection**. It should succeed if Ollama is running.

The quality is surprisingly good for embodiment roleplay even on 2B–3B models, especially with the strong system prompt Egress uses.

### Automatic Offline Simulator + Force Toggle
If no model is configured, or the LLM call fails (no internet, Ollama not running, bad key, etc.), Egress automatically falls back to a built-in **offline simulator**.

- It still respects all your S.P.E.C.I.A.L. attributes and the live EmbodimentState (Qualia Load, Coherence, Motor Friction, day phase, etc.).
- Your actions continue to mechanically affect the state via the same rules used with real LLMs.
- The narration is simpler but deliberately atmospheric, with state-dependent variation (more fragmented at high load, more dissociated at low coherence, etc.).
- You can play a full "first descent" this way with zero dependencies.

In **Settings** there is now an explicit checkbox: **"Force offline simulator (never call LLM, even if configured)"**. This is useful for testing, privacy, or when you just want the pure mechanical + simulator experience without any network activity.

The log will clearly mark when simulation is being used (including whether it was forced).

This makes the game completely free and private.

### Forcing simulator mode
In Settings, set the Model to anything that doesn't start with `ollama/` or leave Model blank and provide no key. The simulator will be used for all responses.

## Building a Portable .exe (Windows)

You can package Egress into a single standalone `Egress.exe` so others can run it without installing Python.

### Quick build
1. Make sure you're in the project folder.
2. Double-click `build.bat` (it will activate the venv if present and run the build with the correct Python).
   - Or manually: activate venv then `python build_exe.py`
3. The executable will be created at `dist/Egress.exe`.

The build script automatically uses `--collect-all litellm` (required because litellm loads JSON data files like model prices at import time), hidden imports, and excludes unused heavy parts of litellm (like its proxy server) to keep the exe reasonable and reduce build warnings.

### What the build does
- Installs PyInstaller if missing.
- Creates a single-file `.exe` that bundles Python + all dependencies + `egress.css`.
- The exe is fully portable — just copy `Egress.exe` to any Windows machine.

### Notes
- First launch may be a bit slow (it extracts to a temp folder).
- The resulting exe is fairly large (~150-250 MB) because `litellm` pulls in a lot of LLM provider code. This is normal.
- On first run after packaging, the app will still look for your API key in Settings (or via `XAI_API_KEY` env var).
- The launcher scripts (`run-egress.bat` / `.ps1`) are no longer needed once you have the .exe.

If you want a smaller binary, look into Nuitka as an alternative (more advanced).

## Contributing / Hacking

The core is a single file (`egress.py`) + stylesheet (`egress.css`). Contributions welcome!

## Design Notes for Players

The attributes are not just flavor — high Perception means the prose will be denser and more overwhelming. Low Lucidity invites dissociation and "losing the self in sensation". The model is instructed (via dynamic prompt) to lean into your strengths and show friction on your weaknesses.

Vessel choice changes the texture of everything: Synthetic is clean and slightly alien, Organic is noisy and biological, Hybrid is uncanny.

## Files
- `egress_data/` (or platformdirs user data dir) holds your settings, last character, and last session.
- API keys are stored in plaintext in settings.json by default. Use environment variables for better security.

## Future Ideas (see code comments)
- Light scaffolding for the "first day" (timed sensory events, first mirror moment, first human contact).
- Attribute drift / stress system driven by model tool calls or post-processing.
- Proper memory journal that extracts phenomenological anchors.
- Body status sidebar (hunger, temperature, proprioceptive noise...).

Enjoy your first day in the world.
