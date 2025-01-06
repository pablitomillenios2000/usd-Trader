import requests
import time
import hashlib
import hmac
from pathlib import Path
import json5
import json

# Load API keys
home_dir = Path.home()
with open(f"{home_dir}/CRYPTO-Trader/src/dist/apikey-crypto.json", "r") as file:
    config = json5.load(file)

API_KEY = config.get("key")
SECRET_KEY = config.get("secret")

# 📥 Endpoint for account info
url = 'https://api.mexc.com/api/v3/sub-account/asset'

# 📅 Generate timestamp
timestamp = int(time.time() * 1000)

# 🔗 Build the query string with the new parameters
account_type = "SPOT"
sub_account = "pablito1234"
query_string = f'timestamp={timestamp}&accountType={account_type}&subAccount={sub_account}'

# 🖊️ Sign the request
signature = hmac.new(
    SECRET_KEY.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# 📦 Add the signature to the query string
query_string += f'&signature={signature}'

# 📤 Make the request
headers = {
    'X-MEXC-APIKEY': API_KEY
}

# Send the request with the query string parameters
params = {
    'timestamp': timestamp,
    'accountType': account_type,
    'subAccount': sub_account,
    'signature': signature
}

response = requests.get(url, headers=headers, params=params)

# 📋 Print the response
if response.status_code == 200:
    print("Account Info:")
    print(json.dumps(response.json(), indent=4, sort_keys=True))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
