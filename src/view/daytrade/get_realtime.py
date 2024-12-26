import asyncio
import websockets
import json
import time

# Binance WebSocket URL for the 'suiusdc' pair
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/suiusdc@trade"

# File where the timestamp and value will be written
OUTPUT_FILE = "realtime.txt"

# Function to write the timestamp and value to the file
def write_to_file(timestamp, value):
    with open(OUTPUT_FILE, "a") as file:
        file.write(f"{timestamp}: {value}\n")

# Function to handle the WebSocket connection and listen for updates
async def listen_binance():
    async with websockets.connect(BINANCE_WS_URL) as ws:
        while True:
            # Receive the message from the WebSocket
            message = await ws.recv()
            data = json.loads(message)

            # Extract the trade price from the message
            price = data['p']  # 'p' is the price of the trade

            # Get the current timestamp in Unix format
            timestamp = int(time.time())  # Unix timestamp in seconds

            # Write the timestamp and price to the file
            write_to_file(timestamp, price)

            # Print progress in the terminal
            print(f"Timestamp: {timestamp}, Price: {price}")

            # Wait for 1 second before querying again
            await asyncio.sleep(1)

# Main function to start the WebSocket listener
async def main():
    await listen_binance()

# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())
