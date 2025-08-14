import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from datetime import datetime

# Load API keys from .env
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

BASE_URL = "https://testnet.binancefuture.com"

class BinanceBot:
    def __init__(self):
        self.headers = {"X-MBX-APIKEY": API_KEY}
        self.log_file = "trading_log.txt"

    def log(self, message):
        """Write logs with timestamp."""
        with open(self.log_file, "a") as f:
            f.write(f"[{datetime.now()}] {message}\n")
        print(message)  # Also print to console

    def sign_request(self, params):
        """Sign request using HMAC SHA256."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        return query_string + "&signature=" + signature

    def server_time(self):
        url = f"{BASE_URL}/fapi/v1/time"
        r = requests.get(url)
        self.log(f"Server Time: {r.json()}")
        return r.json()

    def place_market_order(self, symbol, side, quantity):
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity
        }
        signed = self.sign_request(params)
        r = requests.post(f"{BASE_URL}/fapi/v1/order?{signed}", headers=self.headers)
        self.log(f"Market Order Response: {r.json()}")
        return r.json()

    def get_order_status(self, symbol, order_id):
        params = {"symbol": symbol, "orderId": order_id}
        signed = self.sign_request(params)
        r = requests.get(f"{BASE_URL}/fapi/v1/order?{signed}", headers=self.headers)
        self.log(f"Order Status: {r.json()}")
        return r.json()

    def cancel_order(self, symbol, order_id):
        params = {"symbol": symbol, "orderId": order_id}
        signed = self.sign_request(params)
        r = requests.delete(f"{BASE_URL}/fapi/v1/order?{signed}", headers=self.headers)
        self.log(f"Cancel Order Response: {r.json()}")
        return r.json()

# =============================
# Example usage
# =============================
if __name__ == "__main__":
    bot = BinanceBot()

    # Step 1: Get server time
    bot.server_time()

    # Step 2: Place market buy order
    order = bot.place_market_order("BTCUSDT", "BUY", 0.001)
    order_id = order.get("orderId")

    if order_id:
        # Step 3: Get order status
        bot.get_order_status("BTCUSDT", order_id)

        # Step 4: Cancel order (for testing)
        bot.cancel_order("BTCUSDT", order_id)
