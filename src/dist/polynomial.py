#!/usr/bin/env python3
"""
Polynomial Regression Bands + Channel [DW] — Python Example
-----------------------------------------------------------
Reads data from a CSV, optionally smooths it, computes an nth-order 
polynomial regression over a rolling window, calculates standard deviation 
bands, and logs trades to trades.txt (based on a very basic signal approach).
"""

import numpy as np
import pandas as pd

# =============================================================================
# 1. Super Smoother Filter (2-Pole) - same logic as the Pine Script SSF() function
# =============================================================================
def super_smoother_filter(series: np.ndarray, period: int) -> np.ndarray:
    """
    John Ehlers's 2-pole Super Smoother Filter.
    :param series: Price array to filter
    :param period: Smoothing period
    :return: Filtered array of same length as 'series'
    """
    # Defensive: if period is too small
    if period < 2:
        return series
    
    result = np.zeros_like(series)
    
    # Precompute constants
    from math import exp, sqrt, pi
    omega = 2 * pi * 4 / period
    a = exp(-sqrt(2) * pi * 4 / period)
    b = 2 * a * np.cos((sqrt(2)/2)*omega)
    c2 = b
    c3 = -(a**2)
    c1 = 1 - c2 - c3
    
    # Apply filter
    result[0] = series[0]
    result[1] = series[1]
    for i in range(2, len(series)):
        result[i] = (c1 * series[i]) + (c2 * result[i-1]) + (c3 * result[i-2])
    
    return result

# =============================================================================
# 2. Polynomial Regression Helper
#    We can replicate the same math from Pine, or simply use numpy.polyfit 
#    for convenience. The example below uses numpy.polyfit.
# =============================================================================
def polynomial_regression(x_vals: np.ndarray, y_vals: np.ndarray, degree: int) -> np.poly1d:
    """
    Returns a polynomial (as a function) that fits the data in a least-squares sense.
    :param x_vals: x-axis values (1D)
    :param y_vals: corresponding y-values (1D)
    :param degree: polynomial order
    :return: numpy.poly1d object which can be used as: poly(x)
    """
    coefs = np.polyfit(x_vals, y_vals, deg=degree)
    poly = np.poly1d(coefs)
    return poly

