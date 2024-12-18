import os
import json5
from pybit.unified_trading import HTTP

# Load credentials
home_dir = os.path.expanduser("~")
credentials_file = f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json"

with open(credentials_file, 'r') as f:
    creds = json5.load(f)

api_key = creds.get("key")
api_secret = creds.get("secret")

# Initialize client
client = HTTP(api_key=api_key, api_secret=api_secret, testnet=False)

# Borrow 1 USDT
# Using the "request" method to call the Bybit Unified Margin API endpoint directly
response = client.request(
    method="POST", 
    path="/unified/v3/private/borrow/create-borrow-order",
    data={
        "currency": "USDT",
        "amount": "1"
    }
)

print("Borrow response:", response)
