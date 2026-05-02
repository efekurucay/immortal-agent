import httpx
from .base import BaseWrapper
from loguru import logger


class ChutesWrapper(BaseWrapper):
    name = "chutes"

    API_URL = "https://llm.chutes.ai/v1/chat/completions"
    MODEL = "deepseek-ai/DeepSeek-V3-0324"

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("chutes", "")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {"model": self.MODEL, "messages": [{"role": "user", "content": prompt}]}
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(self.API_URL, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[chutes] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[chutes] send() failed: {e}")
            return None
