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
    symbol = config["pair"].upper()  # Bybit expects uppercase

# Define the parameters
interval = "1m"
ws_url = "wss://stream.bybit.com/spot/quote/ws/v2"
csv_filename = f"../../../assets/{symbol.lower()}-realtime.csv"  # Keep same filename pattern

# Define the column names
columns = [
    "Timestamp", "Open", "High", "Low", "Close", "Volume",
    "QuoteAssetVolume", "TakerBuyBaseVolume", "TakerBuyQuoteVolume",
    "NumberOfTrades"
]

def fetch_historical_data():
    # Clear the file contents before writing
    open(csv_filename, 'w').close()

    base_url = "https://api.bybit.com/spot/quote/v1/kline"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000
    }
    response = requests.get(base_url, params=params)

    # Debugging prints:
    print("HTTP GET:", response.url)
    print("Response status code:", response.status_code)
    print("Response text:", response.text[:500])  # Print first 500 chars for brevity

    # Try parsing
    try:
        data = json5.loads(response.text)
    except ValueError as e:
        print("Error parsing JSON5:", e)
        return

    if data.get("ret_code", None) != 0:
        print(f"Error fetching historical data: {data}")
        return

    klines = data.get("result", [])
    if not isinstance(klines, list):
        print("Unexpected data format for klines:", klines)
        return

    # Convert to DataFrame
    df = pd.DataFrame(klines, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])

    # Add missing columns with zeros
    df["QuoteAssetVolume"] = 0.0
    df["TakerBuyBaseVolume"] = 0.0
    df["TakerBuyQuoteVolume"] = 0.0
    df["NumberOfTrades"] = 0

    # Convert data types
    float_cols = ["Open", "High", "Low", "Close", "Volume", 
                  "QuoteAssetVolume", "TakerBuyBaseVolume", "TakerBuyQuoteVolume"]
    for col in float_cols:
        df[col] = df[col].astype(float)
    df["NumberOfTrades"] = df["NumberOfTrades"].astype(int)
    df["Timestamp"] = df["Timestamp"].astype(int)

    # Save to CSV
    df.to_csv(csv_filename, sep='|', index=False, header=False)
    print(f"Saved historical data to {csv_filename} with | as the separator, no header")


last_candle_time = None

def on_message(ws, message):
    global last_candle_time
    msg = json5.loads(message)

    topic = msg.get("topic", "")
    if topic != "kline":
        return

    data = msg.get("data", {})
    kline_data = data.get("kline", [])

    for candle in kline_data:
        # candle: [open_time, open, high, low, close, volume]
        timestamp = int(candle[0])  # already in seconds
        open_price = float(candle[1])
        high_price = float(candle[2])
        low_price = float(candle[3])
        close_price = float(candle[4])
        volume = float(candle[5])

        # Check if this is a new candle by comparing timestamp
        if last_candle_time is None or timestamp > last_candle_time:
            # Read the existing data
            if Path(csv_filename).exists():
                df = pd.read_csv(csv_filename, sep='|', header=None, names=columns, engine='python')
            else:
                df = pd.DataFrame(columns=columns)

            # Remove oldest line if present
            if len(df) > 0:
                df = df.iloc[1:]

            # Create new data row
            new_data = pd.DataFrame([[
                timestamp, open_price, high_price, low_price, close_price, volume,
                0.0, 0.0, 0.0, 0
            ]], columns=columns)

            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(csv_filename, sep='|', index=False, header=False)

            print(f"Appended data - Timestamp: {timestamp}, O: {open_price}, H: {high_price}, L: {low_price}, C: {close_price}, V: {volume}")
            last_candle_time = timestamp
        else:
            # If it's the same candle (delta update), we update the last entry
            df = pd.read_csv(csv_filename, sep='|', header=None, names=columns, engine='python')
            if len(df) > 0:
                df.iloc[-1] = [
                    timestamp, open_price, high_price, low_price, close_price, volume,
                    0.0, 0.0, 0.0, 0
                ]
                df.to_csv(csv_filename, sep='|', index=False, header=False)
                print(f"Updated current candle - Timestamp: {timestamp}, O: {open_price}, H: {high_price}, L: {low_price}, C: {close_price}, V: {volume}")

def on_open(ws):
    print("WebSocket connection opened")
    # Subscribe to kline topic
    sub_msg = {
        "topic": "kline",
        "event": "sub",
        "params": {
            "symbol": symbol,
            "interval": interval
        }
    }
    ws.send(json5.dumps(sub_msg))

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

# Fetch historical data first
fetch_historical_data()

while True:
    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_open=on_open, on_close=on_close)
    ws.run_forever()
    time.sleep(1)
