import os
import time
import hmac
import hashlib
import requests
import json5
import json
import math

# -------------------- INITIAL SETUP --------------------

home_dir = os.path.expanduser("~")
credentials_file = f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json"

with open(credentials_file, 'r') as f:
    creds = json5.load(f)

api_key = creds.get("key")
api_secret = creds.get("secret")
leverage = float(creds.get("margin", 1))  # leverage from credentials

endpoint = "https://api.bybit.com"

# -------------------- FETCH BALANCE --------------------
balance_path = "/v5/account/wallet-balance"
balance_params = {
    "accountType": "UNIFIED",
    "api_key": api_key,
    "timestamp": str(int(time.time() * 1000)),
    "recvWindow": "5000"
}

sorted_balance_params = dict(sorted(balance_params.items(), key=lambda x: x[0]))
balance_param_str = "&".join([f"{k}={v}" for k, v in sorted_balance_params.items()])

balance_signature = hmac.new(
    api_secret.encode('utf-8'),
    balance_param_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

balance_final_params = {**sorted_balance_params, "sign": balance_signature}

balance_response = requests.get(endpoint + balance_path, params=balance_final_params)
balance_data = balance_response.json()

if balance_data.get("retCode") != 0:
    print("Error fetching balance:", balance_data)
    exit()

# Extract USDT available balance from nested JSON structure
usdt_balance = 0.0
for account in balance_data["result"]["list"]:
    for coin_info in account["coin"]:
        if coin_info["coin"] == "USDT":
            # Depending on what you consider your tradeable balance, you might use:
            # - walletBalance: total funds in USDT
            # - availableToWithdraw: funds that can be withdrawn, often close to what can be traded
            # Here, we use walletBalance as a proxy for what's available to trade.
            usdt_balance = float(coin_info.get("walletBalance", 0.0))
            break
    if usdt_balance > 0:
        break

if usdt_balance <= 0:
    print("No USDT available to trade.")
    exit()

print(f"USDT available: {usdt_balance}")

# -------------------- FETCH CURRENT XRP PRICE --------------------
market_path = "/v5/market/tickers"
market_params = {
    "category": "linear",
    "symbol": "XRPUSDT",
    "api_key": api_key,
    "timestamp": str(int(time.time() * 1000)),
    "recvWindow": "5000"
}

sorted_market_params = dict(sorted(market_params.items(), key=lambda x: x[0]))
market_param_str = "&".join([f"{k}={v}" for k, v in sorted_market_params.items()])

market_signature = hmac.new(
    api_secret.encode('utf-8'),
    market_param_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

market_final_params = {**sorted_market_params, "sign": market_signature}
market_response = requests.get(endpoint + market_path, params=market_final_params)
market_data = market_response.json()

if market_data.get("retCode") != 0:
    print("Error fetching market price:", market_data)
    exit()

last_price = 0.0
if "result" in market_data and "list" in market_data["result"] and len(market_data["result"]["list"]) > 0:
    last_price = float(market_data["result"]["list"][0]["lastPrice"])
else:
    print("Could not fetch last price for XRPUSDT.")
    exit()

if last_price <= 0:
    print("Invalid last price.")
    exit()

# -------------------- CALCULATE QTY --------------------
max_notional = usdt_balance * leverage
qty = math.floor((max_notional / last_price) * 100) / 100.0

if qty <= 0:
    print("Calculated quantity is 0. Check balances or leverage.")
    exit()

# -------------------- SET LEVERAGE (OPTIONAL) --------------------
leverage_path = "/v5/position/set-leverage"
leverage_body = {
    "category": "linear",
    "symbol": "XRPUSDT",
    "buyLeverage": str(leverage),
    "sellLeverage": str(leverage),
    "api_key": api_key,
    "timestamp": str(int(time.time() * 1000)),
    "recvWindow": "5000"
}

sorted_leverage_body = dict(sorted(leverage_body.items(), key=lambda x: x[0]))
leverage_param_str = "&".join([f"{k}={v}" for k, v in sorted_leverage_body.items()])

leverage_signature = hmac.new(
    api_secret.encode('utf-8'),
    leverage_param_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

leverage_final_body = {**sorted_leverage_body, "sign": leverage_signature}

leverage_response = requests.post(endpoint + leverage_path, json=leverage_final_body)
leverage_resp_data = leverage_response.json()

if leverage_resp_data.get("retCode") != 0:
    print("Error setting leverage:", leverage_resp_data)
    # Decide if you want to continue or not
    # exit()

# -------------------- PLACE ORDER --------------------
order_path = "/v5/order/create"
order_body = {
    "category": "spot", 
    "symbol": "XRPUSDT",
    "side": "Buy",
    "orderType": "Market",
    "timeInForce": "GoodTillCancel",
    "qty": str(qty),
    "api_key": api_key,
    "timestamp": str(int(time.time() * 1000)),
    "recvWindow": "5000"
}

sorted_order_body = dict(sorted(order_body.items(), key=lambda x: x[0]))
order_param_str = "&".join([f"{k}={v}" for k, v in sorted_order_body.items()])

order_signature = hmac.new(
    api_secret.encode('utf-8'),
    order_param_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

order_final_body = {**sorted_order_body, "sign": order_signature}

order_response = requests.post(endpoint + order_path, json=order_final_body)
order_data = order_response.json()

if order_data.get("retCode") == 0:
    print("Order placed successfully!")
    print("Order response:", order_data)
else:
    print("Error placing order:", order_data)
