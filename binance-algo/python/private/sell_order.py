import sys
import json
import math
from binance.client import Client
from binance.exceptions import BinanceAPIException

print("Executing Margin SELL order script...")

try:
    # Step 1: Read API keys from the JSON file
    with open("../../dist/apikey-binance.json", "r") as file:
        api_keys = json.load(file)
    
    api_key = api_keys['key']
    api_secret = api_keys['secret']
    trading_pair = api_keys['pair']

    # Step 2: Initialize the Binance client
    client = Client(api_key, api_secret)

    # Step 3: Extract the asset from the trading pair
    asset_to_sell = trading_pair[:3]

    # Step 4: Fetch the balance from the margin account
    margin_account_info = client.get_margin_account()
    asset_balance = 0

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

    # Step 6: Execute a margin market sell order for all available balance
    order = client.create_margin_order(
        symbol=trading_pair,
        side='SELL',
        type='MARKET',
        quantity=asset_balance
    )
    print("Margin SELL order executed successfully. Order details:", order)

    # Step 7: Repay all outstanding loans
    for asset in margin_account_info['userAssets']:
        borrowed_amount = float(asset['borrowed'])
        if borrowed_amount > 0:
            client.repay_margin_loan(asset=asset['asset'], amount=borrowed_amount)
            print(f"Repaid {borrowed_amount} of {asset['asset']} successfully.")

except BinanceAPIException as e:
    if e.code == -1100:
        print("ApiError -1100, character error. [Possibly invalid symbol or insufficient balance]")
    else:
        print(f"Error executing Margin SELL order script: {e}")
except Exception as e:
    print("Error executing Margin SELL order script:", str(e))
    sys.exit(1)
