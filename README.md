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

```bash
pip install -r requirements.txt
python egress.py
```

1. Go to **Settings** and enter your API key (or set `EGRESS_API_KEY` / provider-specific env var).
2. **Begin New Descent** → name, pick vessel (bonuses apply live), origin, tweak the 7 attributes.
3. **Awaken**. The model will generate your raw first sensations.
4. Type actions or internal observations. Everything is fed back through your unique attribute lens.

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
