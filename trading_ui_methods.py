import customtkinter as ctk
from datetime import datetime

def show_notification(self, title, message, color="black"):
    """Show a notification popup"""
    notification_window = ctk.CTkToplevel(self.root)
    notification_window.title(title)
    notification_window.geometry("300x150")
    
    # Center the window
    x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
    y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
    notification_window.geometry(f"+{x}+{y}")
    
    # Message
    ctk.CTkLabel(
        notification_window, 
        text=message,
        text_color=color,
        wraplength=250
    ).pack(pady=20)
    
    # Close button
    ctk.CTkButton(
        notification_window,
        text="OK",
        command=notification_window.destroy
    ).pack(pady=10)
    
    # Auto-close after 5 seconds
    self.root.after(5000, notification_window.destroy)

def update_order_status(self, order):
    """Update order status in the treeview"""
    # First, try to find existing order
    for item in self.order_tree.get_children():
        if self.order_tree.item(item)['values'][0] == order['orderId']:
            # Update existing order
            self.order_tree.item(item, values=(
                datetime.now().strftime('%H:%M:%S'),
                order['symbol'],
                order['type'],
                order['side'],
                order.get('price', 'MARKET'),
                order['origQty'],
                order['status']
            ))
            return
    
    # If not found, insert new order
    self.order_tree.insert('', 0, values=(
        datetime.now().strftime('%H:%M:%S'),
        order['symbol'],
        order['type'],
        order['side'],
        order.get('price', 'MARKET'),
        order['origQty'],
        order['status']
    ))

def refresh_orders(self):
    """Refresh the orders display"""
    try:
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # Get both open and recent orders
        open_orders = self.client.get_open_orders()
        recent_orders = self.client.get_recent_trades(symbol='BTCUSDT', limit=10)
        
        # Add open orders
        for order in open_orders:
            self.update_order_status(order)
        
        # Add recent trades
        for trade in recent_orders:
            self.order_tree.insert('', 'end', values=(
                datetime.fromtimestamp(trade['time']/1000).strftime('%H:%M:%S'),
                trade['symbol'],
                'MARKET',
                trade['isBuyer'] and 'BUY' or 'SELL',
                trade['price'],
                trade['qty'],
                'EXECUTED'
            ))
        
        self.last_refresh_label.configure(
            text=f"Last refresh: {datetime.now().strftime('%H:%M:%S')}"
        )
    except Exception as e:
        self.show_notification("Error", f"Failed to refresh orders: {str(e)}", "red")
