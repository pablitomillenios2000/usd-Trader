import sys
import json5
import math
from binance.client import Client
from binance.exceptions import BinanceAPIException

print("Executing Margin SELL order script...")

try:
    # Step 1: Read API keys from the JSON file
    with open("../../../dist/apikey-binance.json", "r") as file:
        api_keys = json5.load(file)
    
    api_key = api_keys['key']
    api_secret = api_keys['secret']
    trading_pair = api_keys['pair']

    # Step 2: Initialize the Binance client
    client = Client(api_key, api_secret)

    # Step 3: Extract the base asset from the trading pair
    # For example, if trading_pair is "SUIUSDC", base is "SUI"
    # Usually on Binance, pairs are formatted as BASEQUOTE (e.g., BTCUSDT -> BTC as base, USDT as quote)
    # This script assumes the first 3 characters is the base asset. 
    # Adjust if needed. For pairs with variable lengths (like BTCUSDT), 
    # you may need a different logic:
    #   base asset = trading_pair.replace("USDT","").replace("BUSD","").replace("USDC","") etc.
    asset_to_sell = trading_pair[:3]

    # Step 4: Fetch the balance from the margin account
    margin_account_info = client.get_margin_account()
    asset_balance = 0.0
    for asset in margin_account_info['userAssets']:
        if asset['asset'] == asset_to_sell:
            asset_balance = float(asset['free'])
            break

    if asset_balance <= 0:
        raise Exception(f"No {asset_to_sell} balance available to liquidate.")

    # Step 5: Round down the balance using the floor function
    asset_balance = math.floor(asset_balance)

    if asset_balance <= 0:
        raise Exception(f"Rounded {asset_to_sell} balance is zero, no asset to sell.")

    # Debug prints
    print(f"Ready to SELL {asset_balance} {asset_to_sell}")

    # Step 6: Execute a margin market sell order for all available balance
    order = client.create_margin_order(
        symbol=trading_pair,
        side='SELL',
        type='MARKET',
        quantity=asset_balance
    )
    print("Margin SELL order executed successfully. Order details:", order)

    # Optional: Wait or re-check if order is filled
    # For a market order, it's typically filled immediately, but you can add checks if needed.
    # ... (Optional code here)

    # Step 7: Refresh margin account info after the sell
    margin_account_info = client.get_margin_account()

    # Step 8: Repay all outstanding loans
    repaid_anything = False
    for asset in margin_account_info['userAssets']:
        borrowed_amount = float(asset['borrowed'])
        if borrowed_amount > 0:
            # Repay the borrowed amount
            client.repay_margin_loan(asset=asset['asset'], amount=borrowed_amount)
            print(f"Repaid {borrowed_amount} of {asset['asset']} successfully.")
            repaid_anything = True

    if not repaid_anything:
        print("No debt to repay.")

except BinanceAPIException as e:
    if e.code == -1100:
        print("ApiError -1100, character error. [Possibly invalid symbol or insufficient balance]")
    else:
        print(f"Error executing Margin SELL order script: {e}")
except Exception as e:
    print("Error executing Margin SELL order script:", str(e))
    sys.exit(1)
