import importlib
import sys
import os
import asyncio
from loguru import logger
from memory import log_event


CODEGEN_PROMPT = """
You are an expert Python developer.
Write a new async Python wrapper class for an LLM web service.

Requirements:
- Class must extend BaseWrapper (from wrappers.base)
- Must have a `name` class attribute (string, lowercase)
- Must implement: async def send(self, prompt: str) -> str | None
- Use httpx.AsyncClient for HTTP requests
- Use only cookie-based auth (no API keys)
- Return None on any failure, never raise
- Be minimal and robust

Target service: {service_name}
Known endpoint hints: {hints}

Return ONLY the Python code. No explanation. No markdown fences.
"""


async def generate_wrapper_code(working_wrapper, service_name: str, hints: str = "") -> str | None:
    """
    Ask a working wrapper to generate code for a new wrapper.
    """
    prompt = CODEGEN_PROMPT.format(service_name=service_name, hints=hints)
    try:
        code = await working_wrapper.send(prompt)
        return code
    except Exception as e:
        logger.error(f"[codegen] Code generation failed: {e}")
        return None


async def install_wrapper(code: str, wrapper_name: str) -> bool:
    """
    Write generated code to disk and dynamically import it.
    Returns True if the new wrapper loads successfully.
    """
    file_path = os.path.join("wrappers", f"{wrapper_name}_generated.py")
    try:
        with open(file_path, "w") as f:
            f.write(code)

        # Dynamically import
        module_name = f"wrappers.{wrapper_name}_generated"
        if module_name in sys.modules:
            del sys.modules[module_name]

        module = importlib.import_module(module_name)

        # Find the class that extends BaseWrapper
        from wrappers.base import BaseWrapper
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseWrapper)
                and attr is not BaseWrapper
            ):
                logger.success(f"[codegen] Installed new wrapper: {attr_name}")
                await log_event("wrapper_installed", wrapper_name, {"class": attr_name})
                return attr  # return the class itself

        logger.error("[codegen] No valid wrapper class found in generated code.")
        return None

    except Exception as e:
        logger.error(f"[codegen] Install failed: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return None
