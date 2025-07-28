"""
Test script for trading operations using Binance Testnet.
"""
from dotenv import load_dotenv
import os
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException
from src.logger import logger

def test_trading_operations():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("API credentials not found in .env file")
        return
    
    # Initialize client
    client = Client(api_key, api_secret, testnet=True)
    
    try:
        # 1. Market Order Test
        logger.info("\n=== Testing Market Order ===")
        market_order = client.create_order(
            symbol='BTCUSDT',
            side='BUY',
            type='MARKET',
            quantity=0.001  # Small amount for testing
        )
        logger.info(f"Market Order Placed: {market_order}")
        
        # Wait a moment for order to process
        time.sleep(2)
        
        # 2. Limit Order Test
        logger.info("\n=== Testing Limit Order ===")
        # Get current price
        btc_price = float(client.get_symbol_ticker(symbol="BTCUSDT")['price'])
        # Place limit order 2% below current price
        limit_price = round(btc_price * 0.98, 2)
        
        limit_order = client.create_order(
            symbol='BTCUSDT',
            side='BUY',
            type='LIMIT',
            timeInForce='GTC',  # Good Till Cancelled
            quantity=0.001,
            price=limit_price
        )
        logger.info(f"Limit Order Placed: {limit_order}")
        
        # 3. Check Orders Status
        logger.info("\n=== Checking Order Status ===")
        # Check market order status
        if 'orderId' in market_order:
            market_status = client.get_order(
                symbol='BTCUSDT',
                orderId=market_order['orderId']
            )
            logger.info(f"Market Order Status: {market_status['status']}")
        
        # Check limit order status
        if 'orderId' in limit_order:
            limit_status = client.get_order(
                symbol='BTCUSDT',
                orderId=limit_order['orderId']
            )
            logger.info(f"Limit Order Status: {limit_status['status']}")
        
        # 4. Get Open Orders
        logger.info("\n=== Checking Open Orders ===")
        open_orders = client.get_open_orders(symbol='BTCUSDT')
        logger.info(f"Open Orders: {open_orders}")
        
        # 5. Cancel Limit Order
        logger.info("\n=== Cancelling Limit Order ===")
        if 'orderId' in limit_order:
            cancel_result = client.cancel_order(
                symbol='BTCUSDT',
                orderId=limit_order['orderId']
            )
            logger.info(f"Cancel Order Result: {cancel_result}")
        
    except BinanceAPIException as e:
        logger.error(f"Binance API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_trading_operations()
