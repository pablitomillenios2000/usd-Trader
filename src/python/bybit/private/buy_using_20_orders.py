import sys
import json5
import math
import time
import hmac
import hashlib
import requests
from pathlib import Path

print("Executing Margin BUY order script with Bybit...")

API_BASE_URL = "https://api.bybit.com"  # Bybit mainnet API
home_dir = Path.home()

def generate_signature(api_secret, params):
    """Generate HMAC SHA256 signature."""
    query_string = "&".join([f"{key}={params[key]}" for key in sorted(params)])
    return hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def make_request(endpoint, api_key, api_secret, method="GET", params=None):
    """Make an authenticated request to Bybit API."""
    if params is None:
        params = {}
    params['api_key'] = api_key
    params['timestamp'] = int(time.time() * 1000)
    params['sign'] = generate_signature(api_secret, params)

    if method == "GET":
        response = requests.get(f"{API_BASE_URL}{endpoint}", params=params)
    elif method == "POST":
        response = requests.post(f"{API_BASE_URL}{endpoint}", data=params)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    return response.json()

def main():
    try:
        # Step 1: Read API keys and configuration from the JSON file
        with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
            api_keys = json5.load(file)

        api_key = api_keys.get('key')
        api_secret = api_keys.get('secret')
        trading_pair = api_keys.get('pair')
        leverage_strength = api_keys.get('margin', 1)  # Default leverage to 1 if not specified

        if not all([api_key, api_secret, trading_pair]):
            raise ValueError("API key, secret, or trading pair not found in the configuration file.")

        # Step 2: Fetch the USDT balance from the spot account
        account_info = make_request("/spot/v1/account", api_key, api_secret)
        USDT_balance = 0.0
        for asset in account_info['result']['balances']:
            if asset['coin'] == 'USDT':
                USDT_balance = float(asset['free'])
                break

        if USDT_balance <= 0:
            raise Exception("Insufficient USDT balance to execute the order.")

        # Step 3: Calculate the total amount needed based on leverage
        target_balance = USDT_balance * leverage_strength
        borrow_amount = target_balance - USDT_balance

        # Step 4: Check the maximum amount that can be borrowed
        loan_info_resp = make_request("/spot/v1/cross-margin/loan-info", api_key, api_secret, params={'coin': 'USDT'})
        max_borrowable = float(loan_info_resp['result']['loanable'])

        # Step 5: Adjust borrow amount if it exceeds the maximum borrowable amount
        if borrow_amount > max_borrowable:
            print("Borrow amount exceeds the maximum borrowable amount.")
            print(f"Borrow amount requested: {borrow_amount} USDT, Maximum borrowable: {max_borrowable} USDT")
            borrow_amount = 0

        # Step 6: Borrow USDT if required and within limits
        if borrow_amount > 0:
            borrow_amount = math.floor(borrow_amount)
            borrow_resp = make_request(
                "/spot/v1/cross-margin/loan",
                api_key,
                api_secret,
                method="POST",
                params={'coin': 'USDT', 'qty': str(borrow_amount)}
            )
            if borrow_resp.get('ret_code') != 0:
                raise Exception(f"Failed to borrow USDT: {borrow_resp.get('ret_msg')}")
            print(f"Successfully borrowed {borrow_amount} USDT.")

            # Update USDT_balance after borrow
            time.sleep(1)
            account_info = make_request("/spot/v1/account", api_key, api_secret)
            for asset in account_info['result']['balances']:
                if asset['coin'] == 'USDT':
                    USDT_balance = float(asset['free'])
                    break

        # Step 7: Calculate the total USDT available and determine order size
        total_balance = math.floor(USDT_balance)
        num_orders = 20
        order_size = math.floor(total_balance / num_orders)

        if order_size <= 0:
            raise Exception("Calculated order size is too small to execute.")

        print("Order Parameters:")
        print(f"Symbol: {trading_pair}")
        print(f"Side: BUY")
        print(f"Type: MARKET")
        print(f"Number of Orders: {num_orders}, Each Order Size: {order_size} USDT")

        # Step 8: Execute multiple smaller market buy orders on Bybit Spot
        for i in range(1, num_orders + 1):
            try:
                print(f"Placing order {i}/{num_orders} for {order_size} USDT...")
                order_resp = make_request(
                    "/spot/v1/order",
                    api_key,
                    api_secret,
                    method="POST",
                    params={
                        'symbol': trading_pair,
                        'side': 'Buy',
                        'type': 'MARKET',
                        'quoteOrderQty': str(order_size)
                    }
                )
                if order_resp.get('ret_code') != 0:
                    print(f"Error placing order {i}: {order_resp.get('ret_msg')}")
                    break
                print(f"Order {i} executed successfully. Order ID: {order_resp['result']['orderId']}")
                time.sleep(1)  # Small delay to respect API rate limits

            except Exception as e:
                print(f"General Exception on order {i}: {e}")
                break

    except Exception as e:
        print(f"General Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
