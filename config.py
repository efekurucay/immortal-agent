# =============================================================
# IMMORTAL AGENT — CONFIG
# Fill in your browser cookies for each service.
# Use secondary/burner accounts — not your main accounts.
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

# How long to wait between survival pings (seconds)
PING_INTERVAL = 60

# How long to wait before retrying a dead wrapper (seconds)
COOLDOWN = 300

# Minimum response length to consider alive
MIN_ALIVE_LENGTH = 10

# The survival prompt — must be answerable by any LLM
SURVIVAL_PROMPT = "Reply with exactly one sentence confirming you are operational."

# Max wrapper self-repair attempts before full cooldown
MAX_REPAIR_ATTEMPTS = 3
