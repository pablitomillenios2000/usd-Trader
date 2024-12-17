#!/usr/bin/env python3

import requests
import json
import json5
import time
from pathlib import Path
import csv
import os
import math

# Load the trading pair from apikey-crypto.json
home_dir = Path.home()
config_file = f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json"

try:
    with open(config_file, "r") as file:
        config = json5.load(file)
        if "pair" not in config:
            raise ValueError("The 'pair' key is missing in apikey-crypto.json")
        symbol = config["pair"].upper()  # Bybit expects uppercase
except FileNotFoundError:
    raise FileNotFoundError(f"Configuration file not found at {config_file}")
except ValueError as ve:
    print(ve)
    raise

# CSV file for output
csv_filename = f"../../../assets/{symbol.lower()}-realtime.csv"

# Delete the CSV file if it already exists
if os.path.exists(csv_filename):
    os.remove(csv_filename)
    print(f"Deleted existing file: {csv_filename}")

def fetch_bybit_kline_data(category, symbol, interval, start_ts, end_ts):
    """
    Fetch Kline data from the Bybit API for a given time range.

    Parameters:
    - category (str): Market category (e.g., 'inverse')
    - symbol (str)
    - interval (int): Kline interval in minutes
    - start_ts (int): start timestamp in ms
    - end_ts (int): end timestamp in ms

    Returns:
    - list: A list of kline data entries or None if error
    """
    base_url = "https://api-testnet.bybit.com/v5/market/kline"
    params = {
        "category": category,
        "symbol": symbol,
        "interval": interval,
        "start": start_ts,
        "end": end_ts,
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['retCode'] == 0:
            kline_data = data['result']['list']
            # Sort data by timestamp
            sorted_data = sorted(kline_data, key=lambda x: int(x[0]))
            return sorted_data
        else:
            print(f"Error fetching data: {data['retMsg']}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def write_kline_data_to_csv(kline_data, csv_file, mode='a'):
    """
    Write kline data to CSV file.
    
    Parameters:
    - kline_data (list): list of kline entries
    - csv_file (str)
    - mode (str): write mode ('w' or 'a')
    """
    if not kline_data:
        return

    with open(csv_file, mode, newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter='|')
        for kline in kline_data:
            timestamp = int(kline[0]) // 1000  # Convert to seconds
            open_price = kline[1]
            high_price = kline[2]
            low_price = kline[3]
            close_price = kline[4]
            volume = kline[5]
            turnover = kline[6]
            # Check if trades count is available at index 9
            trades = kline[9] if len(kline) > 9 else 0
            csvwriter.writerow([
                timestamp, open_price, high_price, low_price,
                close_price, volume, turnover, 0, 0, trades
            ])

if __name__ == "__main__":
    category = "inverse"
    interval = 1
    initial_minutes = 3000
    chunk_minutes = 200  # Bybit returns at most 200 candles per request

    end_time = int(time.time() * 1000)
    start_time = end_time - (initial_minutes * 60 * 1000)

    # Number of chunks needed
    total_chunks = math.ceil(initial_minutes / chunk_minutes)

    # Fetch data in chunks of 200 candles each
    # We'll go from oldest to newest chunk
    print("Fetching initial 3000 minutes of data in chunks...")
    current_start = start_time

    # Start by writing with mode='w' for the first chunk, then 'a' afterwards
    write_mode = 'w'

    for i in range(total_chunks):
        chunk_start = current_start
        chunk_end = chunk_start + (chunk_minutes * 60 * 1000)

        # The last chunk might overshoot end_time, so clamp it
        if chunk_end > end_time:
            chunk_end = end_time

        print(f"Fetching chunk {i+1}/{total_chunks}, "
              f"from {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(chunk_start/1000))} "
              f"to {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(chunk_end/1000))}")

        chunk_data = fetch_bybit_kline_data(category, symbol, interval, chunk_start, chunk_end)

        # Write this chunk of data to CSV
        write_kline_data_to_csv(chunk_data, csv_filename, mode=write_mode)

        # After the first write, switch mode to 'a'
        write_mode = 'a'

        # Move start forward for next chunk
        current_start = chunk_end + 1

        # If we've reached or passed end_time, break early
        if current_start > end_time:
            break

    print("Initial data fetch complete.")

    # Step 2: Enter infinite loop to fetch 1 minute of data every minute
    print("Starting infinite loop to fetch new data every minute...")
    while True:
        # Fetch last 1 minute of data
        now = int(time.time() * 1000)
        one_min_ago = now - (1 * 60 * 1000)

        new_data = fetch_bybit_kline_data(category, symbol, interval, one_min_ago, now)
        write_kline_data_to_csv(new_data, csv_filename, mode='a')

        print("Waiting 60 seconds before the next fetch...")
        time.sleep(60)
