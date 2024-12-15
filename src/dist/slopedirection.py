import os
from datetime import datetime

# File paths
slope_file = "../view/output/ema_slopes.txt"
slope_file_micro = "../view/output/ema_slopes_micro.txt"
direction_file = "../view/output/direction.txt"

def parse_ema_slopes(file_path):
    """
    Parses the EMA slopes file.
    Expects lines in the format:
    timestamp,slope,datetime

    Returns:
        list of tuples: [(timestamp, slope), ...]
    """
    data = []
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return data

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                parts = line.split(",")
                # Expecting at least timestamp, slope; datetime can be ignored if present
                if len(parts) < 2:
                    print(f"Skipping invalid line: {line}")
                    continue
                try:
                    timestamp = parts[0]
                    value = parts[1]
                    data.append((timestamp, float(value)))
                except ValueError:
                    print(f"Skipping invalid line: {line}")
    return data

def write_direction_file(slope_data, output_file):
    """
    Writes the direction file based on EMA slopes.
    If slope > 0, write timestamp,5000.
    If slope <= 0, write timestamp,4000.

    Args:
        slope_data (list of tuples): [(timestamp, slope), ...]
        output_file (str): Path to the direction file.
    """
    with open(output_file, 'w') as file:
        for timestamp, slope in slope_data:
            direction = 5000 if slope > 0 else 4000
            file.write(f"{timestamp},{direction}\n")

if __name__ == "__main__":
    # Parse EMA slopes file
    ema_slopes = parse_ema_slopes(slope_file)

    # Write direction file
    write_direction_file(ema_slopes, direction_file)

    print(f"Direction file written to: {direction_file}")
