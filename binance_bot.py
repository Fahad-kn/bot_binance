# stage4_bot.py
import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE = "https://testnet.binancefuture.com"  # TESTNET base

class BinanceFuturesBot:
    def __init__(self, api_key, api_secret, base_url=DEFAULT_BASE):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-MBX-APIKEY": self.api_key}

    # ---------- Signing helpers ----------
    def _sign(self, params: dict):
        params = dict(params)  # copy to avoid mutation
        params["timestamp"] = int(time.time() * 1000)
        qs = urlencode(params)
        sig = hmac.new(self.api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        return qs + "&signature=" + sig

    def _get(self, path, params=None, signed=False):
        params = params or {}
        if signed:
            qs = self._sign(params)
            url = f"{self.base_url}{path}?{qs}"
        else:
            url = f"{self.base_url}{path}"
            if params:
                url = f"{url}?{urlencode(params)}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def _post(self, path, params=None, signed=False):
        params = params or {}
        if signed:
            qs = self._sign(params)
            url = f"{self.base_url}{path}?{qs}"
        else:
            url = f"{self.base_url}{path}"
            if params:
                url = f"{url}?{urlencode(params)}"
        r = requests.post(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def _delete(self, path, params=None, signed=False):
        params = params or {}
        if signed:
            qs = self._sign(params)
            url = f"{self.base_url}{path}?{qs}"
        else:
            url = f"{self.base_url}{path}"
            if params:
                url = f"{url}?{urlencode(params)}"
        r = requests.delete(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    # ---------- Basic public methods ----------
    def get_server_time(self):
        return self._get("/fapi/v1/time")

    def get_ticker_price(self, symbol):
        # public endpoint, no signing required
        return self._get("/fapi/v1/ticker/price", params={"symbol": symbol})

    # ---------- Account & position methods (signed) ----------
    def get_account_balance(self):
        """GET /fapi/v2/balance - returns list of balances per asset (signed)."""
        return self._get("/fapi/v2/balance", signed=True)

    def get_account_info(self):
        """GET /fapi/v2/account - account summary (signed)."""
        return self._get("/fapi/v2/account", signed=True)

    def get_position_risk(self, symbol=None):
        """GET /fapi/v2/positionRisk - returns positions (signed)."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._get("/fapi/v2/positionRisk", params=params, signed=True)

    # ---------- Trading helpers ----------
    def place_market_order(self, symbol, side, quantity):
        params = {"symbol": symbol, "side": side.upper(), "type": "MARKET", "quantity": quantity}
        return self._post("/fapi/v1/order", params=params, signed=True)

    def place_limit_order(self, symbol, side, quantity, price, time_in_force="GTC"):
        params = {
            "symbol": symbol, "side": side.upper(), "type": "LIMIT",
            "quantity": quantity, "price": str(price), "timeInForce": time_in_force
        }
        return self._post("/fapi/v1/order", params=params, signed=True)

    def get_order_status(self, symbol, order_id):
        params = {"symbol": symbol, "orderId": order_id}
        return self._get("/fapi/v1/order", params=params, signed=True)

    def cancel_order(self, symbol, order_id):
        params = {"symbol": symbol, "orderId": order_id}
        return self._delete("/fapi/v1/order", params=params, signed=True)

    # ---------- Simple trading loop example ----------
    def simple_trading_loop(self, symbol, buy_price_threshold, buy_qty, poll_interval=5, max_attempts=60):
        """
        Educational demo (Testnet):
        - Polls the current ticker price every poll_interval seconds.
        - If price <= buy_price_threshold, place a MARKET BUY of buy_qty.
        - After order executed, check position via positionRisk and then place opposite MARKET order
          to close that position (same absolute positionAmt).
        - Stops after closing or after max_attempts polling attempts.
        WARNING: This is a learning demo. Use only on TESTNET with small quantities.
        """
        attempts = 0
        print(f"[Loop] watching {symbol} for price <= {buy_price_threshold} ...")
        while attempts < max_attempts:
            attempts += 1
            try:
                ticker = self.get_ticker_price(symbol)
                price = float(ticker["price"])
                print(f"[{attempts}] Current price: {price}")
            except Exception as e:
                print("Error fetching price:", e)
                time.sleep(poll_interval)
                continue

            if price <= buy_price_threshold:
                print(f"Price condition met ({price} <= {buy_price_threshold}). Placing market BUY {buy_qty}...")
                order = self.place_market_order(symbol, "BUY", buy_qty)
                print("Order response:", order)

                # Wait a short time for execution to settle
                time.sleep(1.5)

                # Check positions for this symbol
                positions = self.get_position_risk(symbol=symbol)
                # positions is a list; find the entry for the symbol
                pos = None
                for p in positions:
                    if p.get("symbol") == symbol:
                        pos = p
                        break

                if not pos:
                    print("Warning: no position info found. Exiting loop.")
                    return

                position_amt = float(pos.get("positionAmt", "0"))
                print("PositionAmt:", position_amt, "entryPrice:", pos.get("entryPrice"),
                      "unRealizedProfit:", pos.get("unRealizedProfit"))

                if position_amt == 0:
                    print("No open position (positionAmt=0). Nothing to close.")
                    return

                # Determine opposite side and qty to close (abs of positionAmt)
                side_to_close = "SELL" if position_amt > 0 else "BUY"
                qty_to_close = abs(position_amt)

                print(f"Closing position by placing MARKET {side_to_close} for qty {qty_to_close} ...")
                close_order = self.place_market_order(symbol, side_to_close, qty_to_close)
                print("Close order response:", close_order)

                print("Done — position closed (or close order sent). Exiting loop.")
                return

            # not met
            time.sleep(poll_interval)

        print("Max attempts reached, exiting loop without trades.")
        from stage4_bot import BinanceFuturesBot, load_dotenv
import os
load_dotenv()
bot = BinanceFuturesBot(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))

print("server time:", bot.get_server_time())
print("balances:", bot.get_account_balance())         # GET /fapi/v2/balance. :contentReference[oaicite:7]{index=7}
print("positions:", bot.get_position_risk())          # GET /fapi/v2/positionRisk. :contentReference[oaicite:8]{index=8}

# Demo loop: only run this on testnet. Example: buy if price drops below 30000
bot.simple_trading_loop(symbol="BTCUSDT", buy_price_threshold=30000, buy_qty=0.001, poll_interval=5)

