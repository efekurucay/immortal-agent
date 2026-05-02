import httpx
from .base import BaseWrapper
from loguru import logger


class HuggingFaceWrapper(BaseWrapper):
    name = "huggingface"

    # Using the serverless Inference API with a freely available model
    MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

    @property
    def API_URL(self):
        return f"https://api-inference.huggingface.co/models/{self.MODEL}/v1/chat/completions"

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("huggingface", "")
        if not api_key:
            logger.warning("[huggingface] No API key configured.")
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 256,
        }
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(self.API_URL, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[huggingface] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[huggingface] send() failed: {e}")
            return None
