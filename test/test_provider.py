"""
Unit tests for the provider module.

This module contains tests for the provider functionality including
web3 provider setup, ABI loading, and environment variable handling.
"""

import os
import unittest
from unittest.mock import AsyncMock, patch

from provider import get_web3_provider, load_abi, load_env


class TestProvider(unittest.IsolatedAsyncioTestCase):
    """
    Test case for the provider module functionality.

    Tests the web3 provider context manager, ABI loading, and environment
    variable handling functions.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock for environment variables
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "RPC_URL": "https://example.com/rpc",
                "WETH_ADDRESS": "0x1234567890abcdef",
                "PRIVATE_KEY": "private_key_value",
                "PUBLIC_KEY": "public_key_value",
                "UNISWAP_ROUTER_ADDRESS": "0xabcdef1234567890",
                "TOKEN_OUT_ADDRESS": "0x0987654321fedcba",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.env_patcher.stop()

    @patch("provider.AsyncHTTPProvider")
    @patch("provider.AsyncWeb3")
    async def test_get_web3_provider(self, mock_async_web3, mock_provider):
        """Test that get_web3_provider correctly creates and yields a web3 instance."""
        # Configure mocks
        mock_web3_instance = AsyncMock()
        mock_async_web3.return_value = mock_web3_instance

        # Test the context manager
        async with get_web3_provider("https://example.com/rpc") as w3:
            # Assert provider was created with correct URL
            mock_provider.assert_called_once_with("https://example.com/rpc")
            # Assert Web3 was created with the provider
            mock_async_web3.assert_called_once()
            # Assert we got the right instance
            self.assertEqual(w3, mock_web3_instance)

    @patch("aiofiles.open")
    async def test_load_abi(self, mock_aiofiles_open):
        """Test that load_abi correctly loads and parses an ABI file."""
        # Create a mock file and configure it to return valid JSON
        mock_file = AsyncMock()
        mock_file.__aenter__.return_value = mock_file
        mock_file.read.return_value = '{"abi": [{"type": "function", "name": "test"}]}'
        mock_aiofiles_open.return_value = mock_file

        # Call the function
        result = await load_abi("path/to/abi.json")

        # Assert the file was opened correctly
        mock_aiofiles_open.assert_called_once_with(
            "path/to/abi.json", "r", encoding="utf-8"
        )

        # Assert the result is parsed correctly
        expected = {"abi": [{"type": "function", "name": "test"}]}
        self.assertEqual(result, expected)

    @patch("provider.load_dotenv")
    @patch("provider.logger")
    def test_load_env_success(self, mock_logger, mock_load_dotenv):
        """Test that load_env successfully loads environment variables when all are present."""

        keep_env = os.environ.copy()

        os.environ.update(
            {
                "RPC_URL": "https://example.com/rpc",
                "WETH_ADDRESS": "0x1234567890abcdef",
                "PRIVATE_KEY": "private_key_value",
                "PUBLIC_KEY": "public_key_value",
                "UNISWAP_ROUTER_ADDRESS": "0xabcdef1234567890",
                "TOKEN_OUT_ADDRESS": "0x0987654321fedcba",
                "WETH_DECIMALS": "18",
                "TOKEN_OUT_DECIMALS": "18",
            }
        )

        # Call the function
        load_env()

        # Assert dotenv was called
        mock_load_dotenv.assert_called_once_with(override=True)

        # Assert logger was called with appropriate messages
        mock_logger.info.assert_any_call(
            "Loading environment variables from .env file."
        )
        mock_logger.info.assert_any_call("Environment variables loaded successfully.")

        os.environ.clear()
        os.environ.update(keep_env)

    @patch("provider.load_dotenv")
    def test_load_env_missing_vars(self, _mock_load_dotenv):
        """Test that load_env raises an error when environment variables are missing."""
        # Remove one of the required environment variables
        with patch.dict("os.environ", clear=True):
            # Add only some of the required variables
            os.environ["RPC_URL"] = "https://example.com/rpc"
            # WETH_ADDRESS is missing

            # Assert that the function raises ValueError
            with self.assertRaises(ValueError) as context:
                load_env()

            # Check that the error message contains the missing variable
            self.assertIn("WETH_ADDRESS", str(context.exception))


if __name__ == "__main__":
    unittest.main()
