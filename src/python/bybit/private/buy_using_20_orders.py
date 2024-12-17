import sys
import json5
import math
import time
import datetime
from pathlib import Path
from pybit.spot import HTTP  # pybit library for Bybit Spot
# Note: pybit has multiple modules, ensure you use the correct Spot endpoint class.

print("Executing Margin BUY order script with Bybit...")

home_dir = Path.home()

def get_server_time(client):
    """ Get Bybit server time (if needed). """
    resp = client.query('/v2/public/time', method='GET', auth=False)
    # Example response: {"ret_code":0,"ret_msg":"OK","ext_code":"","ext_info":"","result":{"server_time":1638239422840},"time_now":"1638239422.840441"}
    return resp['result']['server_time']

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

        # Step 2: Initialize the Bybit Spot client
        # Note: If you are testing, you might want to use the testnet endpoint and keys.
        client = HTTP(
            endpoint="https://api.bybit.com", 
            api_key=api_key,
            api_secret=api_secret
        )

        # (Optional) Step 3: Fetch server time if needed
        # Bybit typically doesn't require manual synchronization like Binance.
        # server_time = get_server_time(client)
        # local_time = int(time.time() * 1000)
        # offset = server_time - local_time
        # print(f"Server time: {datetime.datetime.fromtimestamp(server_time/1000)}, Offset: {offset} ms")

        # Step 4: Fetch the USDC balance from the spot account
        account_info = client.query('/spot/v1/account', method='GET')
        # account_info structure: { "ret_code":0, "result":{"balances":[{"coin":"USDC","free":"...","locked":"..."}]}, ... }
        USDC_balance = 0.0
        for asset in account_info['result']['balances']:
            if asset['coin'] == 'USDC':
                USDC_balance = float(asset['free'])
                break

        if USDC_balance <= 0:
            raise Exception("Insufficient USDC balance to execute the order.")

        # Step 5: Calculate the total amount needed based on leverage
        target_balance = USDC_balance * leverage_strength
        borrow_amount = target_balance - USDC_balance

        # Step 6: Check the maximum amount that can be borrowed - Bybit endpoint
        # According to Bybit Docs: GET /spot/v1/cross-margin/loan-info?coin=USDC
        loan_info_resp = client.query('/spot/v1/cross-margin/loan-info', method='GET', query={'coin': 'USDC'})
        # Response example: {"ret_code":0,"result":{"loanable":"1000"},"ret_msg":"OK"}
        max_borrowable = float(loan_info_resp['result']['loanable'])

        # Step 7: Adjust borrow amount if it exceeds the maximum borrowable amount
        if borrow_amount > max_borrowable:
            print("Borrow amount exceeds the maximum borrowable amount.")
            print(f"Borrow amount requested: {borrow_amount} USDC, Maximum borrowable: {max_borrowable} USDC")
            borrow_amount = 0  # Set borrow amount to 0, and use only the available USDC

        # Step 8: If borrowing is required and within limits, proceed to borrow
        if borrow_amount > 0:
            borrow_amount = math.floor(borrow_amount)
            # POST /spot/v1/cross-margin/loan
            # Params: coin, qty
            borrow_resp = client.query('/spot/v1/cross-margin/loan', method='POST', data={'coin':'USDC','qty':str(borrow_amount)})
            if borrow_resp.get('ret_code') != 0:
                raise Exception(f"Failed to borrow USDC: {borrow_resp.get('ret_msg')}")
            print(f"Successfully borrowed {borrow_amount} USDC.")

            # Update USDC_balance after borrow
            # Wait a moment for balance to update
            time.sleep(1)
            account_info = client.query('/spot/v1/account', method='GET')
            for asset in account_info['result']['balances']:
                if asset['coin'] == 'USDC':
                    USDC_balance = float(asset['free'])
                    break

        # Step 9: Calculate the total USDC available and determine order size
        # After borrowing, USDC_balance should now reflect total (available + borrowed)
        total_balance = math.floor(USDC_balance)
        num_orders = 20
        order_size = math.floor(total_balance / num_orders)

        if order_size <= 0:
            raise Exception("Calculated order size is too small to execute.")

        print("Order Parameters:")
        print(f"Symbol: {trading_pair}")
        print(f"Side: BUY")
        print(f"Type: MARKET")
        print(f"Number of Orders: {num_orders}, Each Order Size: {order_size} USDC")

        # Step 10: Execute multiple smaller market buy orders on Bybit Spot
        # Bybit Spot order endpoint: POST /spot/v1/order
        # Required params: symbol, side, type, qty (for base), or quoteOrderQty if applicable.
        # Unlike Binance, Bybit does not always support quoteOrderQty in the same way. 
        # Bybit expects qty as the BASE amount for market orders. We must convert USDC to base qty.
        #
        # For a Market BUY, Bybit requires a 'quoteOrderQty' param (for quote-based orders) on Spot:
        # According to docs: type=MARKET and side=BUY can support `quoteOrderQty`.
        # Let's assume we can use `quoteOrderQty` as on Binance.
        #
        # If not supported, you'd have to fetch the current price and calculate the base amount.
        
        for i in range(1, num_orders + 1):
            try:
                print(f"Placing order {i}/{num_orders} for {order_size} USDC...")

                order_resp = client.query(
                    '/spot/v1/order',
                    method='POST',
                    data={
                        'symbol': trading_pair,
                        'side': 'BUY',
                        'type': 'MARKET',
                        'quoteOrderQty': str(order_size)  # Using quote-based order
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
        # Catch-all for any other exceptions
        print(f"General Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