# =============================================================================
# 3. Main logic: reading data, computing polynomial bands, generating signals
# =============================================================================
def main(
    csv_file: str = "data.csv",
    period: int = 100,
    order: int = 2,
    smooth: bool = True,
    smooth_period: int = 10,
    stdev_mult: float = 2.0,
    forecast_bars_ago: int = 0,
    offset: int = 0
):
    """
    - Reads a CSV with columns: time, open, high, low, close, volume (common format).
    - Optionally applies the 2-pole Super Smoother to the close before regression.
    - Computes polynomial regression on a rolling window of length 'period'.
    - Writes signals to trades.txt based on a naive cross-over logic.
    """
    # Load data via pandas
    # Expected columns in CSV: time, open, high, low, close, volume
    df = pd.read_csv(csv_file)
    
    # Ensure columns exist
    required_cols = {"time", "open", "high", "low", "close", "volume"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"CSV missing columns: {missing_cols}")

    # Sort by time if not sorted
    df.sort_values(by="time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Convert "time" to a numeric index or keep as is
    # We'll use a numeric "bar index" approach for x-values
    df["bar_index"] = np.arange(len(df))
    
    # Optionally apply smoothing filter to the close
    if smooth:
        df["filtered_close"] = super_smoother_filter(df["close"].values, smooth_period)
        y_source = df["filtered_close"]
    else:
        y_source = df["close"]
    
    # Prepare a place to store the results: polynomial LSMA, upper band, lower band
    df["poly_lsma"] = np.nan
    df["poly_upper"] = np.nan
    df["poly_lower"] = np.nan
    
    # We'll store a trading "signal" state
    # For example: 1 = long, 0 = flat. (Simple demonstration.)
    df["signal"] = 0
    
    # Rolling polynomial calculation
    # We replicate the idea: for each bar i, we look back 'period' bars 
    # to compute polynomial regression. 
    # Then we shift by 'offset' or 'forecast_bars_ago' if desired.
    # Because polynomial fitting can be expensive, we'll do it only 
    # from i = period-1 to the end. 
    
    close_array = y_source.values
    bar_idx_array = df["bar_index"].values
    
    # We'll store trades in a list, then write to trades.txt
    trades = []
    position = 0  # 1 if long, 0 if flat, -1 if short (if you want short logic)
    
    for i in range(period - 1, len(df)):
        # Example approach: take a slice of length 'period'
        window_slice = slice(i - period + 1 - forecast_bars_ago, i + 1 - forecast_bars_ago)
        y_window = close_array[window_slice]
        x_window = bar_idx_array[window_slice]
        
        # For numerical stability, you might want to use a simpler x range like 1..period
        # But for clarity, we’ll just use the bar indices directly here.
        # If forecast_bars_ago > 0, effectively you're using older data to get the polynomial.
        
        # Fit the polynomial if we have a valid slice
        if len(y_window) == period:
            poly_func = polynomial_regression(x_window, y_window, order)
            
            # Evaluate the polynomial on the *current* bar index + offset
            # The user’s script does something like: poly(x - offset).
            # We can replicate that logic or keep it simple.
            # We'll define "eval_index" as the current bar minus offset, if you like.
            
            eval_index = df["bar_index"][i] - offset
            poly_value = poly_func(eval_index)
            
            # Calculate stdev of y_window
            # We'll measure stdev of the last 'period' real points from the window:
            stdev_window = np.std(y_window, ddof=1)  # sample stdev
            upper_band = poly_value + stdev_mult * stdev_window
            lower_band = poly_value - stdev_mult * stdev_window
            
            df.loc[i, "poly_lsma"] = poly_value
            df.loc[i, "poly_upper"] = upper_band
            df.loc[i, "poly_lower"] = lower_band
            
            # --------------------------------------------------------------------
            # Example naive trade logic:
            # If close > poly_value => go long
            # If close < poly_value => flat
            # This is very basic — adapt to your needs.
            # --------------------------------------------------------------------
            curr_close = df["close"][i]
            
            if position == 0:
                if curr_close > poly_value:
                    # Enter long
                    position = 1
                    trades.append((df["time"][i], "BUY", curr_close))
            elif position == 1:
                if curr_close < poly_value:
                    # Exit
                    position = 0
                    trades.append((df["time"][i], "SELL", curr_close))
            # If you wanted short logic, you'd handle position == -1 etc.
            
            df.loc[i, "signal"] = position
    
    # End main loop
    
    # =============================================================================
    # Write trades to trades.txt
    # =============================================================================
    with open("trades.txt", "w") as f:
        f.write("time,action,price\n")
        for t in trades:
            t_time, t_action, t_price = t
            f.write(f"{t_time},{t_action},{t_price}\n")

    print("Done! Results written to trades.txt")
    # Optionally, you could save the entire DataFrame with columns:
    # time, open, high, low, close, volume, poly_lsma, poly_upper, poly_lower, signal
    # to a CSV for further analysis
    # df.to_csv("output_with_poly.csv", index=False)

# =============================================================================
# If you want to run from the command line:
# python polynomial_regression_bands.py data.csv
# =============================================================================
if __name__ == "__main__":
    import sys
    
    # Basic argument handling
    if len(sys.argv) > 1:
        csv_input = sys.argv[1]
    else:
        csv_input = "data.csv"  # default fallback
    
    # You can tweak these parameters or expose them via argparse if you like:
    main(
        csv_file=csv_input,
        period=100,
        order=2,
        smooth=True,
        smooth_period=10,
        stdev_mult=2.0,
        forecast_bars_ago=0,
        offset=0
    )
