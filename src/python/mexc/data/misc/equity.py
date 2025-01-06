import requests
import time
import hmac
import hashlib
import json5
from pathlib import Path

# Load API keys
home_dir = Path.home()
with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
    config = json5.load(file)

API_KEY = config.get("key")
SECRET_KEY = config.get("secret")

# Base URL
base_url = 'https://www.mexc.com/'

# 🧮 Function to get server time
def get_server_time():
    url = base_url + 'open/api/v2/common/timestamp'
    response = requests.get(url)
    if response.status_code == 200:
        print(response.json()['data'])
        return response.json()['data']
    else:
        raise Exception(f"Failed to get server time: {response.status_code}, {response.text}")

# 🧮 Function to get account equity
def get_account_equity():
    endpoint = '/open/api/v2/account/info'
    url = base_url + endpoint

    # Get MEXC server time
    server_time = get_server_time()

    # Parameters for the request
    params = {
        'api_key': API_KEY,
        'req_time': int(server_time)  # Ensure it's an integer
    }


    # Create the query string in sorted order
    query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params)])
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
