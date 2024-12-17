#!/usr/bin/env python3

import requests
import json
import json5
import time
from pathlib import Path
import csv
import os

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

def fetch_bybit_kline_data(category, symbol, interval, csv_file, minutes, mode='w'):
    """
    Fetch Kline data from the Bybit API and save it to a CSV file.

    Parameters:
    - category (str): Market category (e.g., 'inverse')
    - symbol (str): Trading symbol (e.g., 'BTCUSD')
    - interval (int): Kline interval in minutes (e.g., 1 for 1-minute candles)
    - csv_file (str): File path to save the data
    - minutes (int): Number of minutes to fetch
    - mode (str): 'w' to write a new file, 'a' to append data
    """
    base_url = "https://api-testnet.bybit.com/v5/market/kline"

    # Calculate timestamps
    end_time = int(time.time() * 1000)  # Current time in milliseconds
    start_time = end_time - (minutes * 60 * 1000)  # Subtract N minutes in milliseconds

    params = {
        "category": category,
        "symbol": symbol,
        "interval": interval,
        "start": start_time,
        "end": end_time,
    }

    try:
        print("Sending request to Bybit API...")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['retCode'] == 0:
            print("Data fetched successfully!")
            # Extract and sort data by timestamp
            kline_data = data['result']['list']
            sorted_data = sorted(kline_data, key=lambda x: int(x[0]))

            # Write to CSV file
            with open(csv_file, mode, newline='') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter='|')
                for kline in sorted_data:
                    timestamp = int(kline[0]) // 1000  # Convert to seconds
                    open_price = kline[1]
                    high_price = kline[2]
                    low_price = kline[3]
                    close_price = kline[4]
                    volume = kline[5]
                    turnover = kline[6]
                    trades = kline[9] if len(kline) > 9 else 0  # Optional field
                    csvwriter.writerow([
                        timestamp, open_price, high_price, low_price,
                        close_price, volume, turnover, 0, 0, trades
                    ])

            print(f"Data saved to {csv_file}")
        else:
            print(f"Error: {data['retMsg']}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Parameters
    category = "inverse"  # e.g., 'inverse'
    interval = 1  # 1-minute Kline interval
    initial_minutes = 3000  # Fetch last 3000 minutes of data

    # Step 1: Fetch the first 3000 minutes
    print("Fetching initial 3000 minutes of data...")
    fetch_bybit_kline_data(category, symbol, interval, csv_filename, initial_minutes, mode='w')

    # Step 2: Enter infinite loop to fetch 1 minute of data every minute
    print("Starting infinite loop to fetch new data every minute...")
    while True:
        fetch_bybit_kline_data(category, symbol, interval, csv_filename, 1, mode='a')
        print("Waiting 60 seconds before the next fetch...")
        time.sleep(60)  # Wait for 60 seconds
