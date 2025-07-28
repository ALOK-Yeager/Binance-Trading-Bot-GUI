import pytest
from unittest.mock import MagicMock, patch
from binance.exceptions import BinanceAPIException
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from bot import BasicBot

@pytest.fixture
def mock_client():
    """Fixture to create a mock Binance client."""
    client = MagicMock()
    # Mock successful order creation
    client.futures_create_order.return_value = {
        'orderId': 12345,
        'symbol': 'BTCUSDT',
        'status': 'NEW',
        'side': 'BUY',
        'type': 'LIMIT',
        'quantity': '0.001',
        'price': '50000.0'
    }
    return client

@pytest.fixture
def bot(mock_client):
    """Fixture to create a BasicBot instance with a mock client."""
    with patch('bot.Client', return_value=mock_client):
        return BasicBot(api_key="test_key", api_secret="test_secret")

def test_place_market_order_success(bot, mock_client):
    """Test successful placement of a MARKET order."""
    response = bot.place_order(
        original_symbol="BTC/USDT",
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.001
    )
    
    mock_client.futures_create_order.assert_called_once_with(
        symbol='BTCUSDT',
        side='BUY',
        type='MARKET',
        quantity=0.001
    )
    assert response['orderId'] == 12345
    assert response['status'] == 'NEW'

def test_place_limit_order_success(bot, mock_client):
    """Test successful placement of a LIMIT order."""
    response = bot.place_order(
        original_symbol="BTC/USDT",
        symbol="BTCUSDT",
        side="SELL",
        order_type="LIMIT",
        quantity=0.002,
        price=60000.0
    )
    
    mock_client.futures_create_order.assert_called_once_with(
        symbol='BTCUSDT',
        side='SELL',
        type='LIMIT',
        quantity=0.002,
        price=60000.0,
        timeInForce='GTC'
    )
    assert response['orderId'] == 12345

def test_place_order_invalid_side(bot):
    """Test order placement with an invalid side."""
    with pytest.raises(ValueError, match="Invalid side"):
        bot.place_order("BTC/USDT", "BTCUSDT", "INVALID_SIDE", "MARKET", 0.001)

def test_place_order_invalid_type(bot):
    """Test order placement with an invalid order type."""
    with pytest.raises(ValueError, match="Invalid order type"):
        bot.place_order("BTC/USDT", "BTCUSDT", "BUY", "INVALID_TYPE", 0.001)

def test_place_order_zero_quantity(bot):
    """Test order placement with zero quantity."""
    with pytest.raises(ValueError, match="Invalid quantity"):
        bot.place_order("BTC/USDT", "BTCUSDT", "BUY", "MARKET", 0)

def test_place_limit_order_no_price(bot):
    """Test LIMIT order placement without a price."""
    with pytest.raises(ValueError, match="Invalid price for LIMIT order"):
        bot.place_order("BTC/USDT", "BTCUSDT", "BUY", "LIMIT", 0.001)

def test_place_order_api_exception(bot, mock_client):
    """Test handling of BinanceAPIException during order placement."""
    # Correctly simulate a BinanceAPIException by mocking the response object
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = '{"code": -1121, "msg": "Invalid symbol."}'
    
    # The BinanceAPIException is raised with the response object
    api_exception = BinanceAPIException(response=mock_response, status_code=400, text='{"code": -1121, "msg": "Invalid symbol."}')
    mock_client.futures_create_order.side_effect = api_exception
    
    with pytest.raises(BinanceAPIException) as excinfo:
        bot.place_order("BTC/USDT", "BTCUSDT", "BUY", "MARKET", 0.001)
    
    assert excinfo.value.code == -1121
    assert excinfo.value.status_code == 400

def test_init_with_testnet():
    """Test that the client is initialized correctly for testnet."""
    with patch('bot.Client') as mock_binance_client:
        bot = BasicBot(api_key="test_key", api_secret="test_secret", testnet=True)
        mock_binance_client.assert_called_once_with(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )
        assert bot.client.FUTURES_URL == 'https://testnet.binancefuture.com'

def test_handle_api_error(bot, mock_client):
    """Test handling of API errors."""
    # Create a mock response object
    mock_response = MagicMock()
    mock_response.text = "Invalid symbol"
    mock_response.status_code = 400
    
    # Set up the mock to raise an exception
    mock_client.futures_create_order.side_effect = BinanceAPIException(
        response=mock_response,
        status_code=400,
        text='{"code":-1000,"msg":"Invalid symbol"}'
    )
      
    # Try to place an order, which should raise the exception
    with pytest.raises(BinanceAPIException):
        bot.place_order(
            original_symbol="BTC/USDT",
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=0.001
        )
