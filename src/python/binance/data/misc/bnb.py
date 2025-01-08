import requests
import time
import hmac
import hashlib
import json

# Binance API credentials
API_KEY = "your_api_key_here"
SECRET_KEY = "your_secret_key_here"

# Binance API endpoint
BASE_URL = "https://api.binance.com"
ENDPOINT = "/sapi/v1/broker/subAccount/bnbBurn/marginInterest"

# Parameters to enable BNB burn
params = {
    "interestBNBBurn": "true",  # Set to "true" to enable BNB burn
    "timestamp": int(time.time() * 1000),
}

# Create the signature
query_string = "&".join([f"{key}={value}" for key, value in params.items()])
signature = hmac.new(SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
params["signature"] = signature

# Headers for the request
headers = {
    "X-MBX-APIKEY": API_KEY,
}

# Make the request
response = requests.post(BASE_URL + ENDPOINT, headers=headers, params=params)

# Detailed response handling
if response.status_code == 200:
    try:
        data = response.json()
        print("✅ BNB Burn for Margin Interest has been successfully enabled!")
        print(json.dumps(data, indent=4))
    except json.JSONDecodeError:
        print("⚠️ Success, but unable to parse JSON response.")
else:
    print(f"❌ Failed to enable BNB burn. HTTP Status Code: {response.status_code}")
    try:
        error_data = response.json()
        print("Error Details:")
        print(json.dumps(error_data, indent=4))
    except json.JSONDecodeError:
        print("⚠️ Unable to parse error response as JSON.")
