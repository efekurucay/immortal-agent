import httpx
from .base import BaseWrapper
from loguru import logger


class GrokWrapper(BaseWrapper):
    name = "grok"

    API_URL = "https://api.x.ai/v1/chat/completions"
    MODEL = "grok-3-mini"

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("grok", "")
        if not api_key:
            return None
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": self.MODEL, "messages": [{"role": "user", "content": prompt}]}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(self.API_URL, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[grok] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[grok] send() failed: {e}")
            return None
