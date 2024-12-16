import time
import hmac
import hashlib
import requests
import json5
from urllib.parse import urlencode

with open("../../../dist/apikey-binance.json", "r") as file:
    config = json5.load(file)
    if "pair" not in config:
        raise ValueError("The 'pair' key is missing in apikey-binance.json")
    key = config["key"]
    secret = config["secret"] # Convert to lowercase for Binance's WebSocket API


# Replace these with your actual API credentials
API_KEY = key
API_SECRET = secret

BASE_URL = "https://api.binance.com"  # For production. Use "https://testnet.binance.vision" for testnet.

def sign_request(params, secret_key):
    query_string = urlencode(params)
    signature = hmac.new(
        secret_key.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return signature

def get_max_borrowable_amount(asset):
    endpoint = "/sapi/v1/margin/maxBorrowable"
    timestamp = int(time.time() * 1000)

    params = {
        "asset": asset,
        "timestamp": timestamp
    }

    # Sign the request
    signature = sign_request(params, API_SECRET)
    params["signature"] = signature

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    url = BASE_URL + endpoint
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        # The response typically looks like: {"amount":"123.456789"}
        return float(data["amount"])
    else:
        print("Error fetching max borrowable:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    # Example: Get maximum borrowable amount for USDC
    asset_to_check = "USDC"  # Change this to the asset you want to check.
    max_borrow = get_max_borrowable_amount(asset_to_check)
    if max_borrow is not None:
        print(f"Maximum borrowable {asset_to_check} amount: {max_borrow}")
    else:
        print("Could not retrieve maximum borrowable amount.")
