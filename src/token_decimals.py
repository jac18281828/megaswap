"""get the token decimals"""

import asyncio
import logging
import os

from dotenv import load_dotenv
from web3.exceptions import Web3Exception

from provider import get_web3_provider, load_abi, load_yaml

TOKEN_FILE = "token.yaml"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def get_decimals(w3, token_address):
    """
    Get the decimals of a token.
    """
    try:
        erc20_abi = await load_abi("src/abi/IERC20Metadata.json")
        ck_token_address = w3.to_checksum_address(token_address)
        contract = w3.eth.contract(address=ck_token_address, abi=erc20_abi)
        decimals = await contract.functions.decimals().call()
        return decimals
    except Web3Exception as e:
        logger.error("Error fetching decimals for %s: %s", token_address, e)
        return 0


async def load_each_token():
    """
    Load each token from the token.yaml file.
    """
    tokens = load_yaml(TOKEN_FILE)
    assert tokens, "No tokens found in the token.yaml file."
    assert "tokens" in tokens, "No tokens found in the token.yaml file."
    return tokens["tokens"]


async def main():
    """main method"""
    rpc_url = os.getenv("RPC_URL")
    if not rpc_url:
        raise ValueError("RPC_URL environment variable is not set.")

    tokens = await load_each_token()
    async with get_web3_provider(rpc_url) as w3:
        for token in tokens:
            blockchain = token["blockchain"]
            if blockchain == "MegaETH":
                symbol = token["symbol"]
                address = token["address"]
                decimals = token["decimals"]
                # pylint: disable=logging-fstring-interpolation
                logger.info(
                    f"Checking token {symbol} ({address}) with expected decimals: {decimals}"
                )
                actual_decimals = await get_decimals(w3, address)
                if actual_decimals not in (0, decimals):
                    logger.error(
                        "Token %s (%s) has incorrect decimals: %s (expected: %s)",
                        token["symbol"],
                        address,
                        actual_decimals,
                        decimals,
                    )
                elif actual_decimals == decimals:
                    logger.info(
                        f"Token {token['symbol']} ({address}) has correct decimals: {actual_decimals}"
                    )


if __name__ == "__main__":
    load_dotenv()

    logger.info("Starting token decimals check...")
    asyncio.run(main())
