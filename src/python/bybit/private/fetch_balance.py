import os
import time
import hmac
import hashlib
import requests
import json5

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
api_path = "/v5/account/wallet-balance"

# Request parameters
params = {
    "accountType": "UNIFIED"  # e.g., UNIFIED, CONTRACT, SPOT
}

# Current timestamp in milliseconds
timestamp = str(int(time.time() * 1000))

# Prepare the query string with parameters sorted by key
query_params = {
    "accountType": params["accountType"],
    "api_key": api_key,
    "timestamp": timestamp
}

sorted_query = "&".join([f"{k}={query_params[k]}" for k in sorted(query_params.keys())])

# Generate the HMAC SHA256 signature
signature = hmac.new(
    api_secret.encode('utf-8'),
    sorted_query.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Final URL with the signature
url = f"{endpoint}{api_path}?{sorted_query}&sign={signature}"

# Make the request
headers = {"Content-Type": "application/json"}
response = requests.get(url, headers=headers)

print(response.json())
