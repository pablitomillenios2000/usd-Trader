import sys
import json5
import math
from binance.client import Client
from binance.exceptions import BinanceAPIException
from pathlib import Path

print("Executing Margin BUY order script...")
home_dir = Path.home()

try:
    # Step 1: Read API keys from the JSON file
    with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-binance.json", "r") as file:
        api_keys = json5.load(file)
    
    api_key = api_keys['key']
    api_secret = api_keys['secret']
    trading_pair = api_keys['pair']

    leverageStrength = api_keys['margin']

    # Step 2: Initialize the Binance client
    client = Client(api_key, api_secret)

    # Step 3: Fetch the USDC balance from the margin account
    margin_account_info = client.get_margin_account()
    USDC_balance = 0

    for asset in margin_account_info['userAssets']:
        if asset['asset'] == 'USDC':
            USDC_balance = float(asset['free'])
            break

    if USDC_balance <= 0:
        raise Exception("Insufficient USDC balance to execute the order.")

    # Step 4: Calculate the total amount needed to triplicate the balance
    target_balance = USDC_balance * leverageStrength
    borrow_amount = target_balance - USDC_balance

    # Step 5: Check the maximum amount that can be borrowed
    max_borrowable = float(client.get_max_margin_loan(asset='USDC')['amount'])

    # Step 6: Adjust borrow amount if it exceeds the maximum borrowable amount
    if borrow_amount > max_borrowable:
        print("Borrow amount exceeds the maximum borrowable amount.")
        print(f"Borrow amount: {borrow_amount}, Maximum borrowable: {max_borrowable}")
        borrow_amount = 0  # Set borrow amount to 0, and use only the available USDC

    # Step 7: If borrowing is still required and within limits, proceed to borrow
    if borrow_amount > 0:
        borrow_amount = math.floor(borrow_amount)
        client.create_margin_loan(asset='USDC', amount=borrow_amount)
        print(f"Borrowed {borrow_amount} USDC successfully.")

    # Step 8: Round down the total USDC available to buy the trading pair
    target_balance = math.floor(USDC_balance + borrow_amount)

    # Step 9: Output the parameters before placing the order
    print("Order Parameters:")
    print(f"Symbol: {trading_pair}")
    print(f"Side: BUY")
    print(f"Type: MARKET")
    print(f"Quote Order Quantity: {target_balance}")

    print("Debug: Leverage Strength =", leverageStrength)
    print("Debug: USDC Balance =", USDC_balance)
    print("Debug: Target Balance (before borrow) =", USDC_balance * leverageStrength)


    # Step 10: Execute a margin market buy order for the total amount of USDC available
    order = client.create_margin_order(
        symbol=trading_pair,
        side='BUY',
        type='MARKET',
        quoteOrderQty=target_balance
    )
    
    print("Margin BUY order executed successfully. Order details:", order)

except BinanceAPIException as e:
    # Display a detailed error message
    print(f"Binance API Exception: {e.message} (Code: {e.code})")
except Exception as e:
    print("General Exception:", str(e))
    sys.exit(1)
