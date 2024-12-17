import requests
import json
import json5
import time
from pathlib import Path
import csv

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

def fetch_bybit_kline_data(category, symbol, interval, csv_file, minutes=10):
    """
    Fetch the last N minutes of Kline data from the Bybit Testnet API and save it to a CSV file.

    Parameters:
    - category (str): Market category (e.g., 'inverse')
    - symbol (str): Trading symbol (e.g., 'BTCUSD')
    - interval (int): Kline interval in minutes (e.g., 1 for 1-minute candles)
    - csv_file (str): File path to save the formatted timestamp, price data
    - minutes (int): Number of minutes to fetch (default: 10)
    """
    base_url = "https://api-testnet.bybit.com/v5/market/kline"

    # Calculate timestamps for the last 'minutes' minutes
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

            # Write to CSV file without headers
            with open(csv_file, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter='|')
                for kline in sorted_data:
                    timestamp = int(kline[0]) // 1000  # Convert to seconds
                    open_price = kline[1] if len(kline) > 1 else 0
                    high_price = kline[2] if len(kline) > 2 else 0
                    low_price = kline[3] if len(kline) > 3 else 0
                    close_price = kline[4] if len(kline) > 4 else 0
                    volume = kline[5] if len(kline) > 5 else 0
                    turnover = kline[6] if len(kline) > 6 else 0
                    trades = kline[9] if len(kline) > 9 else 0  # Use dummy data for missing columns
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
    # Specify your parameters here
    category = "inverse"   # e.g., 'inverse'
    interval = 1           # 1-minute Kline interval
    minutes = 10           # Fetch last 10 minutes of data

    # Call the function
    fetch_bybit_kline_data(category, symbol, interval, csv_filename, minutes)
