#!/usr/bin/env python3

from pathlib import Path
import websocket
import json5
import requests
import pandas as pd
import time
import threading

# Load the trading pair from apikey-bybit.json
home_dir = Path.home()

with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
    config = json5.load(file)
    if "pair" not in config:
        raise ValueError("The 'pair' key is missing in apikey-bybit.json")
    symbol = config["pair"].upper()  # Bybit requires uppercase pairs

# Define the parameters
interval = "1"
ws_url = "wss://stream.bybit.com/v5/public/spot"  # Bybit WebSocket endpoint
csv_filename = f"../../../assets/{symbol}-realtime.csv"  # Output path

# Define the column names
columns = [
    "Timestamp", "Open", "High", "Low", "Close", "Volume",
    "QuoteAssetVolume", "TakerBuyBaseVolume", "TakerBuyQuoteVolume",
    "NumberOfTrades"
]

# Function to fetch historical data from Bybit
def fetch_historical_data():
    # Clear the file contents before writing
    open(csv_filename, 'w').close()

    base_url = "https://api.bybit.com/v5/market/kline"

    # Set the current time in milliseconds
    end_time = int(time.time())

    params = {
        "category": "spot",
        "symbol": symbol,
        "interval": interval,
        "end": end_time,
        "limit": 1000
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    # Check for API errors
    if "result" not in data or "list" not in data["result"]:
        print(f"Error fetching historical data: {data}")
        return

    # Extract kline data
    klines = data["result"]["list"]

    # Convert to a DataFrame
    df = pd.DataFrame(klines, columns=[
        "Timestamp", "Open", "High", "Low", "Close", "Volume", "QuoteAssetVolume"
    ])

    # Convert Timestamp from milliseconds to seconds
    df["Timestamp"] = df["Timestamp"].astype(int) // 1000
    df["Timestamp"] = df["Timestamp"].astype(int)

    # Add placeholder columns for missing data
    df["TakerBuyBaseVolume"] = 0.0
    df["TakerBuyQuoteVolume"] = 0.0
    df["NumberOfTrades"] = 0

    # Save to CSV with the custom separator and no header
    df = df[columns]
    df.to_csv(csv_filename, sep='|', index=False, header=False)
    print(f"Saved historical data to {csv_filename} with | as the separator, no header")

# Callback function for when a message is received
def on_message(ws, message):
    data = json.loads(message)
    if "data" in data:
        kline = data["data"]
        timestamp = int(kline['t']) // 1000  # Convert to seconds
        open_price = float(kline['o'])
        high_price = float(kline['h'])
        low_price = float(kline['l'])
        close_price = float(kline['c'])
        volume = float(kline['v'])
        quote_asset_volume = float(kline['q'])
        
        # Placeholder for unused columns
        taker_buy_base_volume = 0.0
        taker_buy_quote_volume = 0.0
        number_of_trades = 0

        # Read the existing data from the CSV with column names
        df = pd.read_csv(csv_filename, sep='|', header=None, names=columns, engine='python')

        # Remove the oldest line if DataFrame has data
        if len(df) > 0:
            df = df.iloc[1:]

        # Append the new data
        new_data = pd.DataFrame([[
            timestamp, open_price, high_price, low_price, close_price, volume,
            quote_asset_volume, taker_buy_base_volume, taker_buy_quote_volume,
            number_of_trades
        ]], columns=columns)

        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(csv_filename, sep='|', index=False, header=False)

        print(f"Appended data - Timestamp: {timestamp}, O: {open_price}, C: {close_price}")

# Callback function for when the connection is opened
def on_open(ws):
    print("WebSocket connection opened")
    subscribe_message = {
        "op": "subscribe",
        "args": [f"kline.{interval}.{symbol}"]
    }
    ws.send(json.dumps(subscribe_message))
    print("Subscribed to kline data")

    # Start a timer to close the websocket after 10 minutes
    def close_ws():
        print("Closing WebSocket connection after 10 minutes")
        ws.close()
    threading.Timer(600, close_ws).start()

# Callback function for when the connection is closed
def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

# Fetch historical data first
fetch_historical_data()

while True:
    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_open=on_open, on_close=on_close)
    ws.run_forever()
    time.sleep(1)
