import importlib
import sys
import os
import asyncio
import textwrap
import subprocess
from pathlib import Path

from loguru import logger

from memory import log_event


SAFE_CODEGEN_PROMPT = """
You are an expert Python developer.
Write a new async Python wrapper class for an LLM web service.

HARD REQUIREMENTS (do not violate any of these):
- Single file, pure Python 3.11 compatible.
- Do NOT import anything except: typing, httpx, asyncio.
- Class must extend BaseWrapper (from wrappers.base) but DO NOT import it directly; assume it will be available at runtime.
- The class must be named {class_name} and have a `name` class attribute set to "{service_name}".
- Implement: async def send(self, prompt: str) -> str | None
- Use httpx.AsyncClient for HTTP requests.
- Catch all exceptions and return None instead of raising.
- Do not read or write any files.
- Do not access environment variables.
- Do not spawn subprocesses.
- Do not use eval or exec.
- Do not import or use any crypto, OS, or system libraries.
- No top-level network calls; only inside send().

Target service: {service_name}
Known endpoint hints: {hints}

Return ONLY the Python code for the wrapper class. No explanation. No markdown fences.
"""


async def generate_wrapper_code(working_wrapper, service_name: str, hints: str = "") -> str | None:
    """Ask a working wrapper to generate code for a new wrapper.

    The returned code will be sandbox-tested before being imported.
    """

    class_name = f"{service_name.capitalize()}Wrapper"
    prompt = SAFE_CODEGEN_PROMPT.format(
        service_name=service_name,
        class_name=class_name,
        hints=hints,
    )
    try:
        code = await working_wrapper.send(prompt)
        return code
    except Exception as e:  # noqa: BLE001
        logger.error(f"[codegen] Code generation failed: {e}")
        return None


def _write_temp_wrapper(code: str, wrapper_name: str) -> Path:
    """Write generated code to a temp file under wrappers/ for testing."""

    path = Path("wrappers") / f"{wrapper_name}_generated.py"
    path.write_text(code)
    return path


def _run_sandbox_test(path: Path, class_name: str) -> bool:
    """Run a minimal sandbox test in a separate Python process.

    This verifies that the module imports and that the class exists and is
    awaitable via an async send() method without crashing on a trivial call.
    """

    test_code = textwrap.dedent(
        f"""
        import asyncio
        import importlib
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path('.').resolve()))

        module_name = '{path.with_suffix('').name.replace(os.sep, '.')}'
        mod = importlib.import_module(module_name)
        cls = getattr(mod, '{class_name}')
        inst = cls()

        async def main():
            try:
                # Use a very simple prompt that should not trigger network-heavy work
                result = await inst.send('ping')
            except Exception:
                raise SystemExit(1)

        asyncio.run(main())
        """
    )

    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-c", test_code],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


async def install_wrapper(code: str, wrapper_name: str):
    """Sandbox, install, and return a new wrapper class.

    Steps:
    - Write code to wrappers/{wrapper_name}_generated.py
    - Run a sandbox import + basic send('ping') test in a child process
    - If it passes, import the module in the main process and return the class
    - If anything fails, remove the file and return None
    """

    file_path: Path | None = None
    class_name = f"{wrapper_name.capitalize()}Wrapper"

    try:
        file_path = _write_temp_wrapper(code, wrapper_name)

        ok = _run_sandbox_test(file_path, class_name)
        if not ok:
            logger.error("[codegen] Sandbox test failed for generated wrapper.")
            if file_path and file_path.exists():
                file_path.unlink()
            return None

        # Dynamically import in main process
        module_name = f"wrappers.{wrapper_name}_generated"
        if module_name in sys.modules:
            del sys.modules[module_name]

        module = importlib.import_module(module_name)

        from wrappers.base import BaseWrapper

        attr = getattr(module, class_name, None)
        if (
            isinstance(attr, type)
            and issubclass(attr, BaseWrapper)
            and attr is not BaseWrapper
        ):
            logger.success(f"[codegen] Installed new wrapper: {class_name}")
            await log_event(
                "wrapper_installed",
                wrapper_name,
                details={"class": class_name},
            )
            return attr

        logger.error("[codegen] No valid wrapper class found in generated code.")
        if file_path and file_path.exists():
            file_path.unlink()
        return None

    except Exception as e:  # noqa: BLE001
        logger.error(f"[codegen] Install failed: {e}")
        if file_path and file_path.exists():
            file_path.unlink()
        return None
