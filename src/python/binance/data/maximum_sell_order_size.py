import requests

BASE_URL = "https://api.binance.com"

def get_order_limits(pair):
    endpoint = "/api/v3/exchangeInfo"
    url = BASE_URL + endpoint

    response = requests.get(url)
    data = response.json()

    for symbol in data['symbols']:
        if symbol['symbol'] == pair:
            for filter in symbol['filters']:
                if filter['filterType'] == "LOT_SIZE":
                    return {
                        "minQty": float(filter['minQty']),
                        "maxQty": float(filter['maxQty']),
                        "stepSize": float(filter['stepSize'])
                    }
    return None

if __name__ == "__main__":
    pair = "SUIUSDC"
    limits = get_order_limits(pair)
    if limits:
        print(f"Sell Order Limits for {pair}:")
        print(f"Minimum Order Size: {limits['minQty']} SUI")
        print(f"Maximum Order Size: {limits['maxQty']} SUI")
        print(f"Step Size: {limits['stepSize']} SUI")
    else:
        print(f"Could not retrieve order limits for {pair}.")
