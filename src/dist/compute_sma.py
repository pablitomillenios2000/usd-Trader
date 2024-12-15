import os
import pandas as pd

# Paths
config_file = "apikey-binance.json"
asset_file = "../view/output/asset.txt"
ema_file = "../view/output/simple_ma.txt"

# Parameters
sma_window = 15000  # Configure the SMA window size

# Ensure the asset file exists
if not os.path.exists(asset_file):
    raise FileNotFoundError(f"The file {asset_file} does not exist.")

# Read asset data
try:
    df = pd.read_csv(
        asset_file, 
        header=None, 
        names=["timestamp", "price"], 
        dtype={"timestamp": int, "price": float}
    )
except Exception as e:
    raise ValueError(f"Error reading {asset_file}: {e}")

# Calculate SMA
df["sma"] = df["price"].rolling(window=sma_window).mean()

# Select only timestamp and SMA columns for output
output_df = df.dropna(subset=["sma"])[["timestamp", "sma"]]

# Output results
output_df.to_csv(ema_file, index=False, header=False, float_format="%.2f")

print(f"Simple Moving Average calculated and saved to {ema_file}.")
