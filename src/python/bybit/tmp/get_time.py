import requests

def get_bybit_server_time():
    url = "https://api.bybit.com/v5/market/time"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        time_ms = data.get("time")  # in milliseconds
        time_s = data.get("result", {}).get("timeSecond")
        time_nano = data.get("result", {}).get("timeNano")
        
        return time_ms, time_s, time_nano
    else:
        raise Exception(f"Failed to get server time. Status code: {response.status_code}")

if __name__ == "__main__":
    time_ms, time_s, time_nano = get_bybit_server_time()
    print("Bybit Server Time (ms):", time_ms)
    print("Bybit Server Time (s):", time_s)
    print("Bybit Server Time (ns):", time_nano)
