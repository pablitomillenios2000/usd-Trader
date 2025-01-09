def main():
    account_info = get_cross_margin_account_info()
    if not account_info:
        print("Unable to retrieve cross margin account info.")
        return

    # The cross margin info is under account_info["userAssets"], which is a list
    user_assets = account_info.get("userAssets", [])

    # Include base_token, USDC, and BNB
    relevant_assets = [
        asset for asset in user_assets
        if asset["asset"] in [base_token.upper(), "USDC", "BNB"]
    ]

    # Extract netAsset values for each relevant token
    balances = {
        asset["asset"]: asset["netAsset"]
        for asset in relevant_assets
    }

    # Print the netAsset values in a single line
    print(f"{base_token.upper()}: {balances.get(base_token.upper(), 0)}, "
          f"USDC: {balances.get('USDC', 0)}, "
          f"BNB: {balances.get('BNB', 0)}")

    # --------------------------------------------------------------------------
    # ADDITIONAL: Calculate estimated net equity for USDC
    # --------------------------------------------------------------------------
    usdc_info = next((asset for asset in relevant_assets if asset["asset"] == "USDC"), None)
    if usdc_info:
        try:
            net_asset_usdc = abs(float(usdc_info["netAsset"]))
            net_equity = round(net_asset_usdc / leverage)
            print(f"\nThe estimated net equity is: ${net_equity}")

            # Write only net equity value to the output file
            with open(outfile, 'w') as f:
                f.write(str(net_equity) + "\n")

        except (ValueError, KeyError, TypeError) as err:
            print(f"\nCould not calculate estimated net equity for USDC: {err}")
    else:
        print("\nNo USDC asset found in the account info to calculate net equity.")
