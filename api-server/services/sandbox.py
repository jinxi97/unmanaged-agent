"""Sandbox provisioning and command execution for E2B and Daytona."""

import logging
import os

from e2b import AsyncSandbox

logger = logging.getLogger(__name__)

# API keys to forward from server env to sandbox commands.
# At least one must be set for pi-agent to work.
API_KEY_NAMES = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "OPENROUTER_API_KEY",
]


def _get_api_key_envs() -> dict[str, str]:
    """Collect API keys from server environment variables."""
    envs = {}
    for key in API_KEY_NAMES:
        value = os.environ.get(key)
        if value:
            envs[key] = value
    return envs


# --- Public API ---


async def create_sandbox(provider: str, config: dict) -> dict:
    """Provision a sandbox and install pi-agent.

    Returns a dict with {"sandbox_id": ..., "url": ...}.
    """
    if provider == "e2b":
        return await _create_e2b_sandbox(config)
    elif provider == "daytona":
        return await _create_daytona_sandbox(config)
    else:
        raise ValueError(f"Unsupported sandbox provider: {provider}")


async def destroy_sandbox(provider: str, sandbox_id: str):
    """Tear down a sandbox."""
    if provider == "e2b":
        await _destroy_e2b_sandbox(sandbox_id)
    elif provider == "daytona":
        await _destroy_daytona_sandbox(sandbox_id)
    else:
        raise ValueError(f"Unsupported sandbox provider: {provider}")


async def run_command(provider: str, sandbox_id: str, command: str) -> AsyncSandbox:
    """Run a command in an existing sandbox with API keys injected.

    Returns the command result with stdout/stderr.
    """
    if provider == "e2b":
        return await _run_e2b_command(sandbox_id, command)
    elif provider == "daytona":
        raise NotImplementedError("Daytona command execution is not yet implemented")
    else:
        raise ValueError(f"Unsupported sandbox provider: {provider}")


# --- E2B ---


async def _create_e2b_sandbox(config: dict) -> dict:
    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        raise RuntimeError("E2B_API_KEY environment variable is not set")

    sandbox = await AsyncSandbox.create(api_key=api_key)
    logger.info("Created E2B sandbox: %s", sandbox.sandbox_id)

    # Install pi-agent in the sandbox
    result = await sandbox.commands.run("npm install -g @mariozechner/pi-coding-agent")
    if result.exit_code != 0:
        logger.error("Failed to install pi-agent: %s", result.stderr)
        await sandbox.kill()
        raise RuntimeError(f"Failed to install pi-agent in sandbox: {result.stderr}")
    logger.info("Installed pi-agent in sandbox %s", sandbox.sandbox_id)

    return {
        "sandbox_id": sandbox.sandbox_id,
        "url": f"https://{sandbox.sandbox_id}.e2b.dev",
        "provider": "e2b",
    }


async def _destroy_e2b_sandbox(sandbox_id: str):
    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        raise RuntimeError("E2B_API_KEY environment variable is not set")

    sandbox = await AsyncSandbox.connect(sandbox_id, api_key=api_key)
    await sandbox.kill()
    logger.info("Destroyed E2B sandbox: %s", sandbox_id)


async def _run_e2b_command(sandbox_id: str, command: str):
    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        raise RuntimeError("E2B_API_KEY environment variable is not set")

    envs = _get_api_key_envs()
    if not envs:
        raise RuntimeError(
            "At least one API key must be set: " + ", ".join(API_KEY_NAMES)
        )

    sandbox = await AsyncSandbox.connect(sandbox_id, api_key=api_key)
    result = await sandbox.commands.run(command, envs=envs)
    return result


# --- Daytona ---


async def _create_daytona_sandbox(config: dict) -> dict:
    api_key = os.environ.get("DAYTONA_API_KEY")
    if not api_key:
        raise RuntimeError("DAYTONA_API_KEY environment variable is not set")

    # TODO: Implement Daytona sandbox creation via their API
    raise NotImplementedError("Daytona sandbox support is not yet implemented")


async def _destroy_daytona_sandbox(sandbox_id: str):
    api_key = os.environ.get("DAYTONA_API_KEY")
    if not api_key:
        raise RuntimeError("DAYTONA_API_KEY environment variable is not set")

    # TODO: Implement Daytona sandbox teardown via their API
    raise NotImplementedError("Daytona sandbox support is not yet implemented")
