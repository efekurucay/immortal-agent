import os
import httpx
from wrappers.base import BaseWrapper


class NagaWrapper(BaseWrapper):
    """Naga AC — free-tier OpenAI-compatible community proxy."""

    name = "naga"
    _url = "https://api.naga.ac/v1/chat/completions"
    _model = "gpt-3.5-turbo"

    async def send(self, prompt: str):
        key = os.environ.get("NAGA_API_KEY") or ""
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
