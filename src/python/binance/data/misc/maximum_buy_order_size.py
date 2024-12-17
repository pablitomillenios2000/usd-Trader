import requests

# Binance API Base URL
BASE_URL = "https://api.binance.com"

def get_max_order_size(pair):
    """
    Fetch the maximum order size for a given trading pair from Binance.
    """
    endpoint = "/api/v3/exchangeInfo"
    url = BASE_URL + endpoint

    try:
        # Fetch exchange information
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Find the specific trading pair
        for symbol in data['symbols']:
            if symbol['symbol'] == pair:
                # Extract the filters for the trading pair
                for filter in symbol['filters']:
                    if filter['filterType'] == "LOT_SIZE":
                        min_qty = float(filter['minQty'])
                        max_qty = float(filter['maxQty'])
                        step_size = float(filter['stepSize'])
                        return min_qty, max_qty, step_size
        return None, None, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange info: {e}")
        return None, None, None

if __name__ == "__main__":
    # Specify the trading pair
    trading_pair = "SUIUSDC"

    # Get maximum order size
    min_order, max_order, step_size = get_max_order_size(trading_pair)

    if max_order is not None:
        print(f"Trading Pair: {trading_pair}")
        print(f"Minimum Order Size: {min_order}")
        print(f"Maximum Order Size: {max_order}")
        print(f"Step Size: {step_size}")
    else:
        print(f"Unable to retrieve order size information for {trading_pair}.")
