import asyncio
from .base import BaseWrapper
from loguru import logger


class GeminiWrapper(BaseWrapper):
    name = "gemini"

    def __init__(self):
        self.client = None

    async def _init_client(self):
        from config import COOKIES
        cookies = COOKIES.get("gemini", {})
        psid = cookies.get("__Secure-1PSID", "")
        psidts = cookies.get("__Secure-1PSIDTS", "")

        if not psid:
            logger.warning("[gemini] No cookie configured.")
            return False

        try:
            from gemini_webapi import GeminiClient
            self.client = GeminiClient(psid, psidts)
            await self.client.init(timeout=30, auto_close=False, auto_refresh=True)
            return True
        except Exception as e:
            logger.error(f"[gemini] Init failed: {e}")
            return False

    async def send(self, prompt: str) -> str | None:
        if self.client is None:
            ok = await self._init_client()
            if not ok:
                return None
        try:
            response = await self.client.generate_content(prompt)
            return response.text if response else None
        except Exception as e:
            logger.error(f"[gemini] send() failed: {e}")
            self.client = None  # force re-init next time
            return None
