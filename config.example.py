# =============================================================
#  IMMORTAL AGENT - EXAMPLE CONFIG
#  Copy this file to config.py and fill in your credentials.
#
#  You only need ONE working provider to get started.
#  Recommended: start with Ollama (local) or Groq (free key).
# =============================================================


# -------------------------------------------------------------
# BROWSER COOKIES  (optional)
# These use unofficial web APIs. ToS risk. Burner accounts only.
# How to get cookies: DevTools -> Application -> Cookies
# -------------------------------------------------------------
COOKIES = {
    "gemini": {
        "__Secure-1PSID": "YOUR_VALUE_HERE",
        "__Secure-1PSIDTS": "YOUR_VALUE_HERE",
    },
    "chatgpt": {
        "__Secure-next-auth.session-token": "YOUR_VALUE_HERE",
    },
    "claude": {
        "sessionKey": "YOUR_VALUE_HERE",
    },
    "perplexity": {
        "__Secure-next-auth.session-token": "YOUR_VALUE_HERE",
        "pplx_auth": "YOUR_VALUE_HERE",
    },
}


# -------------------------------------------------------------
# API KEYS  (recommended - official free tiers, ToS-compliant)
# Leave empty string "" to disable that wrapper.
# -------------------------------------------------------------
API_KEYS = {
    "groq":         "",   # Free - console.groq.com
    "openrouter":   "",   # Free - openrouter.ai
    "huggingface":  "",   # Free - huggingface.co/settings/tokens
    "together":     "",   # Free credits - api.together.xyz
    "mistral":      "",   # Free - console.mistral.ai
    "cohere":       "",   # Free - dashboard.cohere.com
    "cerebras":     "",   # Free - cloud.cerebras.ai
    "sambanova":    "",   # Free - cloud.sambanova.ai
    "grok":         "",   # Free - console.x.ai
}


# -------------------------------------------------------------
# OLLAMA  (fully local, no account or key needed)
# Install from ollama.com then: ollama pull llama3.2
# -------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "llama3.2"


# -------------------------------------------------------------
# AGENT TUNING
# -------------------------------------------------------------

# Seconds between survival pings when alive
PING_INTERVAL = 60

# Seconds to wait before retrying after total failure
COOLDOWN = 300

# Minimum response length to be considered alive
MIN_ALIVE_LENGTH = 10

# The prompt used to test if a wrapper is alive
SURVIVAL_PROMPT = "Reply with exactly one sentence confirming you are operational."

# Max self-repair attempts before entering cooldown
MAX_REPAIR_ATTEMPTS = 3
