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
leverage = float(creds.get("margin", 1))

# Bybit V5 endpoints
endpoint = "https://api.bybit.com"
balance_path = "/v5/account/wallet-balance"
balance_url = f"{endpoint}{balance_path}"

balance_params = {
    "accountType": "UNIFIED",
    "api_key": api_key,
    "timestamp": str(int(time.time() * 1000)),
    "recvWindow": "5000"
}

# Sort parameters by key
sorted_balance_params = dict(sorted(balance_params.items(), key=lambda x: x[0]))
balance_param_str = "&".join([f"{k}={v}" for k, v in sorted_balance_params.items()])

# Sign the request
balance_signature = hmac.new(
    api_secret.encode('utf-8'),
    balance_param_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

balance_final_params = {**sorted_balance_params, "sign": balance_signature}

# Request balance
balance_response = requests.get(balance_url, params=balance_final_params)

# Debug: Check raw response
print("Status code:", balance_response.status_code)
print("Raw response:", balance_response.text)

# Attempt to parse JSON after verifying content
try:
    balance_data = balance_response.json()
except ValueError:
    print("Response is not valid JSON.")
    print("Response text:", balance_response.text)
    exit()

if balance_data.get("retCode") != 0:
    print("Error fetching balance:", balance_data)
    exit()

# Once you have the balance data parsed correctly, proceed with the rest of your logic...
