import requests
import time
import hmac
import hashlib
import math
import json5
import json
from pathlib import Path
import sys
import math
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import datetime

# -------------- NEW HELPER FUNCTIONS START --------------
BASE_URL = 'https://api.binance.com'
def get_sui_price():
    """
    Fetches the SUI/USDC price from Binance.
    """
    try:
        response = requests.get(f'{BASE_URL}/api/v3/ticker/price', params={'symbol': 'SUIUSDC'})
        response.raise_for_status()
        price_data = response.json()
        return float(price_data.get("price", 0))
    except Exception as e:
        print(f"[ERROR] An error occurred while fetching SUI price: {e}")
        return 0.0

def get_margin_account_info(api_key, secret_key, debug=False):
    """
    Fetch margin account info (similar to your equity script).
    """
    try:
        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'
        signature = hmac.new(
            secret_key.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        query_string += f'&signature={signature}'
        headers = {'X-MBX-APIKEY': api_key}

        response = requests.get(
            f'{BASE_URL}/sapi/v1/margin/account',
            headers=headers,
            params=query_string
        )
        response.raise_for_status()

        account_info = response.json()
        if debug:
            # Print only relevant assets for debugging
            user_assets = account_info.get("userAssets", [])
            filtered = [x for x in user_assets if x["asset"] in ["USDC", "SUI"]]
            print("\n[DEBUG] Filtered Margin Assets (SUI and USDC):")
            print(json.dumps(filtered, indent=4))

        return account_info

    except Exception as e:
        print(f"[ERROR] An error occurred in get_margin_account_info: {e}")
        return None


def calculate_equity(margin_account_info, sui_price):
    """
    Calculates total equity (in USDC) = USDC netAsset + (SUI netAsset * SUI price in USDC).
    """
    try:
        user_assets = margin_account_info.get("userAssets", [])
        usdc_asset = next((a for a in user_assets if a["asset"] == "USDC"), None)
        sui_asset  = next((a for a in user_assets if a["asset"] == "SUI"),  None)

        net_asset_usdc = float(usdc_asset.get("netAsset", 0)) if usdc_asset else 0
        net_asset_sui  = float(sui_asset.get("netAsset",  0)) if sui_asset  else 0

        # total in USDC
        total_equity = net_asset_usdc + (net_asset_sui * sui_price)

        # floor to integer as per your equity script logic
        return math.floor(total_equity)

    except Exception as e:
        print(f"[ERROR] An error occurred while calculating equity: {e}")
        return 0
# -------------- NEW HELPER FUNCTIONS END --------------

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
    print("Executing Margin BUY order script...")
    home_dir = Path.home()
    try:
        # Step 1: Read API keys and config
        with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
            api_keys = json5.load(file)

        api_key = api_keys.get('key')
        api_secret = api_keys.get('secret')
        trading_pair = api_keys.get('pair')
        leverage_strength = float(api_keys.get('margin', 1))  # default 1 if not provided

        # The 'account_shared_x' parameter: how many strategies share this total equity
        account_shared_str = api_keys.get('account_shared_x', "1")
        try:
            account_shared_x = float(account_shared_str)
            if account_shared_x <= 0:
                account_shared_x = 1
        except ValueError:
            account_shared_x = 1

        if not all([api_key, api_secret, trading_pair]):
            raise ValueError("API key, secret, or trading pair not found in the configuration file.")

        # Step 2: Create Binance Client
        client = Client(api_key, api_secret)

        # Step 3: Sync time
        sync_server_time(client)

        # -----------------------------------------------------------
        # (A) Get total equity in USDC terms (like your equity script)
        # -----------------------------------------------------------
        # 1) Fetch margin account info
        margin_info_raw = get_margin_account_info(api_key, api_secret, debug=True)
        if not margin_info_raw:
            raise Exception("Could not fetch margin account info. Exiting.")

        # 2) Fetch SUI price in USDC
        sui_price_in_usdc = get_sui_price()
        if sui_price_in_usdc <= 0:
            print("[WARNING] SUI price could not be fetched or is zero. Equity might be incomplete.")

        # 3) Calculate total equity in USDC
        total_equity_usdc = calculate_equity(margin_info_raw, sui_price_in_usdc)
        if total_equity_usdc <= 0:
            raise Exception("Total equity (USDC + SUI) is zero or negative. Cannot proceed.")

        # Step 4: The portion for this specific strategy
        #    => floor-divide the total equity by 'account_shared_x'
        portion_equity = math.floor(total_equity_usdc / account_shared_x)
        print(f"[INFO] Overall total equity (USDC + SUI): {total_equity_usdc}")
        print(f"[INFO] Shared divisor (account_shared_x): {account_shared_x}")
        print(f"[INFO] Portion equity for {trading_pair}: {portion_equity}")

        if portion_equity <= 0:
            raise Exception(
                "Calculated portion of equity is zero or negative. "
                "Check 'account_shared_x' or your margin account."
            )

        # -------------------------------------------------------
        # (B) Borrow logic: You want to multiply portion_equity by
        #     your leverage_strength to see if you should borrow more
        # -------------------------------------------------------
        target_balance = portion_equity * leverage_strength
        # Borrow only if target is > portion_equity
        borrow_amount = target_balance - portion_equity
        borrow_amount = max(borrow_amount, 0)

        # Step 5: Check the maximum borrowable and borrow if needed
        try:
            max_borrowable_info = client.get_max_margin_loan(asset='USDC')
            max_borrowable = float(max_borrowable_info.get('amount', 0.0))
        except Exception as e:
            print("[ERROR] Could not fetch max borrowable info.")
            raise

        if borrow_amount > max_borrowable:
            print("[WARNING] Borrow amount exceeds maximum borrowable. Falling back to no borrow.")
            print(f"Requested Borrow: {borrow_amount:.2f}, Max Borrowable: {max_borrowable:.2f}")
            borrow_amount = 0

        if borrow_amount > 0:
            # floor the borrow amount
            borrow_amount = math.floor(borrow_amount)
            try:
                client.create_margin_loan(asset='USDC', amount=borrow_amount)
                print(f"[INFO] Successfully borrowed {borrow_amount} USDC.")
            except BinanceAPIException as e:
                print(f"[ERROR] Failed to borrow USDC: {e.message} (Code: {e.code})")
                raise

        # Now total USDC we can spend = portion_equity + borrowed
        total_usdc_for_order = math.floor(portion_equity + borrow_amount)
        num_orders = 2  # example: dividing the buy into multiple orders
        order_size = math.floor(total_usdc_for_order / num_orders)

        if order_size <= 0:
            raise Exception("Calculated order size is too small to execute (<= 0).")

        print("[INFO] Order Parameters:")
        print(f"  - Symbol:         {trading_pair}")
        print(f"  - Side:           BUY")
        print(f"  - Type:           MARKET")
        print(f"  - Number of Orders: {num_orders}")
        print(f"  - Each Order Size:  {order_size} USDC")

        # Step 6: Execute each margin market buy order
        for i in range(1, num_orders + 1):
            try:
                print(f"Placing order {i}/{num_orders} for {order_size} USDC...")
                order = place_order_with_retry(client, trading_pair, order_size)
                print(f"Order {i} executed successfully. Order ID: {order.get('orderId')}")
                # small delay to respect rate limits
                time.sleep(1)
            except BinanceAPIException as e:
                print(f"[ERROR] Binance API Exception on order {i}: {e.message} (Code: {e.code})")
                break
            except BinanceRequestException as e:
                print(f"[ERROR] Binance Request Exception on order {i}: {e}")
                break
            except Exception as e:
                print(f"[ERROR] General Exception on order {i}: {e}")
                break

    except BinanceAPIException as e:
        print(f"[ERROR] Binance API Exception: {e.message} (Code: {e.code})")
    except BinanceRequestException as e:
        print(f"[ERROR] Binance Request Exception: {e}")
    except Exception as e:
        print(f"[ERROR] General Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
