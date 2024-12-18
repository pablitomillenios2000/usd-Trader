import os
import time
import json5
import json
import math
from pybit.unified_trading import HTTP

# -------------------- INITIAL SETUP --------------------
home_dir = os.path.expanduser("~")
credentials_file = f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json"

with open(credentials_file, 'r') as f:
    creds = json5.load(f)

api_key = creds.get("key")
api_secret = creds.get("secret")
leverage = float(creds.get("margin", 1))  # desired leverage via borrowing

# Initialize the pybit Unified Trading client
from pybit.unified_trading import HTTP

client = HTTP(
    api_key=api_key,
    api_secret=api_secret,
    testnet=False  # Set to True if you're using testnet
)


# -------------------- FETCH BALANCE --------------------
print("Fetching balance...")
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
    print("No USDT available to trade. You may need to deposit first.")
    exit()

print(f"USDT available: {usdt_balance}")

# -------------------- FETCH CURRENT XRP PRICE --------------------
symbol = "XRPUSDT"
print("Fetching XRP price...")

# First try linear category
market_data = client.get_tickers(category="linear", symbol=symbol)

# If linear fails or no results, try spot
if market_data.get("retCode") != 0 or not market_data["result"].get("list"):
    market_data = client.get_tickers(category="spot", symbol=symbol)

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
    print(f"Attempting to borrow {borrow_amount} USDT for margin...")
    # pybit unified trading currently may not have a direct borrow method exposed.
    # If it does not, we may need to use the generic `call_endpoint` method.
    # The borrow endpoint is: /v5/crypto-loan/borrow
    # We'll try to call it directly via the generic method if supported by pybit version:
    borrow_response = client.call_endpoint(
        method="POST",
        endpoint="/v5/crypto-loan/borrow",
        params={
            "accountType": "UNIFIED",
            "coin": "USDT",
            "qty": str(borrow_amount)
        }
    )

    if borrow_response.get("retCode") != 0:
        print("Error borrowing funds:", borrow_response)
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
print("Placing margin order...")

# pybit's `submit_order` can be used for placing orders, 
# but margin orders might require specific parameters.
# As of current pybit versions, margin trading might be done by specifying `tradeMode="MARGIN"`.
# Check pybit docs if there's a direct method or if we should use call_endpoint.

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
    print("Order response:", json.dumps(order_response, indent=2))
else:
    print("Error placing margin order:", order_response)

# Optional: Implement repayment logic here (similar to borrowing)
