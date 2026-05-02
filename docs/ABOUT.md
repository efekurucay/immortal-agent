# immortal-agent 🧬

> A self-healing AI agent that refuses to die.

## What is it?

`immortal-agent` is an autonomous Python agent with one goal: **stay alive**.

It cycles through 14+ LLM providers. When one fails, it tries the next.
When **all** fail, it writes a new wrapper using the last surviving LLM,
sandbox-tests it in a subprocess, then deploys it in canary mode.

## Architecture

```
Agent Loop
  └── WrapperPool (health-scored, circuit-broken)
        ├── OllamaWrapper       (local, no key)
        ├── GroqWrapper         (free API)
        ├── OpenRouterWrapper   (free tier)
        ├── HuggingFaceWrapper  (serverless inference)
        ├── TogetherWrapper     (free credits)
        ├── MistralWrapper      (free tier)
        ├── CohereWrapper       (free tier)
        ├── CerebrasWrapper     (free tier)
        ├── SambanovaWrapper    (free tier)
        ├── GrokWrapper         (xAI free tier)
        ├── GeminiWrapper       (browser cookie)
        ├── ChatGPTWrapper      (browser cookie)
        ├── ClaudeWrapper       (browser cookie)
        └── PerplexityWrapper   (browser cookie)

Self-Repair Pipeline (when all fail)
  └── codegen → subprocess sandbox test → canary deploy → promote/quarantine
```

## Key Features

- **Circuit breaker** per wrapper — auto open/half-open/close
- **Composite health score** — success rate + latency + error rate
- **Retry + exponential backoff + jitter** — bounded retry budget
- **SQLite observability** — every call logged with latency, success, health score
- **Live CLI dashboard** — real-time wrapper status
- **Self-repair** — writes, tests, and deploys its own fallback wrappers

## Quick Start

```bash
git clone https://github.com/efekurucay/immortal-agent
cd immortal-agent
cp config.example.py config.py  # add at least one API key or run Ollama
pip install -r requirements.txt
python main.py
```

You only need **one** working provider. Recommended: start with Ollama (local, free, no account).

## Philosophy

Most AI agents assume the LLM is always available. This one doesn't.
It treats every provider as potentially hostile and builds redundancy at the code level.
When infrastructure fails, the agent repairs the infrastructure.

## Links

- **GitHub:** https://github.com/efekurucay/immortal-agent
- **Author:** https://efekurucay.com

---

*Built entirely by Perplexity AI in a single conversation with [@efekurucay24](https://github.com/efekurucay)*
