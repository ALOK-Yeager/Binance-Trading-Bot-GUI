"""
Headless Trading Bot for background operation on a server.
This bot runs without a GUI and can be deployed to run continuously.
"""
import os
import time
import logging
from datetime import datetime
from binance import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import threading
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("logs/headless_bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger("headless_bot")

# Load environment variables
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
testnet = os.getenv("TESTNET", "True").lower() in ["true", "1", "t", "yes"]

class HeadlessTradingBot:
    def __init__(self):
        """Initialize the headless trading bot"""
        logger.info("Initializing headless trading bot")
        
        if not api_key or not api_secret:
            logger.error("API key or secret is missing. Check your .env file.")
            sys.exit(1)
            
        try:
            self.client = Client(api_key, api_secret, testnet=testnet)
            # Explicitly set testnet URL for futures endpoints if using testnet
            if testnet:
                self.client.FUTURES_URL = 'https://testnet.binancefuture.com'
            logger.info(f"Connected to Binance {'Testnet' if testnet else 'Production'}")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {str(e)}")
            sys.exit(1)
        
        # Monitoring state
        self.symbols = ["BTCUSDT", "ETHUSDT"]
        self.price_data = {}
        self.running = True
        self.last_balance_check = 0
        self.balance_check_interval = 3600  # Check balance every hour
        
    def monitor_prices(self):
        """Monitor cryptocurrency prices in a separate thread"""
        logger.info(f"Starting price monitoring for: {', '.join(self.symbols)}")
        
        while self.running:
            try:
                for symbol in self.symbols:
                    ticker = self.client.get_symbol_ticker(symbol=symbol)
                    price = float(ticker['price'])
                    
                    if symbol in self.price_data:
                        prev_price = self.price_data[symbol]['price']
                        price_change = ((price - prev_price) / prev_price) * 100
                    else:
                        price_change = 0
                    
                    self.price_data[symbol] = {
                        'price': price,
                        'change': price_change,
                        'timestamp': datetime.now()
                    }
                    
                    logger.info(f"{symbol}: {price} ({price_change:.2f}%)")
                
                # Check account balance periodically
                current_time = time.time()
                if current_time - self.last_balance_check > self.balance_check_interval:
                    self.check_account_balance()
                    self.last_balance_check = current_time
                    
            except BinanceAPIException as e:
                logger.error(f"Binance API Error: {str(e)}")
            except Exception as e:
                logger.error(f"Error monitoring prices: {str(e)}")
            
            # Sleep for 30 seconds before checking again
            time.sleep(30)
    
    def check_account_balance(self):
        """Check account balances and log them"""
        try:
            account = self.client.get_account()
            balances = []
            
            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                
                if free > 0 or locked > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked
                    })
            
            logger.info("Account Balances:")
            for balance in balances:
                logger.info(f"{balance['asset']}: {balance['free']} (free), {balance['locked']} (locked)")
                
        except Exception as e:
            logger.error(f"Error checking account balance: {str(e)}")
    
    def stop(self):
        """Stop the bot gracefully"""
        logger.info("Stopping bot...")
        self.running = False
        
    def run(self):
        """Run the bot"""
        logger.info("Starting headless trading bot")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=self.monitor_prices)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Keep the main thread alive
        while self.running:
            time.sleep(1)
            
        logger.info("Headless trading bot stopped")
    
    def handle_signal(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop()

if __name__ == "__main__":
    bot = HeadlessTradingBot()
    bot.run()
