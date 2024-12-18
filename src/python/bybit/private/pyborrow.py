import time
import hmac
import hashlib
import requests
import math
import json
import os
import json5

from pybit.unified_trading import HTTP

home_dir = os.path.expanduser("~")
credentials_file = f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json"

with open(credentials_file, 'r') as f:
    creds = json5.load(f)

api_key = creds.get("key")
api_secret = creds.get("secret")
leverage = float(creds.get("margin", 1))

client = HTTP(
    api_key=api_key,
    api_secret=api_secret,
    testnet=False
)

def sign_request(secret, params):
    # Sort params
    sorted_params = dict(sorted(params.items(), key=lambda x: x[0]))
    # Generate query string
    param_str = "&".join([f"{k}={v}" for k, v in sorted_params.items()])
    # Sign
    signature = hmac.new(
        secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return sorted_params, signature

# -------------------- FETCH BALANCE --------------------
balance_response = client.get_wallet_balance(accountType="UNIFIED")
if balance_response.get("retCode") != 0:
    print("Error fetching balance:", balance_response)
    exit()

usdt_balance = 0.0
for account in balance_response["result"]["list"]:
    for coin_info in account["coin"]:
        if coin_info["coin"] == "USDT":
            usdt_balance = float(coin_info.get("walletBalance", 0.0))
            break
    if usdt_balance > 0:
        break

if usdt_balance <= 0:
    print("No USDT available.")
    exit()

print(f"USDT available: {usdt_balance}")

# -------------------- FETCH XRP PRICE --------------------
symbol = "XRPUSDT"
market_data = client.get_tickers(category="linear", symbol=symbol)
if market_data.get("retCode") != 0 or not market_data["result"].get("list"):
    market_data = client.get_tickers(category="spot", symbol=symbol)

if market_data.get("retCode") != 0:
    print("Error fetching price:", market_data)
    exit()

if "result" in market_data and "list" in market_data["result"] and len(market_data["result"]["list"]) > 0:
    last_price = float(market_data["result"]["list"][0]["lastPrice"])
    print(f"Last price: {last_price}")
else:
    print("Could not fetch last price.")
    exit()

if last_price <= 0:
    print("Invalid last price.")
    exit()

# -------------------- CALCULATE QTY & BORROW FUNDS --------------------
current_balance = usdt_balance
desired_total = current_balance * leverage
borrow_amount = desired_total - current_balance

endpoint = "https://api.bybit.com"

if borrow_amount > 0:
    print(f"Attempting to borrow {borrow_amount} USDT for margin...")
    borrow_path = "/v5/crypto-loan/borrow"
    borrow_body = {
        "accountType": "UNIFIED",
        "api_key": api_key,
        "coin": "USDT",
        "qty": str(borrow_amount),
        "timestamp": str(int(time.time() * 1000))
    }

    sorted_borrow_body, borrow_signature = sign_request(api_secret, borrow_body)
    borrow_final_body = {**sorted_borrow_body, "sign": borrow_signature}

    borrow_response = requests.post(endpoint + borrow_path, json=borrow_final_body)
    try:
        borrow_data = borrow_response.json()
    except json.JSONDecodeError as e:
        print("Failed to decode borrow response:", borrow_response.text)
        raise e

    if borrow_data.get("retCode") != 0:
        print("Error borrowing funds:", borrow_data)
        exit()
    else:
        print(f"Borrowed {borrow_amount} USDT successfully!")
        current_balance += borrow_amount
else:
    print("No need to borrow funds, leverage is 1x or less.")

qty = (current_balance / last_price)
qty = math.floor(qty * 100) / 100.0  # two decimal places
if qty <= 0:
    print("Calculated quantity is 0.")
    exit()

print(f"Calculated quantity to buy: {qty}")

# -------------------- PLACE MARGIN ORDER --------------------
order_response = client.submit_order(
    category="spot",
    symbol=symbol,
    side="Buy",
    orderType="Market",
    timeInForce="GTC",
    qty=str(qty),
    tradeMode="MARGIN"
)

if order_response.get("retCode") == 0:
    print("Margin order placed successfully!")
    print(json.dumps(order_response, indent=2))
else:
    print("Error placing margin order:", order_response)
