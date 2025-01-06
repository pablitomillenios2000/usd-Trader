import requests
import time
import hashlib
import hmac
from pathlib import Path
import json5

# Load API keys
with open(f"{Path.home()}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
    config = json5.load(file)

API_KEY = config["key"]
SECRET_KEY = config["secret"]
BASE_URL = 'https://contract.mexc.com'

# Generate signature
def sign_request(query_string):
    return hmac.new(SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()

# Place a market order to buy 1 SUIUSDT
def place_order():
    url = f'{BASE_URL}/api/v1/order'
    timestamp = int(time.time() * 1000)
    query_string = f'symbol=SUIUSDT&side=BUY&type=MARKET&vol=1&timestamp={timestamp}'
    signature = sign_request(query_string)
    
    response = requests.post(
        url,
        headers={'X-MEXC-APIKEY': API_KEY},
        params={'symbol': 'SUIUSDT', 'side': 'BUY', 'type': 'MARKET', 'vol': 1, 'timestamp': timestamp, 'signature': signature}
    )
    
    print(response.json())

if __name__ == "__main__":
    place_order()
