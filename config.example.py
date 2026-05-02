"""
config.example.py — Copy to config.py and fill in your API keys.

Leave a key as "" to skip that provider (the agent will route around it).
At minimum, have 1-2 keys to bootstrap. Ollama works with no key at all.
"""

# ── Timing ────────────────────────────────────────────────────────────────────
PING_INTERVAL: int = 60        # seconds between alive pings
COOLDOWN: int = 120            # seconds to wait after total failure
MAX_REPAIR_ATTEMPTS: int = 5   # max self-repair tries before cooldown

# ── Prompts ───────────────────────────────────────────────────────────────────
SURVIVAL_PROMPT: str = "Reply with exactly: I AM ALIVE"

# ── Misc ──────────────────────────────────────────────────────────────────────
MIN_ALIVE_LENGTH: int = 5

# ── API Keys ──────────────────────────────────────────────────────────────────
# Add keys for any services you want to use. Empty string = skip that provider.
API_KEYS: dict[str, str] = {
    # Local — no key needed
    "ollama": "",

    # Free tier inference
    "groq": "",           # console.groq.com — free, very fast
    "cerebras": "",       # cloud.cerebras.ai — free tier
    "chutes": "",         # chutes.ai — free, no key required even
    "scaleway": "",       # console.scaleway.com — free Llama tier
    "hyperbolic": "",     # app.hyperbolic.xyz — free credits
    "klusterai": "",      # kluster.ai — free tier
    "aimlapi": "",        # aimlapi.com — free tier
    "lepton": "",         # leptonai.com — free
    "naga": "",           # naga.ac — free proxy
    "novita": "",         # novita.ai — free tier
    "fireworks": "",      # fireworks.ai — free credits
    "deepinfra": "",      # deepinfra.com — free tier

    # Aggregators (one key = many models)
    "openrouter": "",     # openrouter.ai — free models available
    "huggingface": "",    # huggingface.co — Serverless Inference API
    "together": "",       # together.ai — free trial credits

    # Paid providers (fallback of last resort)
    "sambanova": "",      # sambanova.ai
    "mistral": "",        # mistral.ai
    "cohere": "",         # cohere.com
    "gemini": "",         # aistudio.google.com
    "chatgpt": "",        # platform.openai.com
    "claude": "",         # console.anthropic.com
    "grok": "",           # console.x.ai
    "perplexity": "",     # perplexity.ai/api
}
