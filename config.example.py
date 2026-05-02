# ---------------------------------------------------------------------------
# immortal-agent — configuration example
# Copy to config.py and fill in your keys.
# Keys left empty ("") are simply skipped by the wrapper pool.
# ---------------------------------------------------------------------------

# --- Survival loop ---
PING_INTERVAL   = 60      # seconds between liveness pings
MIN_ALIVE_LENGTH = 10     # minimum char count to consider a response valid

# ---------------------------------------------------------------------------
# API keys  (all optional — fill only what you have)
# ---------------------------------------------------------------------------

# Local
# OLLAMA_MODEL = "llama3"          # override in env or here

# Fastest / free-tier inference
GROQ_API_KEY       = ""
CEREBRAS_API_KEY   = ""
SAMBANOVA_API_KEY  = ""
FIREWORKS_API_KEY  = ""   # https://fireworks.ai
LEPTON_API_KEY     = ""   # https://lepton.ai

# Aggregators
OPENROUTER_API_KEY = ""   # https://openrouter.ai
DEEPINFRA_API_KEY  = ""   # https://deepinfra.com
NOVITA_API_KEY     = ""   # https://novita.ai
NAGA_API_KEY       = ""   # https://naga.ac (community)

# SDK / managed
HUGGINGFACE_TOKEN  = ""
TOGETHER_API_KEY   = ""
MISTRAL_API_KEY    = ""
COHERE_API_KEY     = ""

# Key-based providers
GROK_API_KEY       = ""   # xAI
GEMINI_API_KEY     = ""

# Cookie-based (unofficial — use at your own risk)
CHATGPT_COOKIE     = ""
CLAUDE_COOKIE      = ""
PERPLEXITY_COOKIE  = ""
