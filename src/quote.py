"""Quote a token pair on uniswap"""

import asyncio
import logging
import os

from provider import get_web3_provider, load_abi, load_env
from swap import get_pair

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def get_reserves(w3, token_a, token_b):
    """
    Get the reserves of a token pair.
    """
    uniswap_pair_abi = await load_abi("src/abi/IUniswapV2Pair.json")
    pair_address = await get_pair(w3, token_a, token_b)
    if not pair_address:
        logger.error("Pair address not found for %s and %s", token_a, token_b)
        return None
    logger.info("Pair address: %s", pair_address)
    ck_pair_address = w3.to_checksum_address(pair_address)
    pair_contract = w3.eth.contract(address=ck_pair_address, abi=uniswap_pair_abi)

    # get pair info
    name = await pair_contract.functions.name().call()
    symbol = await pair_contract.functions.symbol().call()
    decimals = await pair_contract.functions.decimals().call()
    logger.info("Pair name: %s", name)
    logger.info("Pair symbol: %s", symbol)
    logger.info("Pair decimals: %s", decimals)
    token0 = await pair_contract.functions.token0().call()
    token1 = await pair_contract.functions.token1().call()
    logger.info("Token0: %s", token0)
    logger.info("Token1: %s", token1)

    reserves = await pair_contract.functions.getReserves().call()
    return reserves


async def main():
    """main method"""

    weth_address = os.getenv("WETH_ADDRESS")
    assert weth_address, "WETH_ADDRESS environment variable is not set."
    token_out = os.getenv("TOKEN_OUT_ADDRESS")
    assert token_out, "TOKEN_OUT_ADDRESS environment variable is not set."
    rpc_url = os.getenv("RPC_URL")
    assert rpc_url, "RPC_URL environment variable is not set."
    weth_decimals = os.getenv("WETH_DECIMALS")
    assert (
        weth_decimals
    ), "WETH_DECIMALS environment variable is not set. Defaulting to 18."
    token_out_decimals = os.getenv("TOKEN_OUT_DECIMALS")
    assert (
        token_out_decimals
    ), "TOKEN_OUT_DECIMALS environment variable is not set. Defaulting to 18."

    async with get_web3_provider(rpc_url) as w3:
        # Get the reserves for the token pair
        reserves = await get_reserves(w3, weth_address, token_out)
        if reserves:
            logger.info("Reserves for %s and %s: %s", weth_address, token_out, reserves)
        else:
            logger.error(
                "Failed to get reserves for %s and %s", weth_address, token_out
            )

        base_decimals = int(weth_decimals)
        out_decimals = int(token_out_decimals)

        reserve_eth = reserves[0] / (10**base_decimals)
        reserve_out_token = reserves[1] / (10**out_decimals)
        logger.info("Reserve ETH: %s", reserve_eth)
        logger.info("Reserve %s: %s", token_out, reserve_out_token)
        # Calculate the price
        price = reserve_out_token / reserve_eth
        formatted_price = f"{price:.4f}" if price >= 0.0001 else f"{price:.4e}"
        logger.info("Quoting %s/%s at %s", token_out, weth_address, formatted_price)


if __name__ == "__main__":
    load_env()
    asyncio.run(main())
