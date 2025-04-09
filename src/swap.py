"""Trade on uniswap - swap tokens"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiofiles
import yaml
from dotenv import load_dotenv
from web3 import AsyncHTTPProvider, AsyncWeb3

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


TOKEN_FILE = "token.yaml"


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
            "RPC_URL",
            "WETH_ADDRESS",
            "PRIVATE_KEY",
            "PUBLIC_KEY",
            "UNISWAP_ROUTER_ADDRESS",
            "TOKEN_OUT_ADDRESS",
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


async def print_balance(w3: AsyncWeb3, address: str) -> None:
    """
    Print the balance of an address in Ether.
    """
    ck_address = w3.to_checksum_address(address)
    balance = await w3.eth.get_balance(ck_address)
    ether_balance = w3.from_wei(balance, "ether")
    logger.info("Balance of %s: %s ETH", address, ether_balance)


async def print_weth_balance(w3: AsyncWeb3, address: str, weth_address: str) -> None:
    """
    Print the WETH balance of an address.
    """
    erc20_abi = await load_abi("src/abi/IERC20Metadata.json")
    ck_weth_address = w3.to_checksum_address(weth_address)
    weth_contract = w3.eth.contract(address=ck_weth_address, abi=erc20_abi)
    balance = await weth_contract.functions.balanceOf(address).call()
    ether_balance = w3.from_wei(balance, "ether")
    logger.info("WETH Balance of %s: %s WETH", address, ether_balance)


async def print_amount_out(
    w3: AsyncWeb3, amount_in: int, token_in: str, token_out: str, out_base: int
) -> None:
    """
    Print the amount out for a given amount in using Uniswap.
    """
    uniswap_router_abi = await load_abi("src/abi/UniswapV2Router02.json")
    uniswap_router_address = os.getenv("UNISWAP_ROUTER_ADDRESS")
    if not uniswap_router_address:
        raise ValueError("UNISWAP_ROUTER_ADDRESS environment variable is not set.")
    uniswap_router_address = w3.to_checksum_address(uniswap_router_address)
    uniswap_router_contract = w3.eth.contract(
        address=uniswap_router_address, abi=uniswap_router_abi
    )

    ck_token_in = w3.to_checksum_address(token_in)
    ck_token_out = w3.to_checksum_address(token_out)

    amount_out = await uniswap_router_contract.functions.getAmountsOut(
        amount_in, [ck_token_in, ck_token_out]
    ).call()

    logger.info(
        "Amount out for %s %s: %s %s",
        amount_in / 10**18,
        token_in,
        amount_out[-1] / out_base,
        token_out,
    )


async def get_pair(w3: AsyncWeb3, token_a: str, token_b: str) -> bool:
    """
    Get the pair address for two tokens.
    """
    uniswap_factory_abi = await load_abi("src/abi/IUniswapFactoryV2.json")
    uniswap_factory_address = os.getenv("UNISWAP_FACTORY_ADDRESS")
    if not uniswap_factory_address:
        raise ValueError("UNISWAP_FACTORY_ADDRESS environment variable is not set.")
    uniswap_factory_address = w3.to_checksum_address(uniswap_factory_address)
    uniswap_factory_contract = w3.eth.contract(
        address=uniswap_factory_address, abi=uniswap_factory_abi
    )

    ck_token_a = w3.to_checksum_address(token_a)
    ck_token_b = w3.to_checksum_address(token_b)

    pair_address = await uniswap_factory_contract.functions.getPair(
        ck_token_a, ck_token_b
    ).call()

    return pair_address != "0x"


async def load_each_token():
    """
    Load each token from the token.yaml file.
    """

    async with aiofiles.open(TOKEN_FILE, "r") as f:
        content = await f.read()
        tokens = yaml.safe_load(content)
    return tokens["tokens"]


async def main() -> None:
    """
    Main function to run the script.
    """
    load_env()
    weth_address = os.getenv("WETH_ADDRESS")
    public_key = os.getenv("PUBLIC_KEY")

    if not weth_address or not public_key:
        raise ValueError("WETH_ADDRESS or PUBLIC_KEY environment variable is not set.")

    rpc_url = os.getenv("RPC_URL")
    if not rpc_url:
        raise ValueError("RPC_URL environment variable is not set.")

    token_out_address = os.getenv("TOKEN_OUT_ADDRESS")
    if not token_out_address:
        raise ValueError("TOKEN_OUT_ADDRESS environment variable is not set.")

    logger.info("Connecting to RPC URL: %s", rpc_url)
    logger.info("WETH Address: %s", weth_address)
    logger.info("Public Key: %s", public_key)

    tokens = await load_each_token()
    logger.info("Loaded tokens: %s", [token["symbol"] for token in tokens])
    # Example usage
    try:
        async with get_web3_provider(rpc_url) as w3:
            await print_balance(w3, public_key)
            await print_weth_balance(w3, public_key, weth_address)
            for token in tokens:
                blockchain = token["blockchain"]
                symbol = token["symbol"]
                if blockchain == "MegaETH" and symbol != "ETH":

                    address = token["address"]
                    decimals = int(token["decimals"])
                    logger.debug("checking token %s (%s)", symbol, address)
                    is_pair = await get_pair(w3, weth_address, address)
                    logger.info(
                        "Is there a pair for %s and %s, %s? %s",
                        weth_address,
                        address,
                        f"{symbol}/WETH",
                        "Yes" if is_pair else "No",
                    )
                    if is_pair:
                        await print_amount_out(
                            w3,
                            10**18,  # 1 ETH in wei
                            weth_address,
                            address,
                            10**decimals,
                        )
    except ValueError as e:
        logger.error("Error: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
