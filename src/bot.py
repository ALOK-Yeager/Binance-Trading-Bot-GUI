import logging
from binance import Client
from binance.exceptions import BinanceAPIException
import os
from dotenv import load_dotenv

class BasicBot:
    def __init__(self, api_key: str = None, api_secret: str = None, testnet=True):
        logging.basicConfig(
            format="[%(asctime)s] %(levelname)s: %(message)s",
            level=logging.INFO
        )
        
        # If API keys not provided, load from environment
        if api_key is None or api_secret is None:
            load_dotenv()
            api_key = os.getenv("BINANCE_API_KEY", "")
            api_secret = os.getenv("BINANCE_API_SECRET", "")
        
        if not api_key or not api_secret:
            logging.error("API key or secret is missing")
            raise ValueError("API key or secret is missing")
            
        self.client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
        # Explicitly set testnet URL for futures endpoints
        self.client.FUTURES_URL = 'https://testnet.binancefuture.com'

    def validate_user_input(self):
        # Symbol input with format conversion
        while True:
            original_symbol = input("Enter symbol (e.g., BTC/USDT): ").strip()
            symbol = original_symbol.replace('/', '').upper()
            if not symbol:
                print("Symbol cannot be empty")
                continue
            break

        # Side validation
        while True:
            side = input("Enter side (BUY/SELL): ").upper()
            if side in ['BUY', 'SELL']:
                break
            print("Invalid side. Must be BUY or SELL")

        # Order type validation
        while True:
            order_type = input("Enter order type (MARKET/LIMIT): ").upper()
            if order_type in ['MARKET', 'LIMIT']:
                break
            print("Invalid order type. Must be MARKET or LIMIT")

        # Quantity validation
        while True:
            try:
                quantity = float(input("Enter quantity: "))
                if quantity > 0:
                    break
                print("Quantity must be greater than 0")
            except ValueError:
                print("Invalid quantity. Must be a number")

        # Price validation for LIMIT orders
        price = None
        if order_type == 'LIMIT':
            while True:
                try:
                    price = float(input("Enter price: "))
                    if price > 0:
                        break
                    print("Price must be greater than 0")
                except ValueError:
                    print("Invalid price. Must be a number")

        return original_symbol, symbol, side, order_type, quantity, price

    def place_order(self, original_symbol, symbol, side, order_type, quantity, price=None):
        try:
            # Input validation
            if side not in ['BUY', 'SELL']:
                raise ValueError("Invalid side")
            if order_type not in ['MARKET', 'LIMIT']:
                raise ValueError("Invalid order type")
            if quantity <= 0:
                raise ValueError("Invalid quantity")
            if order_type == 'LIMIT' and (price is None or price <= 0):
                raise ValueError("Invalid price for LIMIT order")

            # Prepare parameters
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
            }
            
            if order_type == 'LIMIT':
                params['price'] = price
                params['timeInForce'] = 'GTC'  # Required for LIMIT orders

            # Log order placement
            price_display = f"@ {price}" if price else "MARKET"
            logging.info(f"Placing {order_type} order for {original_symbol} ({side}, qty={quantity} {price_display})")

            # Execute order
            response = self.client.futures_create_order(**params)
            return response

        except BinanceAPIException as e:
            error_msg = f"Binance API Error: {e.message} (Code: {e.status_code})"
            logging.error(error_msg)
            raise
        except ValueError as ve:
            error_msg = f"Validation Error: {ve}"
            logging.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logging.error(error_msg)
            raise

    def run(self):
        try:
            # Get and validate user input
            original_symbol, symbol, side, order_type, quantity, price = self.validate_user_input()
            
            # Place order and show results
            response = self.place_order(original_symbol, symbol, side, order_type, quantity, price)
            print("\nOrder Details:")
            print(f"Symbol: {original_symbol}")
            print(f"Side: {side}")
            print(f"Type: {order_type}")
            print(f"Quantity: {quantity}")
            if price:
                print(f"Price: {price}")
            print(f"Order ID: {response['orderId']}")
            print(f"Status: {response['status']}")

        except Exception:
            print("\nOrder placement failed. Check logs for details.")

    def get_account_balance(self, asset=None):
        """Get account balance for a specific asset or all assets"""
        try:
            account = self.client.get_account()
            
            if asset:
                for balance in account['balances']:
                    if balance['asset'] == asset:
                        return {
                            'asset': balance['asset'],
                            'free': float(balance['free']),
                            'locked': float(balance['locked'])
                        }
                return None
            else:
                balances = []
                for balance in account['balances']:
                    if float(balance['free']) > 0 or float(balance['locked']) > 0:
                        balances.append({
                            'asset': balance['asset'],
                            'free': float(balance['free']),
                            'locked': float(balance['locked'])
                        })
                return balances
        
        except BinanceAPIException as e:
            logging.error(f"Binance API Error: {e.message} (Code: {e.status_code})")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    def place_market_order(self, symbol, side, quantity):
        """Place a market order"""
        return self.place_order(
            original_symbol=symbol,
            symbol=symbol.replace('/', ''),
