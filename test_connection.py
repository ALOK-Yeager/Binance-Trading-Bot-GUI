"""
Test script to verify Binance API connection and functionality.
"""
from dotenv import load_dotenv
import os
from binance.client import Client
from src.logger import logger

def test_api_connection():
    """Test the Binance API connection with provided credentials."""
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
        # Test API connection
        account = client.get_account()
        logger.info("Successfully connected to Binance API!")
        logger.info(f"Account type: {account['accountType']}")
        
        # Show balances
        logger.info("\nAccount Balances:")
        for asset in account['balances']:
            if float(asset['free']) > 0 or float(asset['locked']) > 0:
                logger.info(f"{asset['asset']}: Free={asset['free']}, Locked={asset['locked']}")
        
        # Test market data
        btc_price = client.get_symbol_ticker(symbol="BTCUSDT")
        logger.info(f"\nCurrent BTC/USDT price: {btc_price['price']}")
        
    except Exception as e:
        logger.error(f"API connection failed: {str(e)}")

if __name__ == "__main__":
    test_api_connection()
