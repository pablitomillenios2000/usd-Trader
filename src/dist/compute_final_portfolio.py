# Computes interest
# Fees are only for the costs.txt since they are in bnb
# There is a breakdown of costs in the view/output/costs.txt
# Slippage for a 100K order was estimated, we now incorporate it using slippage_percent from the JSON

import os
import json5
from datetime import datetime

# File paths
API_KEY_FILE = "apikey-crypto.json"
ASSET_FILE = "../view/output/asset.txt"
TRADES_FILE = "../view/output/trades.txt"
PORTFOLIO_FILE = "../view/output/portfolio.txt"
COSTS_FILE = "../view/output/costs.txt"

def load_api_data(file_path):
    """
    Load API key data with:
      - investment
      - margin
      - annual interest rate
      - trade fee percentage
      - slippage percentage
    """
    with open(file_path, "r") as f:
        api_data = json5.load(f)
    investment = float(api_data["investment"])
    margin = float(api_data["margin"])
    annual_interest_rate = float(api_data["margin_annual_interest_percentage"]) / 100
    trade_fee_percentage = float(api_data.get("trade_fee_percentage", 0.1)) / 100
    
    # Load slippage_percent, default to 0 if not found
    slippage_percent = float(api_data.get("slippage_percent", 0.0)) / 100
    
    return investment, margin, annual_interest_rate, trade_fee_percentage, slippage_percent

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

def accrue_interest(debt, annual_interest_rate, time_diff_seconds, cash_balance):
    """
    Calculate and return:
      1) The updated debt
      2) The updated cash_balance
      3) The interest accrued in this period
    
    Now we deduct interest from USDC if possible. If not enough cash,
    the remainder is added to 'debt'.
    """
    if debt <= 0:
        # No debt => no interest
        return debt, cash_balance, 0.0

    # Convert annual interest rate to a per-second compounded rate
    seconds_per_year = 365 * 24 * 3600
    per_second_rate = (1 + annual_interest_rate) ** (1 / seconds_per_year) - 1

    # Calculate interest using compound interest formula
    interest_for_period = debt * ((1 + per_second_rate) ** time_diff_seconds - 1)

    # Now pay interest from cash_balance if possible
    if cash_balance >= interest_for_period:
        # Deduct interest from USDC
        cash_balance -= interest_for_period
    else:
        # Not enough USDC to cover interest, so the remainder is added to debt
        shortfall = interest_for_period - cash_balance
        cash_balance = 0.0
        debt += shortfall

    return debt, cash_balance, interest_for_period

def process_events(
    events, 
    price_dict, 
    investment, 
    margin, 
    annual_interest_rate, 
    trade_fee_percentage,
    slippage_percent
):
    """
    Simulate trades (buy/sell) and margin interest, then produce portfolio values.

    IMPORTANT:
      - Fees are NOT deducted from the portfolio in USDC,
        because they're paid separately in BNB.
      - Slippage is accounted for by adjusting the buy/sell prices.
      - Interest is deducted from USDC if possible; if not, it is added to debt.
    
    Returns:
        portfolio_data (list): (timestamp, net_value)
        total_interest_cost (float): The total interest accrued on margin
        total_fees_cost (float): The total trading fees, paid in BNB (not deducted from USDC).
    """
    number_of_shares = 0.0
    cash_balance = investment
    debt = 0.0

    portfolio_data = []
    total_interest_cost = 0.0
    total_fees_cost = 0.0

    # Keep track of last event timestamp for accruing interest
    last_timestamp = None
    last_net_value = investment

    for timestamp, event_type, data in events:
        # First, accrue interest since the last event (if any)
        if last_timestamp is not None:
            time_diff = timestamp - last_timestamp
            debt, cash_balance, interest_accrued = accrue_interest(
                debt, 
                annual_interest_rate, 
                time_diff, 
                cash_balance
            )
            total_interest_cost += interest_accrued

        if event_type == 'price':
            # Update net portfolio value based on current price
            closing_price = data
            net_value = (number_of_shares * closing_price + cash_balance - debt)
            last_net_value = net_value
            portfolio_data.append((timestamp, net_value))

        elif event_type == 'trade':
            # Get the latest known price for the trade timestamp
            closing_price = price_dict[timestamp]

            if data == 'buy':
                # Effective buy price includes upward slippage
                buy_price = closing_price * (1 + slippage_percent)

                # Buy with all available cash + margin
                total_funds = cash_balance + (cash_balance * margin)  # 4x => 5x total
                
                # Trading fee (in BNB, not deducted from USDC)
                fee = total_funds * trade_fee_percentage
                total_fees_cost += fee
                
                # Actual USDC we can use to buy (assuming we're not subtracting fees from USDC)
                # If we wanted to pay fees in USDC, we would do: total_funds - fee
                # But the script states fees are paid in BNB. So we do not reduce total_funds.
                
                # Borrowed amount
                borrowed = total_funds - cash_balance
                debt += borrowed

                # The entire total_funds is used to buy
                shares_to_buy = total_funds / buy_price
                number_of_shares += shares_to_buy

                # After buying, cash is depleted
                cash_balance = 0.0

            elif data == 'sell':
                # Effective sell price includes downward slippage
                sell_price = closing_price * (1 - slippage_percent)
                
                # Sell all shares
                proceeds = number_of_shares * sell_price

                # Fee on the proceeds (paid in BNB)
                fee = proceeds * trade_fee_percentage
                total_fees_cost += fee

                # Reset our shares
                number_of_shares = 0.0

                # Use proceeds to pay debt first
                if proceeds >= debt:
                    cash_balance += (proceeds - debt)
                    debt = 0.0
                else:
                    debt -= proceeds
                    cash_balance = 0.0

            # Recalculate net value
            net_value = (number_of_shares * closing_price + cash_balance - debt)
            last_net_value = net_value
            portfolio_data.append((timestamp, net_value))

        else:
            # If it's not a price or trade event, just keep the last known value
            portfolio_data.append((timestamp, last_net_value))

        last_timestamp = timestamp

    return portfolio_data, total_interest_cost, total_fees_cost

