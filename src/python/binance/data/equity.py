import requests
import time
import hmac
import hashlib
import json5
import math
from pathlib import Path

# Load API keys and margin level from JSON5 file
home_dir = Path.home()
with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-binance.json", "r") as file:
    config = json5.load(file)

API_KEY = config.get("key")
SECRET_KEY = config.get("secret")
MARGIN_LEVEL = float(config.get("margin", 1))  # Default to 1 if margin is not set

equity_filename = "../../../view/output/equity.txt" 

BASE_URL = 'https://api.binance.com'

def get_margin_account_info():
    try:
        # Generate the query string
        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'

        # Sign the query string
        signature = hmac.new(SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()

        # Add signature to the query string
        query_string += f'&signature={signature}'

        # Send the request
        headers = {'X-MBX-APIKEY': API_KEY}
        response = requests.get(f'{BASE_URL}/sapi/v1/margin/account', headers=headers, params=query_string)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def calculate_equity_with_margin(margin_account_info):
    try:
        # Extract total collateral value
        total_collateral = float(margin_account_info.get("totalCollateralValueInUSDT", 0))

        # Divide by the margin level
        raw_equity = total_collateral / MARGIN_LEVEL

        # Round down using floor
        total_equity = math.floor(raw_equity)
        return total_equity
    except Exception as e:
        print(f"An error occurred while calculating equity: {e}")
        return None

def log_equity_to_file(equity):
    try:
        # Get the current Unix timestamp
        timestamp = int(time.time())

        # Open the file in append mode and write the timestamp and equity value
        with open(equity_filename, "a") as file:
            file.write(f"{timestamp},{equity}\n")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")

# Main execution
margin_account_info = get_margin_account_info()
if margin_account_info:
    total_equity = calculate_equity_with_margin(margin_account_info)
    if total_equity is not None:
        print(f"Total Equity (USDT): {total_equity}")
        log_equity_to_file(total_equity)
