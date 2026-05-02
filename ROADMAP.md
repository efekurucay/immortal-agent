# 🗺️ immortal-agent — 2-Year Roadmap (2026–2027)

> Maintained by [@efekurucay](https://github.com/efekurucay)  
> Built by [Perplexity AI](https://perplexity.ai)  
> Last updated: May 2026

This roadmap is organized into 4 quarters per year. Each task is tagged with a priority:
- 🔴 **Critical** — core survivability / correctness
- 🟠 **High** — meaningful capability upgrade
- 🟡 **Medium** — quality of life, observability, polish
- 🟢 **Low** — experimental / future-facing

---

## 📅 2026 — Q2 (May–June): Foundation Hardening

> Theme: **Make what exists production-grade before adding anything new.**

### Core Engine
- [ ] 🔴 Fix `wrapper_pool.py` — ensure `WrapperState.success_rate()` is never called on a wrapper with zero calls (divide-by-zero guard)
- [ ] 🔴 Add `asyncio.timeout()` guard to every wrapper `send()` call — currently some wrappers can hang indefinitely
- [ ] 🔴 Ensure `circuit_breaker` state is persisted to SQLite across restarts (currently in-memory only)
- [ ] 🔴 Write unit tests for circuit breaker state transitions: `closed → open → half_open → closed`
- [ ] 🔴 Write unit tests for `WrapperPool.send_with_fallback()` with mock wrappers
- [ ] 🟠 Add `wrapper.name` uniqueness enforcement in `ALL_WRAPPERS` — duplicate names silently break routing
- [ ] 🟠 Replace bare `except Exception` blocks in all wrappers with typed exception handling (`httpx.TimeoutException`, `httpx.HTTPStatusError`, etc.)
- [ ] 🟠 Add `httpx.AsyncClient` connection pooling — currently a new client is created per call
- [ ] 🟡 Add `pytest` + `pytest-asyncio` to `requirements.txt` and `pyproject.toml`
- [ ] 🟡 Add GitHub Actions CI: run `pytest tests/` on every push to `main`
- [ ] 🟡 Add `ruff` linter to CI pipeline

### Self-Repair Pipeline
- [ ] 🔴 Add import whitelist enforcement in sandbox test — currently only checks class structure, not imports
- [ ] 🔴 Add resource limits to sandbox subprocess (`ulimit` / `resource` module): max 30s CPU, max 128MB RAM
- [ ] 🟠 Add deduplication: before generating a new wrapper, check if an identical endpoint already exists in `wrappers/` or quarantine list
- [ ] 🟠 Store generated wrapper source in SQLite alongside its canary metrics — currently only the file is saved
- [ ] 🟡 Add structured prompt versioning for codegen prompts — log which prompt template produced which wrapper

### Config & Security
- [ ] 🔴 Move all secrets from `config.py` to `.env` — add `python-dotenv` to requirements
- [ ] 🔴 Add `.env.example` and update `.gitignore` to exclude `.env`
- [ ] 🔴 Remove `config.py` from git history (if any real keys were ever committed)
- [ ] 🟠 Add Pydantic v2 config validation — catch missing/malformed keys at startup, not at first call
- [ ] 🟡 Add startup banner showing which wrappers have valid keys configured

---

## 📅 2026 — Q3 (July–September): Observability & Intelligence

> Theme: **If you can't measure it, you can't improve it.**

### Metrics & Logging
- [ ] 🔴 Add `latency_ms`, `success` (bool), `error_kind` columns to SQLite `events` table
- [ ] 🟠 Implement rolling window aggregation helpers: `success_rate_1h()`, `p95_latency_24h()` per wrapper
- [ ] 🟠 Add composite health score formula using: success rate (40%), latency (30%), error rate (20%), circuit state (10%)
- [ ] 🟠 Expose `/metrics` endpoint in `api.py` (Prometheus-compatible text format)
- [ ] 🟡 Add structured JSON logging via `loguru` — every event has `trace_id`, `wrapper`, `latency_ms`, `health_score_delta`
- [ ] 🟡 Add log rotation: keep last 7 days, max 100MB
- [ ] 🟡 Add `--log-level` CLI flag

### Live Dashboard
- [ ] 🟠 Rewrite `dashboard.py` using `rich.live.Live` — auto-refresh every 1 second without flickering
- [ ] 🟠 Add latency sparkline per wrapper (last 20 calls as ASCII chart)
- [ ] 🟠 Add circuit breaker state indicator: `●` closed, `○` open, `◑` half-open
- [ ] 🟡 Add "event log" panel: last 20 events with timestamp, wrapper, outcome
- [ ] 🟡 Add uptime counter: `Alive for Xh Ym Zs`
- [ ] 🟡 Add `--no-color` flag for CI/pipe environments
- [ ] 🟢 Add optional web dashboard (`fastapi` + `htmx`) — real-time SSE updates

### Memory & Learning
- [ ] 🟠 Implement time-of-day bucketed success rates — store hour-of-day in events table
- [ ] 🟠 Add `WrapperPool` warm-start: on startup, load last known health scores from SQLite and skip cold-start penalty
- [ ] 🟡 Add anomaly detection: flag wrappers whose latency suddenly spikes >3x their 24h average
- [ ] 🟡 Add "stickiness" parameter: if current wrapper is healthy, skip re-ranking for N calls to reduce thrash
- [ ] 🟢 Research: can we use a tiny local model (via Ollama) to predict which wrapper will succeed based on time + query type?

---

## 📅 2026 — Q4 (October–December): Ecosystem Integration

> Theme: **Become a standard building block for the agent ecosystem.**

### MCP & Protocol
- [ ] 🔴 Complete `mcp_server.py` integration tests — verify `initialize`, `tools/list`, `tools/call` against real MCP clients
- [ ] 🔴 Add `mcp_server.py` to README with Claude Desktop + Cursor config examples
- [ ] 🟠 Add `streamable-http` transport option to MCP server (alongside stdio)
- [ ] 🟠 Implement MCP `resources` endpoint — expose wrapper health as a live resource
- [ ] 🟠 Submit to [MCP Registry](https://github.com/modelcontextprotocol/servers) as community server
- [ ] 🟡 Add `agents.json` validator CI step — verify schema on every push
- [ ] 🟡 Add `llms.txt` auto-updater script — regenerate from current wrapper list

### REST API
- [ ] 🟠 Build `api.py` — FastAPI app with `POST /send`, `GET /health`, `GET /metrics`
- [ ] 🟠 Add streaming support: `POST /stream` returns SSE token-by-token for wrappers that support it
- [ ] 🟠 Add API key auth (optional, for self-hosted deployments)
- [ ] 🟡 Add OpenAPI auto-generation from FastAPI — replace hand-written `openapi.yaml`
- [ ] 🟡 Add Docker image: `ghcr.io/efekurucay/immortal-agent:latest`
- [ ] 🟡 Add `docker-compose.yml` with SQLite volume mount
- [ ] 🟢 Publish to PyPI as `immortal-agent` package — `pip install immortal-agent`

### New Wrappers
- [ ] 🟠 Add `AzureOpenAIWrapper` — enterprise users
- [ ] 🟠 Add `AnthropicWrapper` (official SDK, not cookie) — `claude-haiku-3-5` free tier
- [ ] 🟠 Add `ReplicateWrapper` — supports many open models
- [ ] 🟡 Add `AI21Wrapper` — Jamba free tier
- [ ] 🟡 Add `PerplexityAPIWrapper` (official API, not cookie)
- [ ] 🟡 Add `NvidiaWrapper` — NIM free API
- [ ] 🟢 Add `GeminiLiveWrapper` — multimodal, streaming
- [ ] 🟢 Research: Cloudflare Workers AI free tier wrapper

---

## 📅 2027 — Q1 (January–March): Distributed Mode

> Theme: **One node is never enough. Immortal means distributed.**

### Multi-Node
- [ ] 🔴 Design gossip protocol for health score sharing between multiple immortal-agent instances
- [ ] 🟠 Add Redis-backed shared health store (optional, falls back to SQLite if no Redis)
- [ ] 🟠 Implement leader election: one node coordinates wrapper generation, others consume
- [ ] 🟠 Add node discovery via `ntfy.sh` (uses agent-write-apis internally — dogfooding)
- [ ] 🟡 Add `--cluster-id` flag — multiple clusters, isolated state
- [ ] 🟡 Build cluster status dashboard — shows all nodes + their health scores
- [ ] 🟢 Research: libp2p / gossipsub for fully decentralized node mesh

### Reliability
- [ ] 🔴 Add automated chaos testing: randomly kill wrappers in CI and verify agent survives
- [ ] 🔴 Add integration test: start agent, kill top 5 wrappers, verify fallback works in <5s
- [ ] 🟠 Add SLO tracking: 99.9% uptime target, auto-alert via ntfy.sh if breached
- [ ] 🟠 Add replay testing: take SQLite event log from production, replay against test pool, verify same routing decisions
- [ ] 🟡 Add `--dry-run` mode: simulate wrapper calls without actually hitting providers

---

## 📅 2027 — Q2 (April–June): Agent-Native Features

> Theme: **immortal-agent becomes a first-class agent framework primitive.**

### Agentic Capabilities
- [ ] 🟠 Add `task_queue.py` — agents can submit tasks, immortal-agent executes them with retries
- [ ] 🟠 Add `memory_retrieval` tool to MCP server — expose SQLite event history as searchable memory
- [ ] 🟠 Add `generate_wrapper` as MCP tool — other agents can trigger wrapper generation
- [ ] 🟠 Add multi-turn conversation support: `POST /conversation` maintains context across calls
- [ ] 🟡 Add `routing_hints` in request body: callers can hint preferred provider or forbidden providers
- [ ] 🟡 Add cost tracking: estimate token cost per call, expose in `/metrics`
- [ ] 🟢 Add `tool_use` pass-through: forward function-calling requests to providers that support it
- [ ] 🟢 Research: can immortal-agent route by capability? (e.g., "needs vision", "needs code execution")

### Self-Evolution
- [ ] 🟠 Add automated wrapper benchmarking: weekly cron that tests all wrappers against standard prompts, stores results
- [ ] 🟠 Add wrapper auto-deprecation: if a wrapper fails >95% of calls for 7 days, move to GRAVEYARD automatically
- [ ] 🟡 Add wrapper auto-update: detect API version changes via changelog scraping, trigger codegen for new endpoint
- [ ] 🟢 Research: can a fine-tuned model improve wrapper generation quality over time using past successes/failures as training data?

---

## 📅 2027 — Q3 (July–September): Production Hardening

> Theme: **Ready for production workloads. Not just a PoC.**

### Performance
- [ ] 🔴 Benchmark: target <100ms p95 overhead (routing logic, not provider latency)
- [ ] 🟠 Add connection pooling at pool level — share `httpx.AsyncClient` instances across wrapper calls
- [ ] 🟠 Add response caching layer: identical prompts within 60s return cached response (opt-in)
- [ ] 🟠 Implement hedged requests: for latency-critical calls, fire 2 providers simultaneously, return first
- [ ] 🟡 Add `uvloop` support — replace default asyncio event loop for better throughput
- [ ] 🟡 Profile and optimize SQLite write path — batch inserts for high-throughput scenarios

### Security
- [ ] 🔴 Security audit of generated wrapper sandbox — ensure no escape path exists
- [ ] 🔴 Add rate limiting to REST API — prevent abuse of self-hosted instances
- [ ] 🟠 Add input sanitization: strip prompt injections before forwarding to providers
- [ ] 🟠 Add `ALLOWED_WRAPPERS` allowlist config — operators can restrict which providers are used
- [ ] 🟡 Add audit log: every API call logged with caller IP (for self-hosted)
- [ ] 🟡 Add secret scanning in CI — ensure no keys are ever committed

---

## 📅 2027 — Q4 (October–December): v2.0 & Community

> Theme: **Ship v2.0. Build a community around it.**

### v2.0 Release
- [ ] 🔴 Tag `v2.0.0` with: distributed mode stable, REST API stable, MCP server stable, PyPI package published
- [ ] 🔴 Write comprehensive documentation site (MkDocs or Docusaurus)
- [ ] 🔴 Write migration guide from v1.x to v2.0
- [ ] 🟠 Add changelog automation: auto-generate `CHANGELOG.md` from conventional commits
- [ ] 🟠 Add release automation: GitHub Actions publishes to PyPI on tag push
- [ ] 🟡 Add `SECURITY.md` — responsible disclosure policy
- [ ] 🟡 Add `CONTRIBUTING.md` — how to add a new wrapper, how to run tests

### Community
- [ ] 🟠 Submit to Hacker News, Reddit r/LocalLLaMA, r/MachineLearning
- [ ] 🟠 Write blog post: "How we built an LLM router that never dies" (for dev.to / Medium)
- [ ] 🟠 Add `wrapper-submission` GitHub Issue template — community can propose new providers
- [ ] 🟡 Add `good-first-issue` labels for community contributions
- [ ] 🟡 Set up GitHub Discussions for architecture questions
- [ ] 🟢 Research: can immortal-agent be used as the backbone for a decentralized LLM inference network?

---

## 🔢 Summary Stats

| Year | Quarter | Theme | Tasks |
|------|---------|-------|-------|
| 2026 | Q2 | Foundation Hardening | 28 |
| 2026 | Q3 | Observability & Intelligence | 26 |
| 2026 | Q4 | Ecosystem Integration | 27 |
| 2027 | Q1 | Distributed Mode | 18 |
| 2027 | Q2 | Agent-Native Features | 19 |
| 2027 | Q3 | Production Hardening | 18 |
| 2027 | Q4 | v2.0 & Community | 18 |
| **Total** | | | **154 tasks** |

---

## 🧭 North Star

> By end of 2027, immortal-agent is the de-facto resilient LLM inference backend for autonomous agents.
> Any agent that needs to make an LLM call — and cannot afford to fail — uses immortal-agent.
> It runs on a Raspberry Pi, in a Docker container, in a GitHub Action, or as a distributed cluster.
> It never dies.
