# Changelog

All notable changes to **immortal-agent** are documented here.

---

## [2.4] - 2026-05-02

### Changed — `agent.py`
- **`REPAIR_CANDIDATES`** expanded from 4 static entries to 10 diverse free-tier providers
  (Scaleway, DeepInfra, Fireworks, Lepton, Novita, Naga, Kluster.ai, AIML API, Hyperbolic, Chutes).
- **`self_repair()`** now tracks `_tried_repair` set to avoid hammering the same provider;
  resets automatically when all candidates are exhausted.
- Candidates are **shuffled** each repair cycle to distribute load.
- Removed redundant `new_instance.is_alive()` check — canary mode in `wrapper_pool.py`
  handles evaluation transparently over subsequent survive() ticks.
- `repair_attempts` resets on successful `alive` tick.
- `status()` now shows `canary_status` tag and full health/success/fail metrics.
- Logged `agent_start` event with version tag on boot.

---

## [2.3] - 2026-05-02

### Added — `wrapper_pool.py`
- `CanaryState` dataclass tracking probationary period for generated wrappers.
- `add_wrapper(wrapper_class)` — single entry point for dynamically adding wrappers in canary mode.
- `_record_canary()` — auto-promotes or quarantines after CANARY_CALLS observations.
  - Immediate quarantine on ≥3 consecutive failures.
  - Promotion if success_rate ≥ 60% after 5 calls.
- `canary_status(name)` — returns human-readable status for dashboard.
- Quarantined wrappers excluded from `_ordered_wrappers()` and `get_live_wrapper()`.

---

## [2.2] - 2026-05-02

### Changed — `codegen.py`
- Replaced freeform `CODEGEN_PROMPT` with `SAFE_CODEGEN_PROMPT`:
  - Restricts imports to `typing`, `httpx`, `asyncio` only.
  - Forbids `eval`, `exec`, subprocess, file I/O, env access, system libraries.
  - Forces named class pattern `{Service}Wrapper`.
- Added `_run_sandbox_test()` — runs generated code in an isolated subprocess.
  - Import + `cls()` + `await send('ping')` smoke test.
  - Non-zero exit = reject, file deleted.
- `install_wrapper()` now requires sandbox test to pass before main-process import.

---

## [2.1] - 2026-05-02

### Added — `wrapper_pool.py`
- `get_wrapper_stats()` integration for dynamic health-based routing.
- `_ordered_wrappers()` sorts by `(-health_score, static_priority)`.

### Added — `memory.py`
- `latency_ms`, `success`, `health_score` columns in `events` table.
- `success_count`, `fail_count`, `total_latency_ms`, `health_score` in `wrappers` table.
- `record_call()` computes composite health score per wrapper.

### Added — `dashboard.py`
- Full rewrite using Rich `Live` context manager.
- Auto-refreshes every 1 second.
- Wrapper Health table + Recent Events panel.

---

## [2.0] - 2026-05-02

### Added — new wrappers
`groq.py`, `openrouter.py`, `mistral.py`, `cohere.py`, `together.py`,
`huggingface.py`, `ollama.py`, `cerebras.py`, `sambanova.py`, `grok.py`

### Added
- `wrapper_pool.py` with circuit breaker (CLOSED/OPEN/HALF_OPEN), bounded retry + jitter,
  and health-based ordering.
- `memory.py` with SQLite persistence for events and wrapper stats.
- `CONVERSATION.md` documenting the full development session.

---

## [1.0] - 2026-05-02

### Initial release
- `agent.py` survival loop.
- `codegen.py` basic wrapper generation.
- `wrappers/`: `base.py`, `gemini.py`, `chatgpt.py`, `claude.py`, `perplexity.py`.
