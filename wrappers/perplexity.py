import httpx
from .base import BaseWrapper
from loguru import logger


class PerplexityWrapper(BaseWrapper):
    name = "perplexity"

    API_URL = "https://api.perplexity.ai/chat/completions"
    MODEL = "sonar"

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("perplexity", "")
        if not api_key:
            return None
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": self.MODEL, "messages": [{"role": "user", "content": prompt}]}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(self.API_URL, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[perplexity] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[perplexity] send() failed: {e}")
            return None
