# Upadted Version on January 6th 2025 to reflect compound interest costs

import os
import json5
from datetime import datetime

# File paths
API_KEY_FILE = "apikey-crypto.json"
ASSET_FILE = "../view/output/asset.txt"
TRADES_FILE = "../view/output/trades.txt"
PORTFOLIO_FILE = "../view/output/portfolio.txt"

def load_api_data(file_path):
    """Load API key data with investment, margin, annual interest rate, and trade fee."""
    with open(file_path, "r") as f:
        api_data = json5.load(f)
    investment = float(api_data["investment"])
    margin = float(api_data["margin"])
    annual_interest_rate = float(api_data["margin_annual_interest_percentage"]) / 100
    trade_fee_percentage = float(api_data.get("trade_fee_percentage", 0.1)) / 100
    return investment, margin, annual_interest_rate, trade_fee_percentage

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

def accrue_interest(debt, annual_interest_rate, time_diff_seconds):
    """Calculate and return the interest accrued for the given time period on the debt."""
    if debt <= 0:
        return 0.0
    
    # Convert annual interest rate to a per-second compounded rate
    seconds_per_year = 365 * 24 * 3600
    per_second_rate = (1 + annual_interest_rate) ** (1 / seconds_per_year) - 1

    # Calculate interest using compound interest formula
    interest_for_period = debt * ((1 + per_second_rate) ** time_diff_seconds - 1)
    return interest_for_period

def process_events(events, price_dict, investment, margin, annual_interest_rate, trade_fee_percentage):
    """Simulate trades, including margin interest and trading fees, and produce portfolio values."""
    number_of_shares = 0.0
    cash_balance = investment
    debt = 0.0
    portfolio_data = []

    # Keep track of last event timestamp to accrue interest
    last_timestamp = None
    last_net_value = investment

    for timestamp, event_type, data in events:
        current_timestamp = datetime.fromtimestamp(timestamp)

        # First accrue interest since the last event (if any)
        if last_timestamp is not None:
            time_diff = timestamp - last_timestamp
            # Accrue interest on current debt
            interest = accrue_interest(debt, annual_interest_rate, time_diff)
            # Add the accrued interest to the debt
            debt += interest
        
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
                # Apply trade fee: fee is on the total notional of the trade
                fee = total_funds * trade_fee_percentage
                effective_funds = total_funds - fee

                shares_to_buy = effective_funds / closing_price
                number_of_shares += shares_to_buy
                # Debt is the borrowed part: (total_funds - cash_balance)
                borrowed = total_funds - cash_balance
                debt += borrowed
                cash_balance = 0.0

            elif data == 'sell':
                # Sell all shares
                proceeds = number_of_shares * closing_price
                # Apply fee: fee = proceeds * trade_fee_percentage
                fee = proceeds * trade_fee_percentage
                net_proceeds = proceeds - fee

                number_of_shares = 0.0
                if net_proceeds >= debt:
                    cash_balance += net_proceeds - debt
                    debt = 0.0
                else:
                    debt -= net_proceeds
                    cash_balance = 0.0

            # Recalculate net value after trade
            net_value = (number_of_shares * closing_price + cash_balance - debt)
            last_net_value = net_value
            portfolio_data.append((timestamp, net_value))

        else:
            # For events not affecting price or trade, keep last known portfolio value
            portfolio_data.append((timestamp, last_net_value))

        last_timestamp = timestamp

    return portfolio_data

def save_portfolio_data(portfolio_data, file_path):
    """Save portfolio values to a file."""
    with open(file_path, "w") as f:
        for timestamp, value in portfolio_data:
            f.write(f"{timestamp},{value:.2f}\n")

def main():
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)

    # Load data
    investment, margin, annual_interest_rate, trade_fee_percentage = load_api_data(API_KEY_FILE)
    price_dict, asset_events = load_asset_data(ASSET_FILE)
    trade_events = load_trade_data(TRADES_FILE)

    # Merge and sort events
    events = sorted(asset_events + trade_events, key=lambda x: x[0])

    # Process portfolio values with interest and fees
    portfolio_data = process_events(events, price_dict, investment, margin, annual_interest_rate, trade_fee_percentage)

    # Save results
    save_portfolio_data(portfolio_data, PORTFOLIO_FILE)
    print(f"Portfolio data saved to {PORTFOLIO_FILE}")

if __name__ == "__main__":
    main()
