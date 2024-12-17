import os
import json5
from collections import deque
from tqdm import tqdm

# Define file paths 
api_key_file = "apikey-crypto.json"
asset_file = "../view/output/asset.txt"
trades_file = "../view/output/trades.txt"

# Load configuration
with open(api_key_file, 'r') as f:
    config = json5.load(f)

investment = config["investment"]
trailing_stop_loss_percentage = config["sl_percentage"]  # Defined in the problem

print("Computing trailing stop loss trades and local minima")

def read_asset_file():
    """Reads the asset file and returns the data as a list of tuples (timestamp, price)."""
    with open(asset_file, 'r') as f:
        return [tuple(map(float, line.strip().split(','))) for line in f]

def initialize_trades_file():
    """Clears the contents of the trades file by opening it in write mode."""
    with open(trades_file, 'w') as f:
        f.write("")  # Clear the file contents

def write_trade(timestamp, action, reason):
    """Writes a trade action to the trades file."""
    with open(trades_file, 'a') as f:
        f.write(f"{int(timestamp)},{action},{reason}\n")

def find_local_minimum(prices):
    """
    Finds a local minimum in the deque of prices.
    Expects prices as a deque of length 3: [(t0, p0), (t1, p1), (t2, p2)]
    Returns the middle element (t1, p1) if it's a local minimum, else None.
    """
    if len(prices) < 3:
        return None
    # Middle price is a local minimum if it's less than the one before and after
    if prices[1][1] < prices[0][1] and prices[1][1] < prices[2][1]:
        return prices[1]
    return None

def process_trades():
    """Processes the trades based on trailing stop loss and local minima."""
    asset_data = read_asset_file()
    trailing_stop_price = None
    # Initialize to 'sell' state to allow first buy on local minimum
    last_action = 'sell'  
    recent_prices = deque(maxlen=3)

    with tqdm(total=len(asset_data), desc="Processing Trades", unit="entry") as pbar:
        for timestamp, price in asset_data:
            recent_prices.append((timestamp, price))

            # Check if we can detect a local minimum (only if we're currently 'sold out')
            if last_action == 'sell' and len(recent_prices) == 3:
                local_minimum = find_local_minimum(recent_prices)
                if local_minimum is not None:
                    # Found a local minimum, execute a buy
                    write_trade(local_minimum[0], 'buy', 'locmin')
                    last_action = 'buy'
                    # Set the initial trailing stop price based on the price at buy time
                    trailing_stop_price = price * (1 - trailing_stop_loss_percentage / 100)

            # If currently in a buy state, manage trailing stop
            if last_action == 'buy':
                # Update the trailing stop price if the current price justifies a higher stop
                new_stop = price * (1 - trailing_stop_loss_percentage / 100)
                if trailing_stop_price is None:
                    trailing_stop_price = new_stop
                else:
                    trailing_stop_price = max(trailing_stop_price, new_stop)

                # Check if price hits the trailing stop
                if price <= trailing_stop_price:
                    write_trade(timestamp, 'sell', 'tsl')
                    last_action = 'sell'
                    trailing_stop_price = None

            pbar.update(1)  # Update progress bar on each iteration

if __name__ == "__main__":
    if not os.path.exists(asset_file):
        raise FileNotFoundError(f"Asset file not found: {asset_file}")
    initialize_trades_file()  # Clear trades file before processing
    process_trades()
