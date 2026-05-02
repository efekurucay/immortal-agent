import httpx
from .base import BaseWrapper
from loguru import logger


class TogetherWrapper(BaseWrapper):
    name = "together"

    API_URL = "https://api.together.xyz/v1/chat/completions"
    MODEL = "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("together", "")
        if not api_key:
            logger.warning("[together] No API key configured.")
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(self.API_URL, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[together] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[together] send() failed: {e}")
            return None
