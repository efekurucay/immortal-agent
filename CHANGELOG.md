# Changelog

All notable changes to immortal-agent are documented here.

## [3.0.0] — 2026-05-02

### Added
- `health.py` — in-process composite health scoring with rolling time windows (1h/24h success rate, P95 latency, error rate, rate-limit signal)
- `rate_budget.py` — global RPM + token budget singleton to prevent self-DDoS
- `rest_api.py` — FastAPI server: `/health`, `/wrappers`, `/events`, `/ask`, `/metrics`, `/budget`
- `multi_agent.py` — multi-shard `Coordinator` that runs N pools in parallel, routes round-robin
- `distributed_recovery.py` — peer-to-peer recovery: request wrapper code from remote immortal-agent instance
- `dashboard.py` — rewritten as live Rich terminal UI (1s refresh, uptime, health bars, event tail)
- `memory.py` — added `hourly` time-series table, `get_hourly_trend()`, `get_best_wrapper_by_hour()`
- `cli.py` — added subcommands: `multi`, `trend`, `budget`, `dashboard`, `server`
- New wrappers: `scaleway`, `aimlapi`, `hyperbolic`, `chutes`, `klusterai` (5 additional free-tier providers)
- `wrappers/__init__.py` — registry now contains 24 wrappers in priority order
- `requirements.txt` — updated with fastapi, uvicorn, pydantic, typer

### Changed
- `memory.py` — latency formula aligned with `health.py` (decay 500ms–8000ms)
- `wrapper_pool.py` — `_ordered_wrappers` now reads health from DB and sorts dynamically
- `ROADMAP.md` tasks implemented: health router, REST API, multi-agent, distributed recovery, live dashboard, time-series memory, rate budget

## [2.4.0] — 2026-04-xx
- Circuit breaker (closed/open/half-open) per wrapper
- Canary promotion / quarantine for generated wrappers
- Retry + exponential backoff + jitter in `WrapperPool._call_with_retry`
- Structured event log with `latency_ms`, `success`, `health_score` columns
- Self-repair pipeline: `generate_wrapper_code` → `install_wrapper` → canary mode

## [1.0.0] — 2026-05-01
- Initial release: basic survival loop, 11 wrappers, SQLite memory
