import os
import httpx
from wrappers.base import BaseWrapper


class DeepInfraWrapper(BaseWrapper):
    name = "deepinfra"
    _url = "https://api.deepinfra.com/v1/openai/chat/completions"
    _model = "meta-llama/Meta-Llama-3-8B-Instruct"

    async def send(self, prompt: str):
        key = os.environ.get("DEEPINFRA_API_KEY") or ""
        if not key:
            return None
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                self._url,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 64,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
