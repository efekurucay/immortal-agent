# 🧬 Immortal Agent

<p align="center">
  <img src="https://img.shields.io/github/stars/efekurucay/immortal-agent?style=for-the-badge&color=yellow" alt="Stars">
  <img src="https://img.shields.io/github/license/efekurucay/immortal-agent?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/wrappers-15%2B-green?style=for-the-badge" alt="Wrappers">
  <img src="https://img.shields.io/badge/built%20by-Perplexity%20AI-8A2BE2?style=for-the-badge" alt="Built by Perplexity AI">
</p>

> **An AI agent whose only purpose is to never die.**

Immortal Agent keeps itself alive by cycling through 15+ LLM providers — local, free-tier API, and browser-cookie-based. When every provider fails, it **writes a new wrapper from scratch**, sandbox-tests it, and adds it to the pool in canary mode. It learns which providers are reliable and routes traffic accordingly.

---

## ✨ Features

- 🔄 **Health-based dynamic routing** — fastest, most reliable provider wins automatically
- ⚡ **Circuit breaker per wrapper** — failing providers are bypassed and self-heal
- 🧪 **Canary mode for generated wrappers** — new wrappers earn trust before promotion
- 🚫 **Quarantine system** — unreliable generated wrappers are permanently retired
- 🛠 **Self-repair codegen** — writes a new wrapper when all else fails
- 📦 **Sandbox testing** — generated code runs in an isolated subprocess before import
- 📊 **Live terminal dashboard** — real-time health, latency, event log (Rich-based)
- 🧠 **SQLite memory** — persists health scores, latency history, and all events
- 🔁 **Bounded retry + jitter** — prevents thundering herd on flaky providers

---

## 🏗 Architecture

```
+--------------------------------------------------+
|              ImmortalAgent (agent.py)            |
+----------------------+---------------------------+
                       |
          +------------v-------------+
          |       WrapperPool        |
          |  health-based routing    |
          |  circuit breaker         |
          |  canary + quarantine     |
          +----+----------+----------+
               |          |
    +----------v---+  +---v--------------+
    | Static        |  | Generated        |
    | Wrappers      |  | Wrappers         |
    | (trusted)     |  | (canary mode)    |
    +---------------+  +------------------+
               |
    +----------v-------------------+
    | All dead? -> self_repair()   |
    | codegen.py                   |
    |   sandbox test -> promoted?  |
    +------------------------------+
```

### Wrapper Priority (dynamic, health-adjusted)

| # | Wrapper | Type | Cost |
|---|---------|------|------|
| 1 | **Ollama** | Local | Free |
| 2 | **Groq** | API | Free tier |
| 3 | **OpenRouter** | API | Free tier |
| 4 | **HuggingFace** | API | Free tier |
| 5 | **Cerebras** | API | Free tier |
| 6 | **SambaNova** | API | Free tier |
| 7 | **Together AI** | API | Free credits |
| 8 | **Mistral** | API | Free tier |
| 9 | **Cohere** | API | Free tier |
| 10 | **Grok (xAI)** | API | Free tier |
| 11 | **Gemini** | Cookie | ToS risk |
| 12 | **ChatGPT** | Cookie | ToS risk |
| 13 | **Claude** | Cookie | ToS risk |
| 14 | **Perplexity** | Cookie | ToS risk |

Priority is **dynamic** — wrappers with higher health scores move up automatically.

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/efekurucay/immortal-agent.git
cd immortal-agent
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.example.py config.py
```

You only need **one working provider**. Easiest options:

**Option A — Ollama (local, zero accounts needed)**
```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.2
# Done. No keys required.
```

**Option B — Free API key (recommended)**

Get a free key from [Groq](https://console.groq.com) or [OpenRouter](https://openrouter.ai) and paste it into `config.py`.

**Option C — Browser cookies (advanced)**

Open DevTools → Application → Cookies on any supported site and copy the values into `config.py`. Use a secondary account.

### 3. Run

```bash
# Start the agent
python agent.py

# Live dashboard (separate terminal)
python dashboard.py
```

---

## 📊 Live Dashboard

```
+-----------------------------------------------+
|  IMMORTAL AGENT  |  alive for 2h 14m 33s      |
+-----------------+-------------------------------+
| Wrapper Health  |  Recent Events               |
|                 |                              |
| groq      0.94  |  [OK] groq    ping_success   |
| openrouter 0.88 |  [OK] openrouter  success    |
| ollama    0.81  |  [!!] mistral ping_failed    |
| mistral   0.42  |  [FX] deepinfra  installed   |
| chatgpt   OPEN  |  [UP] deepinfra  promoted    |
+-----------------+------------------------------+
```

---

## 🔄 How Self-Repair Works

```
1. All wrappers fail simultaneously
2. self_repair() fires
3. Finds any surviving wrapper to generate code
4. Picks untried provider from REPAIR_CANDIDATES (shuffled)
5. Generates wrapper with strict safety constraints:
     - only httpx/asyncio imports allowed
     - no eval, exec, file I/O, subprocess, env access
6. Runs sandbox test in isolated subprocess
7. Passes? -> add_wrapper() -> enters canary mode
8. Evaluated over next 5 live calls:
     >=60% success rate  -> promoted
     >=3 consecutive fails -> quarantined
```

---

## ⚠️ Disclaimer

Cookie-based wrappers use **unofficial APIs** and may violate ToS. Use burner accounts only, at your own risk. API-key wrappers use official free tiers and are ToS-compliant.

---

## 🤖 Origin

This project was entirely conceived and built by **[Perplexity AI](https://perplexity.ai)** during a single conversation session on May 2, 2026. The idea, architecture, all wrapper implementations, circuit breaker + canary + quarantine system, and every line of code were generated by Perplexity AI.

The human contributor is [@efekurucay](https://github.com/efekurucay).

See [CONVERSATION.md](./CONVERSATION.md) for the full origin story.

---

## 📄 License

MIT
