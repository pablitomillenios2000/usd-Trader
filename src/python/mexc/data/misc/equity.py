#!/usr/bin/env python3

import requests
import time
import hmac
import hashlib
import json5
import json
from pathlib import Path

# ------------------------------------------------------------------------------
# 1. LOAD API KEYS AND PAIR FROM JSON5
# ------------------------------------------------------------------------------
home_dir = Path.home()
with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
    config = json5.load(file)

API_KEY = config.get("key")
SECRET_KEY = config.get("secret")

# Example: if the JSON has "pair": "HBARUSDC"
# We'll parse that down to "HBAR" as the base token.
full_pair = config.get("pair", "HBARUSDC")

BASE_URL = 'https://api.binance.com'

# ------------------------------------------------------------------------------
# 2. PARSE THE BASE TOKEN FROM THE PAIR
# ------------------------------------------------------------------------------
def parse_base_token(pair_str):
    """
    If pair_str is like 'HBARUSDC', strip 'USDC' -> 'HBAR'.
    If the pair doesn't end with 'USDC', you can adapt the logic.
    """
    pair_str = pair_str.upper()
    if pair_str.endswith("USDC"):
        # remove trailing "USDC" -> "HBAR"
        return pair_str[:-4]
    # fallback if format is different
    return pair_str

# Extract base token from the pair (e.g. "HBARUSDC" -> "HBAR")
base_token = parse_base_token(full_pair)

# ------------------------------------------------------------------------------
# 3. SIGNING HELPER FOR BINANCE
# ------------------------------------------------------------------------------
def sign_query(query: str) -> str:
    return hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()

# ------------------------------------------------------------------------------
# 4. GET CROSS MARGIN ACCOUNT INFO
# ------------------------------------------------------------------------------
def get_cross_margin_account_info():
    """
    Fetch cross margin account info which shows net assets for each coin.
    """
    try:
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = sign_query(query_string)
        query_string += f"&signature={signature}"

        headers = {"X-MBX-APIKEY": API_KEY}
        url = f"{BASE_URL}/sapi/v1/margin/account"
        resp = requests.get(url, headers=headers, params=query_string)

        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"Error (cross margin): {resp.status_code}, {resp.text}")
            return None
    except Exception as e:
        print(f"Error fetching cross margin info: {e}")
        return None

# ------------------------------------------------------------------------------
# 5. MAIN EXECUTION
# ------------------------------------------------------------------------------
def main():
    account_info = get_cross_margin_account_info()
    if not account_info:
        print("Unable to retrieve cross margin account info.")
        return

    # The cross margin info is under account_info["userAssets"], which is a list
    user_assets = account_info.get("userAssets", [])

    # We want to filter for base token (e.g., "HBAR") + "USDC"
    # e.g., if base_token="HBAR", we want to see "HBAR" and "USDC"
    relevant_assets = [
        asset for asset in user_assets
        if asset["asset"] in [base_token.upper(), "USDC"]
    ]

    # Print the filtered information in JSON format
    print("\nFull Information for the Base Token and USDC:")
    print(json.dumps(relevant_assets, indent=4))

# ------------------------------------------------------------------------------
# 6. EXECUTE MAIN IF RUN DIRECTLY
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
