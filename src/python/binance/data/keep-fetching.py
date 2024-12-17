#!/usr/bin/env python3


from pathlib import Path
import websocket
import json5
import requests
import pandas as pd
import time
import threading

# Load the trading pair from apikey-crypto.json
home_dir = Path.home()

with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
    config = json5.load(file)
    if "pair" not in config:
        raise ValueError("The 'pair' key is missing in apikey-crypto.json")
    symbol = config["pair"].lower()  # Convert to lowercase for Binance's WebSocket API

# Define the parameters
interval = "1m"
ws_url = f"wss://stream.binance.com:9443/ws/{symbol}@kline_{interval}"
csv_filename = f"../../../assets/{symbol}-realtime.csv"  # Dynamically generate the output path

# Define the column names
columns = [
    "Timestamp", "Open", "High", "Low", "Close", "Volume",
    "QuoteAssetVolume", "TakerBuyBaseVolume", "TakerBuyQuoteVolume",
    "NumberOfTrades"
]

# Function to fetch historical data from Binance
def fetch_historical_data():
    # Clear the file contents before writing
    open(csv_filename, 'w').close()

    base_url = "https://api.binance.com/api/v3/klines"

    # Set the end time to the current time in milliseconds
    end_time = int(time.time() * 1000)

    # Request the most recent 1,000 data points
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "endTime": end_time,
        "limit": 1000
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    # Check for API errors
    if not isinstance(data, list):
        print(f"Error fetching historical data: {data}")
        return

    # Convert to a DataFrame
    df = pd.DataFrame(data, columns=[
        "Timestamp", "Open", "High", "Low", "Close", "Volume", "CloseTime",
        "QuoteAssetVolume", "NumberOfTrades", "TakerBuyBaseVolume",
        "TakerBuyQuoteVolume", "Ignore"
    ])

    # Keep only relevant columns
    df = df[columns]

    # Convert Timestamp from milliseconds to seconds
    df["Timestamp"] = df["Timestamp"] // 1000
    df["Timestamp"] = df["Timestamp"].astype(int)

    # Convert data types
    float_cols = ["Open", "High", "Low", "Close", "Volume", "QuoteAssetVolume",
                  "TakerBuyBaseVolume", "TakerBuyQuoteVolume"]
    for col in float_cols:
        df[col] = df[col].astype(float)

    df["NumberOfTrades"] = df["NumberOfTrades"].astype(int)

    # Save to CSV with the custom separator and no header
    df.to_csv(csv_filename, sep='|', index=False, header=False)
    print(f"Saved historical data to {csv_filename} with | as the separator, no header")

# Callback function for when a message is received
def on_message(ws, message):
    data = json5.loads(message)
    kline = data['k']
    is_kline_closed = kline['x']
    if is_kline_closed:
        # Extract relevant data and convert data types
        timestamp = int(kline['t'] // 1000)  # Convert to seconds
        open_price = float(kline['o'])
        high_price = float(kline['h'])
        low_price = float(kline['l'])
        close_price = float(kline['c'])
        volume = float(kline['v'])
        quote_asset_volume = float(kline['q'])
        taker_buy_base_volume = float(kline['V'])
        taker_buy_quote_volume = float(kline['Q'])
        number_of_trades = int(kline['n'])

        # Read the existing data from the CSV with column names
        df = pd.read_csv(csv_filename, sep='|', header=None, names=columns, engine='python')

        # Remove the oldest line (first row) if DataFrame has more than 0 rows
        if len(df) > 0:
            df = df.iloc[1:]

        # Create a new DataFrame for the new data line with specified columns
        new_data = pd.DataFrame([[
            timestamp, open_price, high_price, low_price, close_price, volume,
            quote_asset_volume, taker_buy_base_volume, taker_buy_quote_volume,
            number_of_trades
        ]], columns=columns)

        # Append the new data line
        df = pd.concat([df, new_data], ignore_index=True)

        # Save back to the CSV file
        df.to_csv(csv_filename, sep='|', index=False, header=False)

        print(f"Appended data - Timestamp: {timestamp}, O: {open_price}, H: {high_price}, L: {low_price}, C: {close_price}, V: {volume}, QAV: {quote_asset_volume}, TBBAV: {taker_buy_base_volume}, TBQAV: {taker_buy_quote_volume}, NoT: {number_of_trades}")

# Callback function for when the connection is opened
def on_open(ws):
    print("WebSocket connection opened")
    # Start a timer to close the websocket after 10 minutes (600 seconds)
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
    # Create a WebSocket connection
    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_open=on_open, on_close=on_close)
    ws.run_forever()
    # Wait a bit before restarting to prevent tight loop in case of errors
    time.sleep(1)
