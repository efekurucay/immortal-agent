# =============================================================
# IMMORTAL AGENT — CONFIG
# Fill in your browser cookies and/or API keys.
# For cookie-based services: use secondary/burner accounts.
# For API-key-based services: free tiers are sufficient.
# Copy this file to config.py and fill in your credentials.
# =============================================================

COOKIES = {
    "gemini": {
        # https://gemini.google.com → F12 → Application → Cookies
        "__Secure-1PSID": "",
        "__Secure-1PSIDTS": "",
    },
    "chatgpt": {
        # https://chat.openai.com → F12 → Application → Cookies
        "__Secure-next-auth.session-token": "",
    },
    "claude": {
        # https://claude.ai → F12 → Application → Cookies
        "sessionKey": "",
    },
    "perplexity": {
        # https://www.perplexity.ai → F12 → Application → Cookies
        "__Secure-next-auth.session-token": "",
        "pplx_auth": "",
    },
}

API_KEYS = {
    # ── Free / no credit card ──────────────────────────────────────
    "groq":        "",   # https://console.groq.com  (free, very fast)
    "cerebras":    "",   # https://cloud.cerebras.ai  (free, ultra-fast)
    "chutes":      "",   # https://chutes.ai  (free, no key needed — leave blank)
    "scaleway":    "",   # https://console.scaleway.com/iam/api-keys  (free Llama tier)
    "hyperbolic":  "",   # https://app.hyperbolic.xyz  (free tier)
    "klusterai":   "",   # https://kluster.ai  (free tier)
    "aimlapi":     "",   # https://aimlapi.com  (free tier)
    "huggingface": "",   # https://huggingface.co/settings/tokens  (free serverless inference)
    "lepton":      "",   # https://www.lepton.ai  (free endpoints)
    "novita":      "",   # https://novita.ai  (free tier)
    "naga":        "",   # https://naga.ac  (community proxy)

    # ── Aggregators with free tiers ───────────────────────────────
    "openrouter":  "",   # https://openrouter.ai  (free models available)
    "together":    "",   # https://api.together.xyz  (free credits on signup)
    "deepinfra":   "",   # https://deepinfra.com  (free tier)
    "fireworks":   "",   # https://fireworks.ai  (free credits on signup)

    # ── Paid (affordable) ─────────────────────────────────────────
    "sambanova":   "",   # https://cloud.sambanova.ai
    "mistral":     "",   # https://console.mistral.ai
    "cohere":      "",   # https://dashboard.cohere.com

    # ── Paid (used as fallback) ───────────────────────────────────
    "grok":        "",   # https://console.x.ai
}

# ── Ollama (local, no key needed) ─────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "llama3.2"   # Run: ollama pull llama3.2

# ── Timing ────────────────────────────────────────────────────────────────────
# How long to wait between survival pings (seconds)
PING_INTERVAL = 60

# How long to wait before retrying after total failure (seconds)
COOLDOWN = 300

# ── Alive detection ───────────────────────────────────────────────────────────
# Minimum response length to consider a wrapper alive
MIN_ALIVE_LENGTH = 10

# The survival prompt — must be answerable by any LLM
SURVIVAL_PROMPT = "Reply with exactly one sentence confirming you are operational."

# ── Self-repair ───────────────────────────────────────────────────────────────
# Max wrapper self-repair attempts before entering full cooldown
MAX_REPAIR_ATTEMPTS = 3
