# =============================================================
# IMMORTAL AGENT — CONFIG
# Fill in your browser cookies and/or API keys.
# For cookie-based services: use secondary/burner accounts.
# For API-key-based services: free tiers are sufficient.
# =============================================================

COOKIES = {
    "gemini": {
        "__Secure-1PSID": "",
        "__Secure-1PSIDTS": "",
    },
    "chatgpt": {
        "__Secure-next-auth.session-token": "",
    },
    "claude": {
        "sessionKey": "",
    },
    "perplexity": {
        "__Secure-next-auth.session-token": "",
        "pplx_auth": "",
    },
}

API_KEYS = {
    "openrouter": "",    # https://openrouter.ai
    "groq": "",          # https://console.groq.com
    "mistral": "",       # https://console.mistral.ai
    "cohere": "",        # https://dashboard.cohere.com
    "together": "",      # https://api.together.xyz
    "huggingface": "",   # https://huggingface.co/settings/tokens
    "grok": "",          # https://console.x.ai
    "cerebras": "",      # https://cloud.cerebras.ai
    "sambanova": "",     # https://cloud.sambanova.ai
}

# Ollama local endpoint (no key needed)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

# How long to wait between survival pings (seconds)
PING_INTERVAL = 60

# How long to wait before retrying after total failure (seconds)
COOLDOWN = 300

# Minimum response length to consider alive
MIN_ALIVE_LENGTH = 10

# The survival prompt — must be answerable by any LLM
SURVIVAL_PROMPT = "Reply with exactly one sentence confirming you are operational."

# Max wrapper self-repair attempts before full cooldown
MAX_REPAIR_ATTEMPTS = 3
