from pathlib import Path
import sys
import json5
import math
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import time
import datetime

print("Executing Margin BUY order script...")
home_dir = Path.home()

def sync_server_time(client):
    """
    Synchronizes local system time with Binance server time.
    This updates the client's internal timestamp offset.
    """
    try:
        server_time_response = client.get_server_time()
        server_time = server_time_response['serverTime']  # in milliseconds
        local_time = int(time.time() * 1000)  # in milliseconds
        time_offset = server_time - local_time
        client.time_offset = time_offset  # Update the client's internal time offset

        # For debugging: Print the server time, local time, and offset
        server_time_dt = datetime.datetime.fromtimestamp(server_time / 1000.0)
        local_time_dt = datetime.datetime.fromtimestamp(local_time / 1000.0)
        offset_seconds = time_offset / 1000.0

        print(f"[Time Sync] Server Time: {server_time_dt} | Local Time: {local_time_dt} | Offset: {offset_seconds} seconds")

    except Exception as e:
        print(f"Failed to synchronize time: {e}")
        raise

def place_order_with_retry(client, trading_pair, order_size, max_retries=3):
    """
    Place an order with retry logic for timestamp errors.
    """
    for attempt in range(1, max_retries + 1):
        try:
            order = client.create_margin_order(
                symbol=trading_pair,
                side='BUY',
                type='MARKET',
                quoteOrderQty=order_size
            )
            return order
        except BinanceAPIException as e:
            if e.code == -1021:  # Timestamp error
                print(f"Attempt {attempt}: Timestamp error detected. Resynchronizing time...")
                sync_server_time(client)
                # Adding a longer sleep to ensure time sync takes effect
                time.sleep(2)
            else:
                print(f"Binance API Exception on attempt {attempt}: {e.message} (Code: {e.code})")
                raise
        except BinanceRequestException as e:
            print(f"Binance Request Exception on attempt {attempt}: {e}")
            raise
        except Exception as e:
            print(f"General Exception on attempt {attempt}: {e}")
            raise
    raise Exception("Failed to place order after multiple retries due to timestamp issues.")

def main():
    try:
        # Step 1: Read API keys and configuration from the JSON file
        with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
            api_keys = json5.load(file)

        api_key = api_keys.get('key')
        api_secret = api_keys.get('secret')
        trading_pair = api_keys.get('pair')
        leverage_strength = api_keys.get('margin', 1)  # Default leverage to 1 if not specified

        # Read the 'account_shared_x' parameter from the JSON
        account_shared_str = api_keys.get('account_shared_x', "1")
        try:
            account_shared_x = float(account_shared_str)
            if account_shared_x <= 0:
                account_shared_x = 1  # fallback to 1 if invalid
        except ValueError:
            account_shared_x = 1  # fallback if the JSON is invalid

        if not all([api_key, api_secret, trading_pair]):
            raise ValueError("API key, secret, or trading pair not found in the configuration file.")

        # Step 2: Initialize the Binance client
        client = Client(api_key, api_secret)

        # Step 3: Synchronize time with Binance server
        sync_server_time(client)

        # Step 4: Fetch margin account info and parse *NET* equity for USDC
        margin_account_info = client.get_margin_account()
        
        USDC_net_equity = 0.0
        for asset in margin_account_info.get('userAssets', []):
            if asset.get('asset') == 'USDC':
                # netAsset = free + locked - borrowed - interest
                USDC_net_equity = float(asset.get('netAsset', 0.0))
                break

        if USDC_net_equity <= 0:
            raise Exception(
                "Insufficient USDC net equity to execute the order. "
                "Check your margin positions, borrowed amounts, etc."
            )

        # -------------------------------------------------------------------
        # Divide the NET USDC equity by 'account_shared_x'
        # to only invest the portion for this particular coin.
        # -------------------------------------------------------------------
        portion_equity = USDC_net_equity / account_shared_x
        print(f"[INFO] Total USDC net equity: {USDC_net_equity:.2f}")
        print(f"[INFO] Shared divisor: {account_shared_x}")
        print(f"[INFO] Portion equity for {trading_pair}: {portion_equity:.2f}")

        if portion_equity <= 0:
            raise Exception(
                "Calculated portion of net USDC equity is zero or negative. "
                "Check 'account_shared_x' or your margin account."
            )

        # Step 5: Calculate how much we want after leverage
        # Example: portion_equity=1000, leverage_strength=4 => target_balance=4000
        target_balance = portion_equity * leverage_strength

        # Borrow only enough to reach the target from portion_equity
        borrow_amount = target_balance - portion_equity  # if target_balance > portion_equity, else 0

        # Step 6: Check the maximum amount that can be borrowed
        max_borrowable_info = client.get_max_margin_loan(asset='USDC')
        max_borrowable = float(max_borrowable_info.get('amount', 0.0))

        # Step 7: Adjust borrow amount if it exceeds the maximum borrowable amount
        if borrow_amount > max_borrowable:
            print("Borrow amount exceeds the maximum borrowable amount.")
            print(f"Borrow amount requested: {borrow_amount:.2f} USDC, Maximum borrowable: {max_borrowable:.2f} USDC")
            borrow_amount = 0  # fallback: do not borrow, just use portion_equity

        # Step 8: If borrowing is required and within limits, proceed to borrow
        if borrow_amount > 0:
            borrow_amount = math.floor(borrow_amount)
            try:
                client.create_margin_loan(asset='USDC', amount=borrow_amount)
                print(f"Successfully borrowed {borrow_amount} USDC.")
            except BinanceAPIException as e:
                print(f"Failed to borrow USDC: {e.message} (Code: {e.code})")
                raise
            except Exception as e:
                print(f"General Exception during borrowing: {e}")
                raise

        # Step 9: Now we have "portion_equity + borrowed" USDC to trade
        total_usdc_for_order = math.floor(portion_equity + borrow_amount)
        num_orders = 2
        order_size = math.floor(total_usdc_for_order / num_orders)

        if order_size <= 0:
            raise Exception("Calculated order size is too small to execute.")

        print("Order Parameters:")
        print(f"Symbol: {trading_pair}")
        print(f"Side: BUY")
        print(f"Type: MARKET")
        print(f"Number of Orders: {num_orders}, Each Order Size: {order_size} USDC")

        # Step 10: Execute multiple smaller margin market buy orders sequentially
        for i in range(1, num_orders + 1):
            try:
                print(f"Placing order {i}/{num_orders} for {order_size} USDC...")
                order = place_order_with_retry(client, trading_pair, order_size)
                print(f"Order {i} executed successfully. Order ID: {order.get('orderId')}")
                # Optional: Print additional order details for debugging
                # print(json.dumps(order, indent=2))
                time.sleep(1)  # Small delay to respect API rate limits
            except BinanceAPIException as e:
                print(f"Binance API Exception on order {i}: {e.message} (Code: {e.code})")
                break
            except BinanceRequestException as e:
                print(f"Binance Request Exception on order {i}: {e}")
                break
            except Exception as e:
                print(f"General Exception on order {i}: {e}")
                break

    except BinanceAPIException as e:
        print(f"Binance API Exception: {e.message} (Code: {e.code})")
    except BinanceRequestException as e:
        print(f"Binance Request Exception: {e}")
    except Exception as e:
        print(f"General Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
