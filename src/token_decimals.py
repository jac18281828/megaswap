import asyncio
import json
import logging
import os

import aiofiles
import yaml
from dotenv import load_dotenv
from web3.exceptions import Web3Exception

from swap import get_web3_provider

TOKEN_FILE = "token.yaml"
ERC20_ABI = json.loads(open("src/abi/IERC20Metadata.json").read())

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
        ck_token_address = w3.to_checksum_address(token_address)
        contract = w3.eth.contract(address=ck_token_address, abi=ERC20_ABI)
        decimals = await contract.functions.decimals().call()
        return decimals
    except Web3Exception as e:
        logger.error(f"Error fetching decimals for {token_address}: {e}")
        return 0


async def load_each_token():
    """
    Load each token from the token.yaml file.
    """

    async with aiofiles.open(TOKEN_FILE, "r") as f:
        content = await f.read()
        tokens = yaml.safe_load(content)
    return tokens["tokens"]


async def main():
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
                logger.info(
                    f"Checking token {symbol} ({address}) with expected decimals: {decimals}"
                )
                actual_decimals = await get_decimals(w3, address)
                if actual_decimals != 0 and actual_decimals != decimals:
                    logger.info(
                        f"Token {token['symbol']} ({address}) has incorrect decimals: {actual_decimals} (expected: {decimals})"
                    )
                elif actual_decimals == decimals:
                    logger.info(
                        f"Token {token['symbol']} ({address}) has correct decimals: {actual_decimals}"
                    )


if __name__ == "__main__":
    load_dotenv()

    logger.info("Starting token decimals check...")
    asyncio.run(main())
