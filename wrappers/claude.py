import httpx
import json
import uuid
from .base import BaseWrapper
from loguru import logger


class ClaudeWrapper(BaseWrapper):
    name = "claude"

    BASE_URL = "https://claude.ai/api"

    async def send(self, prompt: str) -> str | None:
        from config import COOKIES
        session_key = COOKIES.get("claude", {}).get("sessionKey", "")
        if not session_key:
            logger.warning("[claude] No cookie configured.")
            return None

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Cookie": f"sessionKey={session_key}",
            "Referer": "https://claude.ai/",
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Create a new conversation
                conv_resp = await client.post(
                    f"{self.BASE_URL}/organizations/unknown/chat_conversations",
                    headers=headers,
                    json={"uuid": str(uuid.uuid4()), "name": ""},
                )

                if conv_resp.status_code not in (200, 201):
                    logger.error(f"[claude] Failed to create conversation: {conv_resp.status_code}")
                    return None

                conv_id = conv_resp.json().get("uuid")
                if not conv_id:
                    return None

                # Send message
                msg_resp = await client.post(
                    f"{self.BASE_URL}/organizations/unknown/chat_conversations/{conv_id}/completion",
                    headers={**headers, "Accept": "text/event-stream"},
                    json={
                        "prompt": prompt,
                        "timezone": "UTC",
                        "attachments": [],
                        "files": [],
                    },
                )

                if msg_resp.status_code != 200:
                    logger.error(f"[claude] Message failed: {msg_resp.status_code}")
                    return None

                result = ""
                for line in msg_resp.text.splitlines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("type") == "completion":
                                result += data.get("completion", "")
                        except Exception:
                            continue
                return result.strip() if result else None

        except Exception as e:
            logger.error(f"[claude] send() failed: {e}")
            return None
