import requests
import time
import hmac
import hashlib
import json5
from pathlib import Path

# ------------------------------------------------------------------------------
# 1. LOAD API KEYS AND PAIR FROM JSON5
# ------------------------------------------------------------------------------
home_dir = Path.home()
with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
    config = json5.load(file)

API_KEY = config.get("key")
SECRET_KEY = config.get("secret")

# 📌 API Base URL
base_url = 'https://www.mexc.com/'

# 🧮 Function to get account equity
def get_account_equity():
    endpoint = '/open/api/v2/account/info'
    url = base_url + endpoint

    # Timestamp for the request
    timestamp = int(time.time() * 1000)

    # Parameters for the request
    params = {
        'api_key': API_KEY,
        'req_time': timestamp
    }

    # Create the signature
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params['sign'] = signature

    # Headers
    headers = {
        'X-MEXC-APIKEY': API_KEY
    }

    try:
        # Send the request with a timeout
        response = requests.get(url, headers=headers, params=params, timeout=10)

        # Check response status
        if response.status_code == 200:
            data = response.json()
            equity = data['data']['equity']
            print(f"Account Equity: {equity} USDT")
        else:
            print(f"Error: {response.status_code}, {response.text}")
    except requests.exceptions.Timeout:
        print("Request timed out. The server took too long to respond.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# 🔄 Call the function
get_account_equity()
