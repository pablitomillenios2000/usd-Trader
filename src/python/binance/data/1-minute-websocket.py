import websocket
import json5
from pathlib import Path

# Load the trading pair from apikey-binance.json
home_dir = Path.home()
with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-binance.json", "r") as file:
    config = json5.load(file)
    if "pair" not in config:
        raise ValueError("The 'pair' key is missing in apikey-binance.json")
    symbol = config["pair"].lower()  # Convert to lowercase for Binance's WebSocket API

# Define the WebSocket URL for Binance's real-time kline data
interval = "1m"
ws_url = f"wss://stream.binance.com:9443/ws/{symbol}@kline_{interval}"

# Callback function for when a message is received
def on_message(ws, message):
    data = json5.loads(message)
    kline = data['k']
    is_kline_closed = kline['x']
    if is_kline_closed:
        timestamp = kline['t']
        open_price = kline['o']
        high_price = kline['h']
        low_price = kline['l']
        close_price = kline['c']
        volume = kline['v']
        print(f"Timestamp: {timestamp}, O: {open_price}, H: {high_price}, L: {low_price}, C: {close_price}, V: {volume}")

# Callback function for when the connection is opened
def on_open(ws):
    print("WebSocket connection opened")

# Callback function for when the connection is closed
def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

# Create a WebSocket connection
ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_open=on_open, on_close=on_close)
ws.run_forever()
