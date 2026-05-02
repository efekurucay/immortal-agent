# 💡 The Idea Behind Immortal Agent

**Author:** [@efekurucay](https://github.com/efekurucay)  
**Built with:** Perplexity AI  
**Date:** May 2, 2026

---

## The Core Insight

LLM services apply very different rate limits to their **web UI** versus their **official API**. A web browser session is treated as a human user — far more lenient, far fewer restrictions. The official API, by contrast, has hard quota limits that run out quickly on free tiers.

This observation leads to a natural question: what if an agent authenticated as a web user across multiple services simultaneously? It would be nearly impossible to kill.

---

## The Concept

A **self-preserving agent** with a single fitness criterion:

> Can I send a prompt and receive a text response from at least one LLM?

If yes → alive. If no → fight to recover.

The agent doesn't need to be smart. It doesn't need to reason. It just needs to stay in the conversation.

```
[Survival Loop]
  → try all wrappers
  → got a response? → alive ✅ → sleep → repeat
  → all dead? → ask a surviving model to write a new wrapper
  → install new wrapper → test → continue
  → still dead? → cooldown → retry
```

---

## Why It's Hard to Kill

- **14 services** in the wrapper pool across 3 categories:
  - Local (Ollama) — no rate limits, no auth, always available if running
  - Free official APIs (Groq, Cerebras, SambaNova, OpenRouter, HuggingFace, Together, Mistral, Cohere, Grok)
  - Cookie-based web sessions (Gemini, ChatGPT, Claude, Perplexity)
- **Self-repair**: if all wrappers fail, the agent generates new wrapper code using any surviving model
- **Memory**: SQLite tracks which wrappers die and when, so the agent learns over time
- **Priority ordering**: most reliable services are tried first

---

## Architecture Philosophy

Keep it minimal. The agent's only job is survival — not intelligence, not usefulness, not safety. A single `while True` loop with a clear alive/dead check is more robust than a complex orchestration framework.

The self-repair mechanism is the most interesting part: the agent uses *language* to fix its own ability to use *language*. It asks a working model to write Python code for a new wrapper, installs it dynamically, and adds it to the pool. The agent writes its own immune system.

---

## Timeline

| Time | Milestone |
|---|---|
| 20:28 | Idea sparked by a conversation about LLM rate limits |
| 20:43 | Immortal Agent concept defined |
| 20:45 | Implementation started |
| 20:52 | v1.0 — 11 wrappers, full architecture pushed to GitHub |
| 21:00 | v1.1 — Dashboard, CLI, Grok/Cerebras/SambaNova wrappers, tests added |

**Total time from idea to v1.1: ~32 minutes.**
