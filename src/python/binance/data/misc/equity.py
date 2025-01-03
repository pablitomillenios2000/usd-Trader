import requests
import time
import hmac
import hashlib
import json5
import json
import math
from pathlib import Path

# Load API keys and margin level from JSON5 file
home_dir = Path.home()
with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
    config = json5.load(file)

API_KEY = config.get("key")
SECRET_KEY = config.get("secret")
MARGIN_LEVEL = float(config.get("margin", 1))  # Default to 1 if margin is not set

equity_filename = "../../../view/output/equity.txt"
BASE_URL = 'https://api.binance.com'
debug_mode = True  # Enable debug mode


# Get SUI price in USDC
def get_sui_price():
    try:
        response = requests.get(f'{BASE_URL}/api/v3/ticker/price', params={'symbol': 'SUIUSDC'})
        if response.status_code == 200:
            price_data = response.json()
            return float(price_data.get("price", 0))
        else:
            print(f"Error fetching SUI/USDC price: {response.status_code}, {response.text}")
            return 0
    except Exception as e:
        print(f"An error occurred while fetching SUI price: {e}")
        return 0


# Get margin account info
def get_margin_account_info():
    try:
        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'
        signature = hmac.new(SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        query_string += f'&signature={signature}'
        headers = {'X-MBX-APIKEY': API_KEY}
        response = requests.get(f'{BASE_URL}/sapi/v1/margin/account', headers=headers, params=query_string)
        if response.status_code == 200:
            account_info = response.json()

            # Debug output: Print all margin account info
            if debug_mode:
                print("\nDEBUG: Full Margin Account Info (Filtered for SUI and USDC):")
                filtered_assets = [asset for asset in account_info.get("userAssets", []) if asset["asset"] in ["SUI", "USDC"]]
                print("\nDEBUG: Filtered Assets (SUI and USDC):")
                print(json.dumps(filtered_assets, indent=4))

            return account_info
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Calculate equity using netAsset of USDC and SUI
def calculate_equity(margin_account_info, sui_price):
    try:
        user_assets = margin_account_info.get("userAssets", [])
        usdc_asset = next((asset for asset in user_assets if asset["asset"] == "USDC"), None)
        sui_asset = next((asset for asset in user_assets if asset["asset"] == "SUI"), None)

        net_asset_usdc = float(usdc_asset.get("netAsset", 0)) if usdc_asset else 0
        net_asset_sui = float(sui_asset.get("netAsset", 0)) if sui_asset else 0

        # Calculate total equity
        total_equity = net_asset_usdc + (net_asset_sui * sui_price)
        return math.floor(total_equity)
    except Exception as e:
        print(f"An error occurred while calculating equity: {e}")
        return None


# Log equity to file
def log_equity_to_file(equity):
    try:
        timestamp = int(time.time())
        with open(equity_filename, "a") as file:
            file.write(f"{timestamp},{equity}\n")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


# Main execution
sui_price = get_sui_price()
margin_account_info = get_margin_account_info()

if margin_account_info:
    total_equity = calculate_equity(margin_account_info, sui_price)
    if total_equity is not None:
        print(f"Total Equity (USDC): {total_equity}")
        log_equity_to_file(total_equity)
