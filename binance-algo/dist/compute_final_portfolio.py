import os
import json5
from datetime import datetime

# File paths
API_KEY_FILE = "apikey-binance.json"
ASSET_FILE = "../view/output/asset.txt"
TRADES_FILE = "../view/output/trades.txt"
PORTFOLIO_FILE = "../view/output/portfolio.txt"

def load_api_data(file_path):
    """Load API key data with investment, margin, and annual interest rate."""
    with open(file_path, "r") as f:
        api_data = json5.load(f)
    return (
        float(api_data["investment"]),
        float(api_data["margin"]),
        float(api_data["margin_annual_interest_percentage"]) / 100
    )

def load_asset_data(file_path):
    """Load asset data as a dictionary of prices and events."""
    price_dict = {}
    asset_events = []
    with open(file_path, "r") as f:
        for line in f:
            timestamp, closing_price = map(float, line.strip().split(","))
            timestamp = int(timestamp)
            price_dict[timestamp] = closing_price
            asset_events.append((timestamp, 'price', closing_price))
    return price_dict, asset_events

def load_trade_data(file_path):
    """Load trade data as a list of trade events, ignoring additional parameters."""
    trade_events = []
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            timestamp, action = int(parts[0]), parts[1]
            trade_events.append((timestamp, 'trade', action))
    return trade_events


def process_events(events, price_dict, investment, margin, annual_interest_rate):
    """Simulate trades and portfolio value based on provided rules."""
    number_of_shares = 0.0
    cash_balance = investment
    debt = 0.0
    portfolio_data = []

    # Initialize the last known portfolio value to handle constant periods
    last_net_value = investment

    for timestamp, event_type, data in events:
        current_timestamp = datetime.fromtimestamp(timestamp)

        if event_type == 'price':
            closing_price = data
            # Calculate the net portfolio value
            net_value = (number_of_shares * closing_price + cash_balance - debt)
            last_net_value = net_value
            portfolio_data.append((timestamp, net_value))

        elif event_type == 'trade':
            closing_price = price_dict[timestamp]

            if data == 'buy':
                # Buy with all available cash and maximum margin
                total_funds = cash_balance + (cash_balance * margin)
                shares_to_buy = total_funds / closing_price
                number_of_shares += shares_to_buy
                debt += total_funds - cash_balance
                cash_balance = 0.0

            elif data == 'sell':
                # Sell all shares
                proceeds = number_of_shares * closing_price
                number_of_shares = 0.0
                if proceeds >= debt:
                    cash_balance += proceeds - debt
                    debt = 0.0
                else:
                    debt -= proceeds
                    cash_balance = 0.0

            # Recalculate net value after trade
            net_value = (number_of_shares * closing_price + cash_balance - debt)
            last_net_value = net_value
            portfolio_data.append((timestamp, net_value))

        else:
            # For events not affecting price or trade, keep last known portfolio value
            portfolio_data.append((timestamp, last_net_value))

    return portfolio_data

def save_portfolio_data(portfolio_data, file_path):
    """Save portfolio values to a file."""
    with open(file_path, "w") as f:
        for timestamp, value in portfolio_data:
            f.write(f"{timestamp},{value:.2f}\n")

def main():
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)

    # Load data
    investment, margin, annual_interest_rate = load_api_data(API_KEY_FILE)
    price_dict, asset_events = load_asset_data(ASSET_FILE)
    trade_events = load_trade_data(TRADES_FILE)

    # Merge and sort events
    events = sorted(asset_events + trade_events, key=lambda x: x[0])

    # Process portfolio values
    portfolio_data = process_events(events, price_dict, investment, margin, annual_interest_rate)

    # Save results
    save_portfolio_data(portfolio_data, PORTFOLIO_FILE)
    print(f"Portfolio data saved to {PORTFOLIO_FILE}")

if __name__ == "__main__":
    main()
