import httpx
from .base import BaseWrapper
from loguru import logger


class DeepInfraWrapper(BaseWrapper):
    name = "deepinfra"

    API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
    MODEL = "meta-llama/Llama-3.2-3B-Instruct"

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("deepinfra", "")
        if not api_key:
            return None
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": self.MODEL, "messages": [{"role": "user", "content": prompt}]}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(self.API_URL, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[deepinfra] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[deepinfra] send() failed: {e}")
            return None
