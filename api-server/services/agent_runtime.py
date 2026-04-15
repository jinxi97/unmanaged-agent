"""Agent runtime integration — runs pi-agent inside a sandbox."""

import asyncio
import json
import logging
import os
import shlex
from collections.abc import AsyncGenerator

from e2b import AsyncSandbox

from services.sandbox import API_KEY_NAMES, _get_api_key_envs

logger = logging.getLogger(__name__)


async def run_agent(
    *,
    runtime: str,
    model: str,
    system_prompt: str,
    message: str,
    sandbox_id: str,
) -> AsyncGenerator[dict, None]:
    """Run an agent inside a sandbox and yield streamed events.

    Executes pi-agent in --mode json inside the E2B sandbox,
    streaming each JSON line as an event dict via on_stdout callback.
    """
    if runtime != "pi-agent":
        yield {"type": "error", "content": {"text": f"Unsupported runtime: {runtime}"}}
        return

    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        yield {"type": "error", "content": {"text": "E2B_API_KEY environment variable is not set"}}
        return

    envs = _get_api_key_envs()
    if not envs:
        yield {"type": "error", "content": {"text": "At least one API key must be set: " + ", ".join(API_KEY_NAMES)}}
        return

    # Build the pi-agent command with proper shell escaping
    cmd_parts = [
        "npx", "@mariozechner/pi-coding-agent",
        "--mode", "json",
        "--no-session",
        "-p", shlex.quote(message),
        "--model", shlex.quote(model),
    ]
    if system_prompt:
        cmd_parts.extend(["--system-prompt", shlex.quote(system_prompt)])
    cmd = " ".join(cmd_parts)

    logger.info("Running pi-agent in sandbox %s: %s", sandbox_id, cmd)

    queue: asyncio.Queue[dict | None] = asyncio.Queue()
    line_buffer = ""

    def on_stdout(data):
        nonlocal line_buffer
        line_buffer += data
        while "\n" in line_buffer:
            line, line_buffer = line_buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                queue.put_nowait(event)
            except json.JSONDecodeError:
                queue.put_nowait({"type": "text", "content": {"text": line}})

    def on_stderr(data):
        logger.warning("pi-agent stderr: %s", data.strip())

    try:
        sandbox = await AsyncSandbox.connect(sandbox_id, api_key=api_key)

        # Run the command in a background task so we can yield from the queue
        async def _run():
            try:
                result = await sandbox.commands.run(
                    cmd,
                    envs=envs,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                )
                # Flush any remaining buffer
                if line_buffer.strip():
                    try:
                        event = json.loads(line_buffer.strip())
                        queue.put_nowait(event)
                    except json.JSONDecodeError:
                        queue.put_nowait({"type": "text", "content": {"text": line_buffer.strip()}})

                if result.exit_code != 0:
                    queue.put_nowait({"type": "error", "content": {"text": f"pi-agent exited with code {result.exit_code}"}})
            except Exception as e:
                queue.put_nowait({"type": "error", "content": {"text": f"Sandbox execution error: {e}"}})
            finally:
                queue.put_nowait(None)  # Sentinel to signal completion

        task = asyncio.create_task(_run())

        # Yield events as they arrive
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event

        await task

    except Exception as e:
        logger.error("Error running pi-agent in sandbox %s: %s", sandbox_id, e)
        yield {"type": "error", "content": {"text": f"Sandbox execution error: {e}"}}
