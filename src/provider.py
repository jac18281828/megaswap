"""Trade on uniswap - swap tokens"""

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

import aiofiles
import yaml
from dotenv import load_dotenv
from web3 import AsyncHTTPProvider, AsyncWeb3

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_web3_provider(rpc_url: str) -> AsyncIterator[AsyncWeb3]:
    """Context manager to get a Web3 provider with a shared session"""
    provider = AsyncHTTPProvider(rpc_url)
    w3 = AsyncWeb3(provider)
    try:
        yield w3
    finally:
        # We don't close the session here as it's shared
        pass


async def load_abi(file_path: str) -> dict:
    """
    Load an ABI from a file.
    """
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        contents = await file.read()
    return json.loads(contents)


def load_env() -> None:
    """
    Load environment variables from a .env file.
    """
    logger.info("Loading environment variables from .env file.")
    load_dotenv(override=True)
    missing_vars = (
        key
        for key in [
            "PRIVATE_KEY",
            "PUBLIC_KEY",
            "RPC_URL",
            "TOKEN_OUT_ADDRESS",
            "TOKEN_OUT_DECIMALS",
            "UNISWAP_ROUTER_ADDRESS",
            "WETH_ADDRESS",
            "WETH_DECIMALS",
        ]
        if key not in os.environ
    )
    missing_vars_list = list(missing_vars)
    if missing_vars_list:
        var_list = ", ".join(missing_vars_list)
        raise ValueError(
            f"Missing required environment variables: {var_list} visit .env"
        )
    logger.info("Environment variables loaded successfully.")


async def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file.
    """
    async with aiofiles.open(file_path, "r") as file:
        contents = await file.read()
    return yaml.safe_load(contents)
