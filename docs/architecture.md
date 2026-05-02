# Architecture — ImmortalAgent v3.0

## Overview

ImmortalAgent is a self-healing autonomous agent that stays alive as long as at least one LLM provider is reachable. It survives by cycling through a ranked pool of 24 provider wrappers, self-repairing when all known wrappers fail.

```
┌─────────────────────────────────────────────────────────────┐
│                    ImmortalAgent                             │
│                                                             │
│  survive()  ──►  WrapperPool.send_with_fallback()           │
│                      │                                      │
│              ┌───────┴──────────┐                          │
│              │  health router    │  (health.py scores)      │
│              │  circuit breaker  │  (closed/open/half-open) │
│              │  rate budget      │  (rate_budget.py)        │
│              └───────┬──────────┘                          │
│                      │                                      │
│         ┌────────────┼────────────┐                        │
│     Wrapper1    Wrapper2    ...  Wrapper24                  │
│         │            │                                      │
│      memory.py  ←─── record_call()  (SQLite)               │
│                      │                                      │
│              [if all fail]                                  │
│                      │                                      │
│              self_repair()                                  │
│               ├── codegen.py  (generates new wrapper code)  │
│               ├── install_wrapper() (sandbox test)          │
│               ├── canary mode (WrapperPool)                 │
│               └── distributed_recovery.py (peer fallback)  │
└─────────────────────────────────────────────────────────────┘
```

## Components

| File | Role |
|------|------|
| `agent.py` | Main survival loop |
| `wrapper_pool.py` | Health-ordered routing, circuit breaker, canary |
| `health.py` | In-process rolling health windows |
| `rate_budget.py` | Global RPM / token guard |
| `memory.py` | SQLite persistence (events, wrappers, hourly) |
| `codegen.py` | LLM-based new wrapper generation |
| `distributed_recovery.py` | Peer-to-peer wrapper sharing |
| `multi_agent.py` | Multi-shard coordinator |
| `rest_api.py` | FastAPI HTTP interface |
| `dashboard.py` | Live Rich terminal UI |
| `cli.py` | CLI with 10 subcommands |
| `mcp_server.py` | MCP tool server |
| `wrappers/` | 24 provider wrappers |

## Health Scoring

Each wrapper gets a composite score ∈ [0, 1]:

```
health = 0.40 × success_rate_1h
       + 0.30 × latency_score   (1.0 at ≤500ms → 0.0 at ≥8000ms)
       + 0.20 × (1 - error_rate_1h)
       + 0.10 × (1 - rate_limit_signal_5m)
```

The WrapperPool sorts wrappers by health descending before each call.

## Circuit Breaker States

```
CLOSED ──[3 failures]──► OPEN ──[60s timeout]──► HALF_OPEN
   ▲                                                  │
   └──────────[success]──────────────────────────────┘
```

## Multi-Agent Topology

```
Coordinator
  ├── Shard-0 (WrapperPool)
  ├── Shard-1 (WrapperPool)
  └── Shard-2 (WrapperPool)
```

Round-robin routing across healthy shards. If a shard's pool dies,
the coordinator transparently routes to remaining healthy shards.
