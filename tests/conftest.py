"""Test configuration and shared fixtures."""
import pytest
from unittest.mock import MagicMock
from binance.client import Client


@pytest.fixture
def mock_client():
    """Create a mock Binance client."""
    client = MagicMock(spec=Client)
    # Mock successful market order response
    client.futures_create_order.return_value = {
        "orderId": "12345",
        "symbol": "BTCUSDT",
        "status": "FILLED",
        "type": "MARKET",
        "side": "BUY"
    }
    return client


@pytest.fixture
def mock_api_error_client():
    """Create a mock Binance client that raises API errors."""
    client = MagicMock(spec=Client)
    client.futures_create_order.side_effect = Exception("Simulated API error")
    return client
