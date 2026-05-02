import asyncio
import random
from loguru import logger

from config import PING_INTERVAL, COOLDOWN, MAX_REPAIR_ATTEMPTS, SURVIVAL_PROMPT
from wrapper_pool import WrapperPool
from memory import init_db, log_event, get_wrapper_stats
from codegen import generate_wrapper_code, install_wrapper


logger.add("agent.log", rotation="10 MB", retention="7 days")


# Extended candidate pool for self-repair code generation.
# Ordered by likelihood of success (free tiers, open endpoints first).
REPAIR_CANDIDATES = [
    ("scaleway",     "Scaleway Generative APIs, endpoint: https://api.scaleway.ai/v1/chat/completions, free tier"),
    ("deepinfra",    "DeepInfra inference, endpoint: https://api.deepinfra.com/v1/openai/chat/completions, free tier"),
    ("fireworks",    "Fireworks AI, endpoint: https://api.fireworks.ai/inference/v1/chat/completions, free tier"),
    ("lepton",       "Lepton AI, endpoint: https://llama3-1-8b.lepton.run/api/v1/chat/completions, free"),
    ("novita",       "Novita AI, endpoint: https://api.novita.ai/v3/openai/chat/completions, free tier"),
    ("naga",         "Naga AI proxy, endpoint: https://api.naga.ac/v1/chat/completions"),
    ("klusterai",    "Kluster.ai, endpoint: https://api.kluster.ai/v1/chat/completions"),
    ("aimlapi",      "AI/ML API, endpoint: https://api.aimlapi.com/v1/chat/completions, free tier"),
    ("hyperbolic",   "Hyperbolic AI, endpoint: https://api.hyperbolic.xyz/v1/chat/completions, free tier"),
    ("chutes",       "Chutes.ai, endpoint: https://llm.chutes.ai/v1/chat/completions, free"),
]


class ImmortalAgent:
    def __init__(self):
        self.pool = WrapperPool()
        self.alive = False
        self.generation = 0
        self.repair_attempts = 0
        # Track which service names we've already tried generating (avoid repeats)
        self._tried_repair: set[str] = set()

    async def survive(self):
        """Core survival loop."""
        await init_db()
        logger.info("\U0001f9ec Immortal Agent awakening...")
        await log_event("agent_start", "agent", details={"version": "2.4"})

        while True:
            self.generation += 1
            logger.info(f"--- Generation {self.generation} ---")

            response, source = await self.pool.send_with_fallback(SURVIVAL_PROMPT)

            if response:
                self.alive = True
                self.repair_attempts = 0
                logger.success(f"\u2705 ALIVE via [{source}]: {response[:80]}")
                await log_event(
                    "alive",
                    source,
                    details={"generation": self.generation},
                )
                await asyncio.sleep(PING_INTERVAL)

            else:
                self.alive = False
                logger.error("\U0001f480 All wrappers dead. Attempting self-repair...")
                await log_event(
                    "all_dead",
                    "agent",
                    details={"generation": self.generation},
                )

                repaired = await self.self_repair()

                if repaired:
                    logger.success("\U0001f527 Self-repair successful. Resuming.")
                else:
                    logger.error(
                        f"\U0001f635 Self-repair failed. "
                        f"Cooling down for {COOLDOWN}s..."
                    )
                    await log_event(
                        "repair_failed",
                        "agent",
                        details={"attempts": self.repair_attempts},
                    )
                    await asyncio.sleep(COOLDOWN)

    async def self_repair(self) -> bool:
        """Attempt to recover by generating a new wrapper via a live model.

        Strategy:
        1. Find any still-live wrapper to act as the code generator.
        2. Pick a candidate service we haven't tried yet from REPAIR_CANDIDATES,
           shuffled to avoid always hammering the same first entry.
        3. Generate code, sandbox-test it, add to pool in canary mode.
        4. Return True as soon as one canary wrapper is successfully added
           (canary will self-evaluate in subsequent survive() ticks).
        """

        if self.repair_attempts >= MAX_REPAIR_ATTEMPTS:
            logger.warning("[repair] Max repair attempts reached. Skipping.")
            return False

        self.repair_attempts += 1

        working = await self.pool.get_live_wrapper()
        if not working:
            logger.error("[repair] No working wrapper available for code generation.")
            return False

        # Build candidate list: exclude already-known names and already-tried ones
        known_names = {w.name for w in self.pool.wrappers}
        candidates = [
            (name, hints)
            for name, hints in REPAIR_CANDIDATES
            if name not in known_names and name not in self._tried_repair
        ]

        if not candidates:
            # Exhausted all known candidates; reset tried set and try again
            logger.warning("[repair] All candidates tried. Resetting tried set.")
            self._tried_repair.clear()
            candidates = [
                (name, hints)
                for name, hints in REPAIR_CANDIDATES
                if name not in known_names
            ]

        # Shuffle to distribute load across candidates
        random.shuffle(candidates)

        for service_name, hints in candidates:
            self._tried_repair.add(service_name)
            logger.info(f"[repair] Generating wrapper for: {service_name}")

            code = await generate_wrapper_code(working, service_name, hints)
            if not code:
                logger.warning(f"[repair] Code generation returned nothing for {service_name}.")
                continue

            wrapper_class = await install_wrapper(code, service_name)
            if wrapper_class is None:
                logger.warning(f"[repair] Sandbox/install failed for {service_name}.")
                continue

            # Hand off to pool — canary mode handles evaluation from here
            self.pool.add_wrapper(wrapper_class)
            logger.success(
                f"[repair] Wrapper [{service_name}] installed in canary mode. "
                f"Will be evaluated over next {5} calls."
            )
            await log_event(
                "self_repair_success",
                service_name,
                details={"generator": working.name, "attempt": self.repair_attempts},
            )
            return True

        return False

    async def status(self):
        stats = await get_wrapper_stats()
        logger.info("=== Wrapper Status ===")
        for s in stats:
            canary = self.pool.canary_status(s["name"])
            tag = f" [{canary}]" if canary else ""
            logger.info(
                f"  {s['name']}{tag}: health={s.get('health_score', 0):.2f} "
                f"| fails={s['fail_count']} | succ={s['success_count']}"
            )


if __name__ == "__main__":
    agent = ImmortalAgent()
    try:
        asyncio.run(agent.survive())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user.")
