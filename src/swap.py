"""Trade on uniswap - swap tokens"""

import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

import aiohttp
from web3 import AsyncHTTPProvider, AsyncWeb3


logger = logging.getLogger(__name__)

# Singleton client session
_CLIENT_SESSION: Optional[aiohttp.ClientSession] = None


# pylint: disable=global-statement
async def get_client_session() -> aiohttp.ClientSession:
    """Get or create a shared client session"""
    global _CLIENT_SESSION
    if _CLIENT_SESSION is None or _CLIENT_SESSION.closed:
        _CLIENT_SESSION = aiohttp.ClientSession()
    return _CLIENT_SESSION


@asynccontextmanager
async def get_web3_provider(rpc_url: str) -> AsyncIterator[AsyncWeb3]:
    """Context manager to get a Web3 provider with a shared session"""
    session = await get_client_session()
    provider = AsyncHTTPProvider(rpc_url)
    await provider.cache_async_session(session)
    w3 = AsyncWeb3(provider)
    try:
        yield w3
    finally:
        # We don't close the session here as it's shared
        pass


def load_abi(file_path: str) -> dict:
    """
    Load an ABI from a file.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
