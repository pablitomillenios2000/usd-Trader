import requests
import json

def fetch_bybit_kline_data(category, symbol, interval, output_file):
    """
    Fetch Kline data from the Bybit Testnet API and save it to a file.

    Parameters:
    - category (str): Market category (e.g., 'inverse')
    - symbol (str): Trading symbol (e.g., 'BTCUSD')
    - interval (int): Kline interval in minutes (e.g., 60 for hourly)
    - start (int): Start time in milliseconds
    - end (int): End time in milliseconds
    - output_file (str): File path to save the response JSON
    """
    base_url = "https://api-testnet.bybit.com/v5/market/kline"
    params = {
        "category": category,
        "symbol": symbol,
        "interval": interval,
    }

    try:
        print("Sending request to Bybit API...")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['retCode'] == 0:
            print("Data fetched successfully!")
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Data saved to {output_file}")
        else:
            print(f"Error: {data['retMsg']}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Specify your parameters here
    category = "inverse"   # e.g., 'inverse'
    symbol = "BTCUSD"      # Trading pair, e.g., 'BTCUSD'
    interval = 1          # Kline interval in minutes (e.g., 60 for hourly)
    #start = 1670601600000  # Start time in milliseconds
    #end = 1670608800000    # End time in milliseconds
    output_file = "bybit_kline_data.json"  # File to save the response

    # Call the function
    fetch_bybit_kline_data(category, symbol, interval, output_file)
