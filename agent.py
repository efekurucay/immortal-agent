import asyncio
from loguru import logger
from config import PING_INTERVAL, COOLDOWN, MAX_REPAIR_ATTEMPTS, SURVIVAL_PROMPT
from wrapper_pool import WrapperPool
from memory import init_db, log_event, get_wrapper_stats
from codegen import generate_wrapper_code, install_wrapper


logger.add("agent.log", rotation="10 MB", retention="7 days")


class ImmortalAgent:
    def __init__(self):
        self.pool = WrapperPool()
        self.alive = False
        self.generation = 0
        self.repair_attempts = 0

    async def survive(self):
        """Core survival loop."""
        await init_db()
        logger.info("🧬 Immortal Agent awakening...")

        while True:
            self.generation += 1
            logger.info(f"--- Generation {self.generation} ---")

            response, source = await self.pool.send_with_fallback(SURVIVAL_PROMPT)

            if response:
                self.alive = True
                self.repair_attempts = 0
                logger.success(f"✅ ALIVE via [{source}]: {response[:80]}")
                await log_event("alive", source, {"generation": self.generation})
                await asyncio.sleep(PING_INTERVAL)

            else:
                self.alive = False
                logger.error("💀 All wrappers dead. Attempting self-repair...")
                await log_event("all_dead", "agent", {"generation": self.generation})

                repaired = await self.self_repair()

                if repaired:
                    logger.success("🔧 Self-repair successful. Resuming.")
                    self.pool.reset_dead()
                else:
                    logger.error(f"😵 Self-repair failed. Cooling down for {COOLDOWN}s...")
                    await log_event("repair_failed", "agent", {"attempts": self.repair_attempts})
                    await asyncio.sleep(COOLDOWN)
                    self.pool.reset_dead()  # try again after cooldown

    async def self_repair(self) -> bool:
        """
        Attempt to recover by asking any living wrapper to generate a new wrapper.
        """
        if self.repair_attempts >= MAX_REPAIR_ATTEMPTS:
            logger.warning("[repair] Max repair attempts reached.")
            return False

        self.repair_attempts += 1

        # Try to find any wrapper still alive for code generation
        self.pool.reset_dead()
        working = await self.pool.get_live_wrapper()

        if not working:
            logger.error("[repair] No working wrapper available for code generation.")
            return False

        # Ask it to generate a new wrapper for a different service
        known_names = {w.name for w in self.pool.wrappers}
        candidates = [
            ("openrouter", "OpenRouter.ai free tier, endpoint: https://openrouter.ai/api/v1/chat/completions"),
            ("groq", "Groq cloud free tier, endpoint: https://api.groq.com/openai/v1/chat/completions"),
            ("mistral", "Mistral AI chat, endpoint: https://chat.mistral.ai"),
            ("cohere", "Cohere web UI, endpoint: https://coral.cohere.com"),
        ]

        for service_name, hints in candidates:
            if service_name in known_names:
                continue

            logger.info(f"[repair] Generating wrapper for: {service_name}")
            code = await generate_wrapper_code(working, service_name, hints)

            if not code:
                continue

            wrapper_class = await install_wrapper(code, service_name)
            if wrapper_class:
                self.pool.add_wrapper(wrapper_class)
                # Test the new wrapper
                new_instance = self.pool.wrappers[-1]
                alive = await new_instance.is_alive()
                if alive:
                    logger.success(f"[repair] New wrapper [{service_name}] is alive!")
                    return True

        return False

    async def status(self):
        stats = await get_wrapper_stats()
        logger.info("=== Wrapper Status ===")
        for s in stats:
            logger.info(f"  {s['name']}: {s['status']} | fails: {s['fail_count']}")


if __name__ == "__main__":
    agent = ImmortalAgent()
    try:
        asyncio.run(agent.survive())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user.")
