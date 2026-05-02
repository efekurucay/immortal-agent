#!/usr/bin/env python3
"""
immortal-agent MCP Server
=========================
Exposes the wrapper pool as an MCP tool server over stdio transport.
Any MCP-compatible agent (Claude Desktop, Cursor, Cline, etc.) can
add this as a tool server and use immortal-agent as its LLM backend.

Usage (add to your MCP client config):
  {
    "mcpServers": {
      "immortal-agent": {
        "command": "python",
        "args": ["mcp_server.py"],
        "cwd": "/path/to/immortal-agent"
      }
    }
  }
"""
import asyncio
import json
import sys

from wrapper_pool import WrapperPool
from wrappers import ALL_WRAPPERS

pool = WrapperPool(ALL_WRAPPERS)


def _write(obj: dict) -> None:
    line = json.dumps(obj)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _read() -> dict | None:
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line.strip())


async def _tool_send(args: dict) -> str:
    prompt = args.get("prompt", "")
    if not prompt:
        return "Error: prompt is required."
    result = await pool.send_with_fallback(prompt)
    return result or "Error: all providers failed."


async def _tool_health(_args: dict) -> dict:
    statuses = {}
    for wrapper_cls in ALL_WRAPPERS:
        name = wrapper_cls.name
        state = pool.states.get(name)
        if state:
            statuses[name] = {
                "state": state.circuit,
                "failures": state.failure_count,
                "success_rate": round(state.success_rate(), 3),
            }
        else:
            statuses[name] = {"state": "unknown"}
    return statuses


TOOLS = {"send": _tool_send, "health": _tool_health}

TOOL_SCHEMAS = [
    {
        "name": "send",
        "description": (
            "Send a prompt to immortal-agent's 19-provider wrapper pool. "
            "Automatically falls back across providers until one responds."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"prompt": {"type": "string"}},
            "required": ["prompt"],
        },
    },
    {
        "name": "health",
        "description": "Returns the live health status of all 19 provider wrappers.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


async def main() -> None:
    while True:
        msg = _read()
        if msg is None:
            break
        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            _write({"jsonrpc": "2.0", "id": msg_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "immortal-agent", "version": "1.1.0"},
            }})
        elif method == "tools/list":
            _write({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOL_SCHEMAS}})
        elif method == "tools/call":
            tool_name = params.get("name")
            handler = TOOLS.get(tool_name)
            if handler is None:
                _write({"jsonrpc": "2.0", "id": msg_id,
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}})
            else:
                result = await handler(params.get("arguments", {}))
                content = result if isinstance(result, str) else json.dumps(result, indent=2)
                _write({"jsonrpc": "2.0", "id": msg_id,
                        "result": {"content": [{"type": "text", "text": content}]}})
        elif method and method.startswith("notifications/"):
            pass
        elif msg_id is not None:
            _write({"jsonrpc": "2.0", "id": msg_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"}})


if __name__ == "__main__":
    asyncio.run(main())
