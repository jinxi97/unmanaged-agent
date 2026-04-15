"""Agent runtime integration — spawns pi-agent as a subprocess."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


async def run_agent(
    *,
    runtime: str,
    model: str,
    system_prompt: str,
    message: str,
    sandbox_url: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Run an agent and yield streamed events.

    Spawns the agent runtime as a subprocess, sends the user message via stdin,
    and yields each line of stdout as a parsed event dict.
    """
    if runtime != "pi-agent":
        yield {"type": "error", "content": {"text": f"Unsupported runtime: {runtime}"}}
        return

    cmd = ["pi-agent", "--model", model]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    if sandbox_url:
        cmd.extend(["--sandbox-url", sandbox_url])

    logger.info("Spawning pi-agent: %s", " ".join(cmd))

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Send the user message and close stdin
        process.stdin.write(json.dumps({"type": "message", "content": message}).encode() + b"\n")
        await process.stdin.drain()
        process.stdin.close()

        # Stream stdout line-by-line
        async for line in process.stdout:
            line = line.decode().strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                yield event
            except json.JSONDecodeError:
                yield {"type": "text", "content": {"text": line}}

        await process.wait()

        if process.returncode != 0:
            stderr = await process.stderr.read()
            logger.error("pi-agent exited with code %d: %s", process.returncode, stderr.decode())
            yield {"type": "error", "content": {"text": f"pi-agent exited with code {process.returncode}"}}

    except FileNotFoundError:
        yield {"type": "error", "content": {"text": "pi-agent binary not found. Make sure it's installed and on PATH."}}
