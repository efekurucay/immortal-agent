# 🧬 Immortal Agent

A self-sustaining AI agent whose only goal is to **stay alive** — defined as being able to send a prompt and receive a response from at least one LLM service.

If a wrapper dies, the agent writes a new one. If all wrappers die, it tries to recover. As long as it can talk, it lives.

## How It Works

```
[Agent Loop]
  → Try all wrappers in pool
  → Got a response? → alive ✅ → wait → repeat
  → All dead? → ask a living model to write a new wrapper
  → Test new wrapper → if ok → add to pool → continue
  → Still dead? → cooldown → retry
```

## Architecture

```
immortal-agent/
├── agent.py          # Main survival loop
├── wrapper_pool.py   # Manages all wrappers
├── wrappers/
│   ├── base.py       # Abstract base wrapper
│   ├── gemini.py     # Gemini web (cookie-based)
│   ├── chatgpt.py    # ChatGPT web (cookie-based)
│   ├── claude.py     # Claude web (cookie-based)
│   └── perplexity.py # Perplexity web (cookie-based)
├── codegen.py        # Self-repair: writes new wrappers
├── memory.py         # SQLite memory of past events
├── config.py         # Cookies & settings
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

Copy your cookies into `config.py`:

```python
COOKIES = {
    "gemini": {
        "__Secure-1PSID": "YOUR_COOKIE",
        "__Secure-1PSIDTS": "YOUR_COOKIE",
    },
    "chatgpt": {
        "__Secure-next-auth.session-token": "YOUR_COOKIE",
    },
    "claude": {
        "sessionKey": "YOUR_COOKIE",
    },
    "perplexity": {
        "__Secure-next-auth.session-token": "YOUR_COOKIE",
    }
}
```

Run:

```bash
python agent.py
```

## Survival Log

All events are logged to `memory.db` (SQLite) and `agent.log`.

## ⚠️ Disclaimer

This project uses unofficial/reverse-engineered web APIs. Usage may violate each service's Terms of Service. Use at your own risk with secondary accounts.
