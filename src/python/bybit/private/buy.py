import os
import time
import hmac
import hashlib
import requests
import json5
import json

# Set your home directory path accordingly
home_dir = os.path.expanduser("~")

# Path to your JSON file containing API credentials
credentials_file = f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json"

# Load API credentials from JSON5 file
with open(credentials_file, 'r') as f:
    creds = json5.load(f)

api_key = creds.get("key")
api_secret = creds.get("secret")

# Bybit V5 endpoints
endpoint = "https://api.bybit.com"
api_path = "/v5/order/create"
url = f"{endpoint}{api_path}"

# Prepare order parameters
params = {
    "api_key": api_key,
    "category": "spot",
    "orderType": "Market",
    "qty": "1",
    "recvWindow": "5000",
    "side": "Buy",
    "symbol": "XRPUSDT",
    "timeInForce": "GTC",
    "timestamp": str(int(time.time() * 1000))
}

# Sort parameters by key
sorted_params = dict(sorted(params.items(), key=lambda x: x[0]))

# Create the query string
param_str = "&".join([f"{k}={v}" for k, v in sorted_params.items()])

# Generate the signature
signature = hmac.new(
    api_secret.encode('utf-8'),
    param_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Add the signature to the final request body
final_body = {**sorted_params, "sign": signature}

headers = {"Content-Type": "application/json"}

# Make the POST request
response = requests.post(url, headers=headers, data=json.dumps(final_body))
print(response.json())
