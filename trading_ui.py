"""
Enhanced Trading Bot UI with live updates, order history, and real-time notifications
"""
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from dotenv import load_dotenv
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
import threading
import time
from datetime import datetime
import queue
from typing import Dict, Optional

# --- UI Enhancements ---
# 1. Set a modern theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# 2. Define consistent font styles
HEADING_FONT = ("Arial", 18, "bold")
LABEL_FONT = ("Arial", 14)
ENTRY_FONT = ("Arial", 14)
BUTTON_FONT = ("Arial", 14, "bold")

class TradingBotUI:
    def __init__(self):
        # Load API credentials
        load_dotenv()
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY')
        self.client = Client(self.api_key, self.api_secret, testnet=True)
        
        # Initialize state variables
        self.stop_threads = False
        self.last_price = 0.0
        self.update_queue = queue.Queue()
        self.order_updates_queue = queue.Queue()
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Trading Bot UI")
        self.root.geometry("1200x800") # Increased size for better layout

        # --- Main Layout Configuration ---
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1) # Allow status frame to expand

        # Top frame for price and order sections
        top_frame = ctk.CTkFrame(self.root)
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)

        self.price_frame = self.create_price_frame(top_frame)
        self.order_frame = self.create_order_frame(top_frame)
        
        self.price_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        self.order_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

        # Status frame for order history
        self.status_frame = self.create_status_frame(self.root)
        self.status_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Bottom frame for controls
        control_frame = ctk.CTkFrame(self.root)
        control_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        control_frame.grid_columnconfigure(0, weight=1) # Left-align refresh
        control_frame.grid_columnconfigure(1, weight=1) # Right-align exit

        self.refresh_button = ctk.CTkButton(
            control_frame, text="Refresh", command=self.refresh_orders, font=BUTTON_FONT
        )
        self.refresh_button.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.close_button = ctk.CTkButton(
            control_frame, text="Exit", command=self.on_closing, font=BUTTON_FONT
        )
        self.close_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Start background tasks
        self.price_update_thread = threading.Thread(target=self.update_prices, daemon=True)
        self.price_update_thread.start()
        self.process_updates()
        self.auto_refresh_orders()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_price_frame(self, parent):
        """Create the price monitoring section"""
        frame = ctk.CTkFrame(parent)
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(frame, text="Price Monitor", font=HEADING_FONT).grid(row=0, column=0, pady=10, sticky="ew")
        
        self.price_label = ctk.CTkLabel(frame, text="BTC/USDT: Loading...", font=LABEL_FONT)
        self.price_label.grid(row=1, column=0, pady=5, padx=10, sticky="ew")
        
        self.last_update_label = ctk.CTkLabel(frame, text="Last Update: -", font=("Arial", 12))
        self.last_update_label.grid(row=2, column=0, pady=5, padx=10, sticky="ew")

        return frame

    def create_order_frame(self, parent):
        """Create the order placement section"""
        frame = ctk.CTkFrame(parent)
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(frame, text="Place Order", font=HEADING_FONT).grid(row=0, column=0, pady=10, sticky="ew")
        
        # Create a sub-frame for inputs to align them properly
        input_frame = ctk.CTkFrame(frame)
        input_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        # Symbol selection (Dropdown)
        ctk.CTkLabel(input_frame, text="Symbol:", font=LABEL_FONT).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.symbol_var = tk.StringVar(value="BTCUSDT")
        symbol_menu = ctk.CTkOptionMenu(input_frame, variable=self.symbol_var, values=["BTCUSDT", "ETHUSDT", "BNBUSDT"], font=ENTRY_FONT)
        symbol_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Order type selection
        ctk.CTkLabel(input_frame, text="Order Type:", font=LABEL_FONT).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.order_type_var = tk.StringVar(value="MARKET")
        order_type_menu = ctk.CTkOptionMenu(input_frame, variable=self.order_type_var, values=["MARKET", "LIMIT"], font=ENTRY_FONT)
        order_type_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Side selection
        ctk.CTkLabel(input_frame, text="Side:", font=LABEL_FONT).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.side_var = tk.StringVar(value="BUY")
        side_menu = ctk.CTkOptionMenu(input_frame, variable=self.side_var, values=["BUY", "SELL"], font=ENTRY_FONT)
        side_menu.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Quantity input
        ctk.CTkLabel(input_frame, text="Quantity:", font=LABEL_FONT).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.quantity_var = tk.StringVar(value="0.001")
        ctk.CTkEntry(input_frame, textvariable=self.quantity_var, font=ENTRY_FONT).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        # Price input (for limit orders)
        ctk.CTkLabel(input_frame, text="Price:", font=LABEL_FONT).grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.price_var = tk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.price_var, font=ENTRY_FONT).grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        # Place order button
        ctk.CTkButton(frame, text="Place Order", command=self.place_order, font=BUTTON_FONT).grid(row=2, column=0, pady=20, padx=10)

        return frame

    def create_status_frame(self, parent):
        """Create the status display section with a styled Treeview"""
        status_frame = ctk.CTkFrame(parent)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(status_frame, text="Order History", font=HEADING_FONT).grid(row=0, column=0, pady=10, sticky="ew")
        
        # --- Style for Treeview to match dark theme ---
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2a2d2e",
                        foreground="white",
                        rowheight=40,  # Further increased row height
                        fieldbackground="#343638",
                        bordercolor="#343638",
                        borderwidth=0,
                        font=("Arial", 16))  # Further increased font size
        style.map('Treeview', background=[('selected', '#22559b')])
        style.configure("Treeview.Heading",
                        background="#565b5e",
                        foreground="white",
                        relief="flat",
                        font=("Arial", 18, "bold"))  # Further increased heading font size
        style.map("Treeview.Heading",
                  background=[('active', '#3484F0')])

        # Create treeview for orders
        columns = ('S.No.', 'Time', 'Symbol', 'Type', 'Side', 'Price', 'Quantity', 'Status')
        self.order_tree = ttk.Treeview(status_frame, columns=columns, show='headings', height=8) # Set height to show fewer rows
        
        # Set column headings and widths
        self.order_tree.heading('S.No.', text='S.No.')
        self.order_tree.column('S.No.', width=50, anchor='center')
        
        self.order_tree.heading('Time', text='Time')
        self.order_tree.column('Time', width=180, anchor='center')

        self.order_tree.heading('Symbol', text='Symbol')
        self.order_tree.column('Symbol', width=120, anchor='center')

        self.order_tree.heading('Type', text='Type')
        self.order_tree.column('Type', width=100, anchor='center')

        self.order_tree.heading('Side', text='Side')
        self.order_tree.column('Side', width=100, anchor='center')

        self.order_tree.heading('Price', text='Price')
        self.order_tree.column('Price', width=150, anchor='center')

        self.order_tree.heading('Quantity', text='Quantity')
        self.order_tree.column('Quantity', width=150, anchor='center')

        self.order_tree.heading('Status', text='Status')
        self.order_tree.column('Status', width=120, anchor='center')
        
        self.order_tree.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Add scrollbar
        scrollbar = ctk.CTkScrollbar(status_frame, command=self.order_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.order_tree.configure(yscrollcommand=scrollbar.set)

        return status_frame

    def update_prices(self):
        """Update price information periodically"""
        while not self.stop_threads:
            try:
                ticker = self.client.get_symbol_ticker(symbol="BTCUSDT")
                new_price = float(ticker['price'])
                
                self.update_queue.put(('price', {
                    'price': new_price,
                    'time': datetime.now(),
                    'change': new_price - self.last_price if self.last_price else 0
                }))
                
                self.last_price = new_price
                time.sleep(1)
                
            except Exception as e:
                print(f"Error updating price: {str(e)}")
                time.sleep(5)
    
    def process_updates(self):
        """Process updates from the queue and update UI"""
        try:
            while not self.update_queue.empty():
                update_type, data = self.update_queue.get_nowait()
                
                if update_type == 'price':
                    price_color = "#4CAF50" if data['change'] >= 0 else "#F44336"
                    self.price_label.configure(
                        text=f"BTC/USDT: {data['price']:.2f}",
                        text_color=price_color
                    )
                    self.last_update_label.configure(
                        text=f"Last Update: {data['time'].strftime('%H:%M:%S')}"
                    )
                
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error processing updates: {str(e)}")
        
        if not self.stop_threads:
            self.root.after(100, self.process_updates)

    def place_order(self):
        """Handle order placement"""
        try:
            symbol = self.symbol_var.get()
            order_type = self.order_type_var.get()
            side = self.side_var.get()
            quantity = float(self.quantity_var.get())
            
            params = {'symbol': symbol, 'side': side, 'type': order_type, 'quantity': quantity}
            
            if order_type == 'LIMIT':
                price_str = self.price_var.get()
                if not price_str:
                    self.show_notification("Error", "Price is required for LIMIT orders", "error")
                    return
                params['price'] = float(price_str)
                params['timeInForce'] = 'GTC'
            
            self.root.config(cursor="watch")
            order = self.client.create_order(**params)
            self.root.config(cursor="")
            
            self.show_notification("Success", f"Order {order['orderId']} placed successfully!", "success")
            self.refresh_orders()
            
        except BinanceAPIException as e:
            self.show_notification("Order Failed", str(e), "error")
        except Exception as e:
            self.show_notification("Error", f"An unexpected error occurred: {str(e)}", "error")
        finally:
            self.root.config(cursor="")

    def show_notification(self, title: str, message: str, type_: str = "info"):
        """Show a custom notification window"""
        colors = {"success": "#4CAF50", "error": "#F44336", "info": "#2196F3"}
        
        notification = ctk.CTkToplevel(self.root)
        notification.title(title)
        notification.geometry("350x150")
        notification.attributes("-topmost", True)

        frame = ctk.CTkFrame(notification)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            frame, text=message, text_color=colors.get(type_, colors["info"]), wraplength=320, font=LABEL_FONT
        ).pack(pady=10, expand=True)
        
        ctk.CTkButton(
            frame, text="OK", command=notification.destroy, font=BUTTON_FONT
        ).pack(pady=10)
        
        notification.after(5000, notification.destroy)

    def refresh_orders(self):
        """Refresh the orders display"""
        try:
            for item in self.order_tree.get_children():
                self.order_tree.delete(item)
            
            orders = self.client.get_all_orders(symbol=self.symbol_var.get(), limit=50)
            sorted_orders = sorted(orders, key=lambda x: x['time'], reverse=True)
            
            for i, order in enumerate(sorted_orders, 1):
                tags = ()
                if order['type'] == 'LIMIT':
                    tags = ('limit_order',)
                
                self.order_tree.insert('', 'end', values=(
                    i, # Serial number
                    datetime.fromtimestamp(order['time']/1000).strftime('%Y-%m-%d %H:%M:%S'),
                    order['symbol'],
                    order['type'],
                    order['side'],
                    order['price'],
                    order['origQty'],
                    order['status']
                ), tags=tags)
            
            # Color LIMIT orders in red
            self.order_tree.tag_configure('limit_order', foreground='#F44336')
                
        except Exception as e:
            self.show_notification("Refresh Failed", f"Failed to refresh orders: {str(e)}", "error")

    def auto_refresh_orders(self):
        """Automatically refresh orders every 30 seconds"""
        if not self.stop_threads:
            self.refresh_orders()
            self.root.after(30000, self.auto_refresh_orders)
    
    def on_closing(self):
        """Clean up and close the application"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.stop_threads = True
            if hasattr(self, 'price_update_thread'):
                self.price_update_thread.join(timeout=1.0)
            self.root.destroy()

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

if __name__ == "__main__":
    app = TradingBotUI()
    app.run()
