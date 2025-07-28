"""
Enhanced Web UI for Binance Trading Bot - Trading interface with order placement and monitoring
"""
from flask import Flask, render_template_string, jsonify, request, redirect, url_for
from binance import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime
import threading
import time
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("logs/web_ui.log"), logging.StreamHandler()]
)
logger = logging.getLogger("web_ui")

# Load environment variables
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
testnet = os.getenv("TESTNET", "True").lower() in ["true", "1", "t", "yes"]

# Initialize Flask app
app = Flask(__name__)

# Global state
market_data = {}
account_balances = []
order_history = []
bot_status = "Running"
last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
price_changes = {}  # To track price changes for color indicators

# Initialize Binance client
try:
    client = Client(api_key, api_secret, testnet=testnet)
    # Explicitly set testnet URL for futures endpoints if using testnet
    if testnet:
        client.FUTURES_URL = 'https://testnet.binancefuture.com'
    logger.info("Binance client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Binance client: {str(e)}")
    client = None

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Binance Trading Bot Dashboard</title>
    <style>
        :root {
            --primary-color: #3484F0;
            --secondary-color: #4CAF50;
            --danger-color: #F44336;
            --dark-bg: #2a2d2e;
            --light-text: #ffffff;
            --card-bg: #343638;
            --light-bg: #f5f5f5;
            --border-color: #ddd;
        }
        
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: var(--light-bg);
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 15px;
        }
        
        h1 {
            color: var(--primary-color);
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.2rem;
        }
        
        .card {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            overflow: hidden;
        }
        
        .card-header {
            background-color: var(--primary-color);
            color: white;
            padding: 12px 20px;
            font-size: 1.2rem;
            font-weight: bold;
        }
        
        .card-body {
            padding: 20px;
        }
        
        .status-container {
            background-color: var(--secondary-color);
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
            font-size: 1.2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
            background-color: white;
        }
        
        th, td {
            border: 1px solid var(--border-color);
            padding: 12px;
            text-align: left;
        }
        
        th {
            background-color: #f2f2f2;
            position: sticky;
            top: 0;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .price-up {
            color: var(--secondary-color);
            font-weight: bold;
        }
        
        .price-down {
            color: var(--danger-color);
            font-weight: bold;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        
        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        
        button {
            background-color: var(--primary-color);
            border: none;
            color: white;
            padding: 12px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 10px 0;
            cursor: pointer;
            border-radius: 5px;
            width: 100%;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }
        
        button:hover {
            background-color: #2a6ebd;
            transform: translateY(-2px);
        }
        
        .notification {
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        
        .notification.success {
            background-color: #d4edda;
            color: #155724;
        }
        
        .notification.error {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        .notification.info {
            background-color: #d1ecf1;
            color: #0c5460;
        }
        
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: 1px solid transparent;
            border-bottom: none;
            margin-right: 5px;
            border-radius: 5px 5px 0 0;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            background-color: white;
            border-color: var(--border-color);
            border-bottom-color: white;
            margin-bottom: -1px;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .last-update {
            text-align: right;
            font-size: 0.8rem;
            color: #666;
            margin-top: 10px;
        }
        
        .text-center {
            text-align: center;
        }
        
        /* Auto refresh indication */
        .refresh-indicator {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: var(--primary-color);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.8rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Binance Trading Bot Dashboard</h1>
        
        <div class="status-container">
            Bot Status: {{ bot_status }}
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="openTab('market-data')">Market Data</div>
            <div class="tab" onclick="openTab('place-order')">Place Order</div>
            <div class="tab" onclick="openTab('orders')">Order History</div>
            <div class="tab" onclick="openTab('balances')">Account Balances</div>
        </div>
        
        <!-- Market Data Tab -->
        <div id="market-data" class="tab-content active card">
            <div class="card-header">Live Market Data</div>
            <div class="card-body">
                <table>
                    <thead>
                        <tr>
                            <th>Pair</th>
                            <th>Price</th>
                            <th>24h Change</th>
                            <th>Updated</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for symbol, data in market_data.items() %}
                        <tr>
                            <td>{{ symbol }}</td>
                            {% if data.change > 0 %}
                                <td class="price-up">{{ data.price }}</td>
                                <td class="price-up">+{{ data.change|round(2) }}%</td>
                            {% elif data.change < 0 %}
                                <td class="price-down">{{ data.price }}</td>
                                <td class="price-down">{{ data.change|round(2) }}%</td>
                            {% else %}
                                <td>{{ data.price }}</td>
                                <td>{{ data.change|round(2) }}%</td>
                            {% endif %}
                            <td>{{ data.updated }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Place Order Tab -->
        <div id="place-order" class="tab-content card">
            <div class="card-header">Place New Order</div>
            <div class="card-body">
                {% if notification %}
                <div class="notification {{ notification.type }}">
                    {{ notification.message }}
                </div>
                {% endif %}
                
                <form action="/place_order" method="POST">
                    <div class="grid">
                        <div>
                            <div class="form-group">
                                <label for="symbol">Symbol:</label>
                                <select name="symbol" id="symbol" required>
                                    <option value="BTCUSDT">BTC/USDT</option>
                                    <option value="ETHUSDT">ETH/USDT</option>
                                    <option value="BNBUSDT">BNB/USDT</option>
                                    <option value="LTCUSDT">LTC/USDT</option>
                                    <option value="SOLUSDT">SOL/USDT</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="side">Side:</label>
                                <select name="side" id="side" required>
                                    <option value="BUY">BUY</option>
                                    <option value="SELL">SELL</option>
                                </select>
                            </div>
                        </div>
                        
                        <div>
                            <div class="form-group">
                                <label for="type">Order Type:</label>
                                <select name="type" id="type" onchange="togglePriceField()" required>
                                    <option value="MARKET">MARKET</option>
                                    <option value="LIMIT">LIMIT</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="quantity">Quantity:</label>
                                <input type="number" name="quantity" id="quantity" step="0.001" min="0.001" required>
                            </div>
                            
                            <div class="form-group" id="price-field" style="display:none;">
                                <label for="price">Price:</label>
                                <input type="number" name="price" id="price" step="0.01">
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit">Place Order</button>
                </form>
            </div>
        </div>
        
        <!-- Order History Tab -->
        <div id="orders" class="tab-content card">
            <div class="card-header">Order History</div>
            <div class="card-body">
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Type</th>
                            <th>Side</th>
                            <th>Price</th>
                            <th>Quantity</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for order in order_history %}
                        <tr>
                            <td>{{ order.time }}</td>
                            <td>{{ order.symbol }}</td>
                            <td>{{ order.type }}</td>
                            <td>{{ order.side }}</td>
                            <td>{{ order.price }}</td>
                            <td>{{ order.quantity }}</td>
                            <td>{{ order.status }}</td>
                        </tr>
                        {% endfor %}
                        {% if not order_history %}
                        <tr>
                            <td colspan="7" class="text-center">No orders found</td>
                        </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Account Balances Tab -->
        <div id="balances" class="tab-content card">
            <div class="card-header">Account Balances</div>
            <div class="card-body">
                <table>
                    <thead>
                        <tr>
                            <th>Asset</th>
                            <th>Free</th>
                            <th>Locked</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for balance in account_balances %}
                        <tr>
                            <td>{{ balance.asset }}</td>
                            <td>{{ balance.free }}</td>
                            <td>{{ balance.locked }}</td>
                        </tr>
                        {% endfor %}
                        {% if not account_balances %}
                        <tr>
                            <td colspan="3" class="text-center">No balance data available</td>
                        </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="last-update">Last updated: {{ last_update }}</div>
        <div class="refresh-indicator">Auto-refreshing data...</div>
    </div>
    
    <script>
        // Tab functionality
        function openTab(tabName) {
            // Hide all tabs
            const tabContents = document.getElementsByClassName("tab-content");
            for (let i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove("active");
            }
            
            // Remove active class from all tabs
            const tabs = document.getElementsByClassName("tab");
            for (let i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove("active");
            }
            
            // Show the selected tab content
            document.getElementById(tabName).classList.add("active");
            
            // Set the clicked tab as active
            event.currentTarget.classList.add("active");
        }
        
        // Toggle price field based on order type
        function togglePriceField() {
            const orderType = document.getElementById("type").value;
            const priceField = document.getElementById("price-field");
            
            if (orderType === "LIMIT") {
                priceField.style.display = "block";
                document.getElementById("price").required = true;
            } else {
                priceField.style.display = "none";
                document.getElementById("price").required = false;
            }
        }
        
        // Auto refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
"""

def update_market_data():
    """Background thread to update market data periodically"""
    global market_data, account_balances, order_history, last_update, price_changes, bot_status
    
    while True:
        try:
            if client:
                # Update market data
                symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "LTCUSDT", "SOLUSDT"]
                updated_data = {}
                
                for symbol in symbols:
                    try:
                        # Get current price
                        ticker = client.get_ticker(symbol=symbol)
                        
                        # Calculate 24h change
                        change = float(ticker['priceChangePercent'])
                        
                        # Track price change direction for coloring
                        current_price = float(ticker['lastPrice'])
                        if symbol in market_data:
                            last_price = float(market_data[symbol]['price'])
                            if current_price > last_price:
                                direction = "up"
                            elif current_price < last_price:
                                direction = "down"
                            else:
                                direction = "same"
                        else:
                            direction = "same"
                        
                        # Update market data
                        updated_data[symbol] = {
                            'price': ticker['lastPrice'],
                            'change': change,
                            'direction': direction,
                            'updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                    except Exception as e:
                        logger.error(f"Error updating market data for {symbol}: {str(e)}")
                
                # Update global market data
                market_data = updated_data
                
                # Update account balances
                try:
                    account = client.get_account()
                    balances = []
                    for balance in account['balances']:
                        if float(balance['free']) > 0 or float(balance['locked']) > 0:
                            balances.append({
                                'asset': balance['asset'],
                                'free': balance['free'],
                                'locked': balance['locked']
                            })
                    account_balances = balances
                except Exception as e:
                    logger.error(f"Error updating account balances: {str(e)}")
                
                # Update order history
                try:
                    all_orders = []
                    for symbol in symbols:
                        orders = client.get_all_orders(symbol=symbol, limit=10)
                        all_orders.extend(orders)
                    
                    # Sort by time (newest first) and limit to last 20
                    all_orders.sort(key=lambda x: x['time'], reverse=True)
                    all_orders = all_orders[:20]
                    
                    # Format for display
                    formatted_orders = []
                    for order in all_orders:
                        formatted_orders.append({
                            'time': datetime.fromtimestamp(order['time']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                            'symbol': order['symbol'],
                            'type': order['type'],
                            'side': order['side'],
                            'price': order.get('price', 'MARKET'),
                            'quantity': order['origQty'],
                            'status': order['status']
                        })
                    
                    order_history = formatted_orders
                except Exception as e:
                    logger.error(f"Error updating order history: {str(e)}")
                
                # Update timestamp
                last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info("Market data updated successfully")
            else:
                logger.warning("Binance client not initialized, can't update data")
                bot_status = "Error - API not connected"
        
        except Exception as e:
            logger.error(f"Error in update_market_data thread: {str(e)}")
        
        time.sleep(30)  # Update every 30 seconds

@app.route('/')
def index():
    """Main dashboard route"""
    global market_data, account_balances, order_history, last_update, bot_status
    
    # Ensure we have some data
    if not market_data and client:
        try:
            # Get some initial data for BTCUSDT
            ticker = client.get_ticker(symbol="BTCUSDT")
            market_data["BTCUSDT"] = {
                'price': ticker['lastPrice'],
                'change': float(ticker['priceChangePercent']),
                'direction': 'same',
                'updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Get some initial account data
            account = client.get_account()
            for balance in account['balances']:
                if float(balance['free']) > 0 or float(balance['locked']) > 0:
                    account_balances.append({
                        'asset': balance['asset'],
                        'free': balance['free'],
                        'locked': balance['locked']
                    })
            
            # Get some initial orders
            orders = client.get_all_orders(symbol="BTCUSDT", limit=10)
            for order in orders[:10]:
                order_history.append({
                    'time': datetime.fromtimestamp(order['time']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'symbol': order['symbol'],
                    'type': order['type'],
                    'side': order['side'],
                    'price': order.get('price', 'MARKET'),
                    'quantity': order['origQty'],
                    'status': order['status']
                })
            
        except Exception as e:
            logger.error(f"Error getting initial data: {str(e)}")
    
    # Check if there's a notification in the session
    notification = request.args.get('notification')
    notification_type = request.args.get('type', 'info')
    
    notification_data = None
    if notification:
        notification_data = {
            'message': notification,
            'type': notification_type
        }
    
    # Render the dashboard
    return render_template_string(
        HTML_TEMPLATE,
        market_data=market_data,
        account_balances=account_balances,
        order_history=order_history,
        last_update=last_update,
        bot_status=bot_status,
        notification=notification_data
    )

@app.route('/api/data')
def api_data():
    """API endpoint to get current data as JSON"""
    return jsonify({
        'market_data': market_data,
        'account_balances': account_balances,
        'order_history': order_history,
        'last_update': last_update,
        'bot_status': bot_status
    })

@app.route('/place_order', methods=['POST'])
def place_order():
    """Handle order placement"""
    try:
        # Get form data
        symbol = request.form.get('symbol')
        side = request.form.get('side')
        order_type = request.form.get('type')
        quantity = request.form.get('quantity')
        price = request.form.get('price')
        
        # Validate inputs
        if not all([symbol, side, order_type, quantity]):
            return redirect(f'/?notification=Missing required fields&type=error')
        
        # Convert quantity to float
        try:
            quantity = float(quantity)
        except ValueError:
            return redirect(f'/?notification=Invalid quantity&type=error')
        
        # For LIMIT orders, price is required
        if order_type == 'LIMIT' and not price:
            return redirect(f'/?notification=Price is required for LIMIT orders&type=error')
        
        # Get current market price to check for PERCENT_PRICE_BY_SIDE filter
        if order_type == 'LIMIT' and client:
            try:
                # Get current price
                ticker = client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                
                # Get price filter info
                exchange_info = client.get_exchange_info()
                price_filter = None
                
                for sym_info in exchange_info['symbols']:
                    if sym_info['symbol'] == symbol:
                        for filter_item in sym_info['filters']:
                            if filter_item['filterType'] == 'PERCENT_PRICE_BY_SIDE':
                                price_filter = filter_item
                                break
                
                # Check if price is within allowed range
                if price_filter and price:
                    price_float = float(price)
                    if side == 'BUY':
                        max_price = current_price * float(price_filter.get('bidMultiplierUp', 1.2))
                        if price_float > max_price:
                            return redirect(f'/?notification=Price too high! Maximum allowed: {max_price:.2f}&type=error')
                    else:  # SELL
                        min_price = current_price * float(price_filter.get('askMultiplierDown', 0.8))
                        if price_float < min_price:
                            return redirect(f'/?notification=Price too low! Minimum allowed: {min_price:.2f}&type=error')
            except Exception as e:
                logger.warning(f"Couldn't check price filter: {str(e)}")
        
        # Prepare order parameters
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        # Add price for LIMIT orders
        if order_type == 'LIMIT' and price:
            try:
                price_float = float(price)
                params['price'] = price_float
                params['timeInForce'] = 'GTC'
            except ValueError:
                return redirect(f'/?notification=Invalid price&type=error')
        
        # Place order
        if client:
            order = client.create_order(**params)
            logger.info(f"Order placed: {order}")
            
            # Update order history immediately
            global order_history
            order_history.insert(0, {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'price': price if order_type == 'LIMIT' else 'MARKET',
                'quantity': quantity,
                'status': 'NEW'
            })
            
            return redirect(f'/?notification=Order placed successfully! Order ID: {order["orderId"]}&type=success')
        else:
            return redirect(f'/?notification=API client not initialized&type=error')
    
    except BinanceAPIException as e:
        logger.error(f"Binance API Error: {e}")
        return redirect(f'/?notification=Binance API Error: {e.message} (Code: {e.status_code})&type=error')
    
    except Exception as e:
        logger.error(f"Unexpected error placing order: {str(e)}")
        return redirect(f'/?notification=Error placing order: {str(e)}&type=error')

if __name__ == "__main__":
    # Start the background thread for updates
    update_thread = threading.Thread(target=update_market_data, daemon=True)
    update_thread.start()
    
    # Run the Flask app
    app.run(host="0.0.0.0", port=8080, debug=False)
