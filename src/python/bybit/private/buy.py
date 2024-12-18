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
leverage = float(creds.get("margin", 1))  # desired leverage via borrowing

endpoint = "https://api.bybit.com"

def sign_request(secret, params):
    sorted_params = dict(sorted(params.items(), key=lambda x: x[0]))
    param_str = "&".join([f"{k}={v}" for k, v in sorted_params.items()])
    signature = hmac.new(
        secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return sorted_params, signature

# -------------------- FETCH BALANCE --------------------
balance_path = "/v5/account/wallet-balance"
balance_params = {
    "accountType": "UNIFIED",
    "api_key": api_key,
    "timestamp": str(int(time.time() * 1000)),
    "recvWindow": "5000"
}
sorted_balance_params, balance_signature = sign_request(api_secret, balance_params)
balance_final_params = {**sorted_balance_params, "sign": balance_signature}

print("Fetching balance...")
balance_response = requests.get(endpoint + balance_path, params=balance_final_params)
try:
    balance_data = balance_response.json()
except json.JSONDecodeError as e:
    print("Failed to decode JSON for balance response.")
    print("Status code:", balance_response.status_code)
    print("Response text:", balance_response.text)
    raise e

if balance_data.get("retCode") != 0:
    print("Error fetching balance:", balance_data)
    exit()

usdt_balance = 0.0
for account in balance_data["result"]["list"]:
    for coin_info in account["coin"]:
        if coin_info["coin"] == "USDT":
            usdt_balance = float(coin_info.get("walletBalance", 0.0))
            break
    if usdt_balance > 0:
        break

if usdt_balance <= 0:
    print("No USDT available to trade. You may need to deposit first.")
    exit()

print(f"USDT available: {usdt_balance}")

# -------------------- FETCH CURRENT XRP PRICE --------------------
symbol = "XRPUSDT"
market_path = "/v5/market/tickers"

def fetch_price(symbol):
    # Try linear category first
    market_params = {
        "api_key": api_key,
        "category": "linear",
        "symbol": symbol,
        "timestamp": str(int(time.time() * 1000)),
        "recvWindow": "5000"
    }
    sorted_market_params, market_signature = sign_request(api_secret, market_params)
    market_final_params = {**sorted_market_params, "sign": market_signature}

    response = requests.get(endpoint + market_path, params=market_final_params)
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print("Failed to decode JSON for market (linear) response.")
        print("Status code:", response.status_code)
        print("Response text:", response.text)
        raise e

    # If linear fails, try spot category
    if data.get("retCode") != 0 or "list" not in data.get("result", {}) or len(data["result"]["list"]) == 0:
        market_params["category"] = "spot"
        sorted_market_params, market_signature = sign_request(api_secret, market_params)
        market_final_params = {**sorted_market_params, "sign": market_signature}

        response = requests.get(endpoint + market_path, params=market_final_params)
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print("Failed to decode JSON for market (spot) response.")
            print("Status code:", response.status_code)
            print("Response text:", response.text)
            raise e

    return data

print("Fetching XRP price...")
market_data = fetch_price(symbol)
if market_data.get("retCode") != 0:
    print("Error fetching market price:", market_data)
    exit()

if "result" in market_data and "list" in market_data["result"] and len(market_data["result"]["list"]) > 0:
    last_price = float(market_data["result"]["list"][0]["lastPrice"])
    print(f"Last price: {last_price}")
else:
    print("Could not fetch last price for XRPUSDT.")
    exit()

if last_price <= 0:
    print("Invalid last price.")
    exit()

# -------------------- CALCULATE QTY & BORROW FUNDS --------------------
current_balance = usdt_balance
desired_total = current_balance * leverage
borrow_amount = desired_total - current_balance



if borrow_amount > 0:
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

    print(f"Attempting to borrow {borrow_amount} USDT for margin...")
    borrow_response = requests.post(endpoint + borrow_path, json=borrow_final_body)
    print("Borrow status code:", borrow_response.status_code)
    print("Borrow raw response text:", borrow_response.text)

    try:
        borrow_data = borrow_response.json()
    except json.JSONDecodeError as e:
        print("Failed to decode JSON for borrow response.")
        print("Status code:", borrow_response.status_code)
        print("Response text:", borrow_response.text)
        raise e

    if borrow_data.get("retCode") != 0:
        print("Error borrowing funds:", borrow_data)
        # If the API returned a non-standard response, consider that borrow might not be available.
        exit()
    else:
        print(f"Borrowed {borrow_amount} USDT successfully!")
        current_balance += borrow_amount
else:
    print("No need to borrow funds, leverage is 1x or less.")

qty = (current_balance / last_price)
qty = math.floor(qty * 100) / 100.0  # adjust for 2 decimal places

if qty <= 0:
    print("Calculated quantity is 0. Check balances or last price.")
    exit()

print(f"Calculated quantity to buy: {qty}")

# -------------------- PLACE MARGIN ORDER --------------------
order_path = "/v5/order/create"
order_body = {
    "category": "spot",
    "symbol": symbol,
    "side": "Buy",
    "orderType": "Market",
    "timeInForce": "GTC",
    "qty": str(qty),
    "tradeMode": "MARGIN",
    "api_key": api_key,
    "timestamp": str(int(time.time() * 1000)),
    "recvWindow": "5000"
}
sorted_order_body, order_signature = sign_request(api_secret, order_body)
order_final_body = {**sorted_order_body, "sign": order_signature}

print("Placing margin order...")
order_response = requests.post(endpoint + order_path, json=order_final_body)
print("Order status code:", order_response.status_code)
print("Order raw response text:", order_response.text)

try:
    order_data = order_response.json()
except json.JSONDecodeError as e:
    print("Failed to decode JSON for order response.")
    print("Status code:", order_response.status_code)
    print("Response text:", order_response.text)
    raise e

if order_data.get("retCode") == 0:
    print("Margin order placed successfully!")
    print("Order response:", json.dumps(order_data, indent=2))
else:
    print("Error placing margin order:", order_data)

# Optional: Implement repayment logic here.