def save_portfolio_data(portfolio_data, file_path):
    """Save portfolio values to a file."""
    with open(file_path, "w") as f:
        for timestamp, value in portfolio_data:
            f.write(f"{timestamp},{value:.2f}\n")

def format_with_upticks(value, currency="$usdc"):
    """
    Convert a float to a string with 2 decimal places and 
    use upticks `'` for thousands separators, then append a currency unit.
    
    Example:
       1234567.89 -> "1'234'567.89 $usdc"
    """
    base_formatted = "{:,.2f}".format(value)  # e.g. "1,234,567.89"
    with_upticks = base_formatted.replace(",", "'")  # e.g. "1'234'567.89"
    return f"{with_upticks} {currency}"

def save_costs_data(
    total_interest_cost, 
    total_fees_cost, 
    final_portfolio_value, 
    portfolio_including_fees, 
    file_path
):
    """
    Save cost variables to a file, with upticks and currency appended.
    """
    with open(file_path, "w") as f:
        f.write(f"total_interest_cost,{format_with_upticks(total_interest_cost, '$usdc')}\n")
        f.write(f"total_fees_cost,{format_with_upticks(total_fees_cost, '$usdc')}\n")
        f.write(f"final_portfolio,{format_with_upticks(final_portfolio_value, '$usdc')}\n")
        f.write(f"portfolio_including_fees,{format_with_upticks(portfolio_including_fees, '$usdc')}\n")

def main():
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)

    # Load data
    (investment, 
     margin, 
     annual_interest_rate, 
     trade_fee_percentage, 
     slippage_percent) = load_api_data(API_KEY_FILE)
     
    price_dict, asset_events = load_asset_data(ASSET_FILE)
    trade_events = load_trade_data(TRADES_FILE)

    # Merge all events and sort by timestamp
    events = sorted(asset_events + trade_events, key=lambda x: x[0])

    # Process trades, track portfolio values and costs
    portfolio_data, total_interest_cost, total_fees_cost = process_events(
        events, 
        price_dict, 
        investment, 
        margin, 
        annual_interest_rate, 
        trade_fee_percentage,
        slippage_percent
    )

    # The final portfolio value is the net_value from the last entry in portfolio_data
    final_portfolio_value = portfolio_data[-1][1] if portfolio_data else 0.0

    # Portfolio value minus the total fees cost
    portfolio_including_fees = final_portfolio_value - total_fees_cost

    # Save portfolio results
    save_portfolio_data(portfolio_data, PORTFOLIO_FILE)
    print(f"Portfolio data saved to {PORTFOLIO_FILE}")

    # Save cost results (now includes final_portfolio and portfolio_including_fees)
    save_costs_data(
        total_interest_cost, 
        total_fees_cost,
        final_portfolio_value,
        portfolio_including_fees,
        COSTS_FILE
    )
    print(f"Costs data saved to {COSTS_FILE}")

if __name__ == "__main__":
    main()
