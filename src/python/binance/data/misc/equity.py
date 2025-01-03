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
                #print(json.dumps(account_info, indent=4))

                # Filter assets for SUI and USDC
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


# Calculate equity using USDC netAsset
def calculate_equity_from_usdc(margin_account_info):
    try:
        user_assets = margin_account_info.get("userAssets", [])
        usdc_asset = next((asset for asset in user_assets if asset["asset"] == "USDC"), None)

        if usdc_asset:
            net_asset_usdc = float(usdc_asset.get("netAsset", 0))
            return math.floor(net_asset_usdc)
        else:
            print("USDC asset not found in margin account.")
            return None
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
margin_account_info = get_margin_account_info()

if margin_account_info:
    total_equity = calculate_equity_from_usdc(margin_account_info)
    if total_equity is not None:
        print(f"Total Equity (USDC): {total_equity}")
        log_equity_to_file(total_equity)
