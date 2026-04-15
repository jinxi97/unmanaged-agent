"""Sandbox provisioning for E2B and Daytona."""

import logging
import os

from e2b import AsyncSandbox

logger = logging.getLogger(__name__)


async def create_sandbox(provider: str, config: dict) -> dict:
    """Provision a sandbox and return connection info.

    Returns a dict with at least {"sandbox_id": ..., "url": ...}.
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


# --- E2B ---


async def _create_e2b_sandbox(config: dict) -> dict:
    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        raise RuntimeError("E2B_API_KEY environment variable is not set")

    sandbox = await AsyncSandbox.create(api_key=api_key)
    logger.info("Created E2B sandbox: %s", sandbox.sandbox_id)
    return {
        "sandbox_id": sandbox.sandbox_id,
        "url": sandbox.get_hostname(),
        "provider": "e2b",
    }


async def _destroy_e2b_sandbox(sandbox_id: str):
    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        raise RuntimeError("E2B_API_KEY environment variable is not set")

    sandbox = await AsyncSandbox.connect(sandbox_id, api_key=api_key)
    await sandbox.kill()
    logger.info("Destroyed E2B sandbox: %s", sandbox_id)


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
