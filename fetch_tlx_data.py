import requests
import csv
from datetime import datetime, timedelta

# Base API URL
BASE_URL = "https://api.tlx.fi/functions/v1/prices"

# Tokens (Map token names to their IDs)
TOKENS = {
    "BTC4X": "0xCb9fB365f52BF2e49f7e76b7E8dd3e068171D136",
    "BTC2X": "0xc1422a15de4B7ED22EEedaEA2a4276De542C7a77",
    "BTC3X": "0x54cC16d2c91F6fa0a30d4C22868459085A7CE4d9",
    "ETH3X": "0xC013551A4c84BBcec4f75DBb8a45a444E2E9bbe7",
    "ETH2X": "0x46A0277d53274cAfbb089e9870d2448e4224dAD9",
    "SOL2X": "0x94cC3a994Af812628Fa50f0a4ABe1E2085618Fb8",
    "SOL3X": "0xe4DA85B92aE54ebF736EB51f0E962859454662fa",
}

# Granularities
GRANULARITIES = ["4hours"]

# Date range
START_DATE = datetime(2024, 8, 1)
END_DATE = datetime(2024, 11, 23)


def fetch_data(token_id, granularity, start_date, end_date):
    url = f"{BASE_URL}/{token_id}"
    params = {
        "granularity": granularity,
        "from": start_date.isoformat(),
        "to": end_date.isoformat()
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for Token ID {token_id} (Granularity: {granularity}): {response.status_code}")
        return []


def append_to_csv(data, output_file):
    if not data:
        print("No data to append.")
        return

    with open(output_file, "a", newline="") as f:
        writer = csv.writer(f)

        # Write header only if the file is empty
        if f.tell() == 0:
            writer.writerow(['time', 'close'])

        # Write data rows
        for entry in data:
            timestamp = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            time_formatted = timestamp.strftime("%d/%m/%Y %H:%M")
            close_price = entry["price"]
            writer.writerow([time_formatted, close_price])


def main():
    for token_name, token_id in TOKENS.items():
        output_file = f"TLX_{token_name}Data.csv"

        # Start with an empty file
        open(output_file, "w").close()

        for granularity in GRANULARITIES:
            current_date = START_DATE

            while current_date < END_DATE:
                next_date = current_date + timedelta(days=30)
                if next_date > END_DATE:
                    next_date = END_DATE

                print(f"Fetching {granularity} data for {token_name} from {current_date} to {next_date}")
                data = fetch_data(token_id, granularity, current_date, next_date)

                if data:
                    append_to_csv(data, output_file)

                current_date = next_date


if __name__ == "__main__":
    main()



























# import requests
# import csv
# from datetime import datetime, timedelta

# # Base API URL
# BASE_URL = "https://api.tlx.fi/functions/v1/prices"

# # Tokens (Map token names to their IDs)
# TOKENS = {
#     "BTC4X": "0xCb9fB365f52BF2e49f7e76b7E8dd3e068171D136",
#     "BTC2X": "0xc1422a15de4B7ED22EEedaEA2a4276De542C7a77",
#     "BTC3X": "0x54cC16d2c91F6fa0a30d4C22868459085A7CE4d9",
#     "ETH3X": "0xC013551A4c84BBcec4f75DBb8a45a444E2E9bbe7",
#     "ETH2X": "0x46A0277d53274cAfbb089e9870d2448e4224dAD9",
#     "SOL2X": "0x94cC3a994Af812628Fa50f0a4ABe1E2085618Fb8",
#     "SOL3X": "0xe4DA85B92aE54ebF736EB51f0E962859454662fa",
# }

# # Comprehensive list of possible granularities
# GRANULARITIES = [
#     # "1minute", 
#     # "5minutes", 
#     # "15minutes", 
#     # "30minutes",
#     # "1hour", 
#     "4hours", 
#     # "6hours", 
#     # "12hours",
#     # "1day", 
#     # "1week", 
#     # "1month"
# ]

# # Date range
# START_DATE = datetime(2024, 8, 1)  # Starting date
# END_DATE = datetime(2024, 11, 23)  # Ending date


# def fetch_data(token_id, granularity, start_date, end_date):
#     """
#     Fetch data for a specific token, granularity, and date range.
#     """
#     url = f"{BASE_URL}/{token_id}"
#     params = {
#         "granularity": granularity,
#         "from": start_date.isoformat(),
#         "to": end_date.isoformat()
#     }
#     response = requests.get(url, params=params)

#     if response.status_code == 200:
#         return response.json()  # Parse JSON response
#     else:
#         print(f"Failed to fetch data for Token ID {token_id} (Granularity: {granularity}): {response.status_code}")
#         return []


# def append_to_csv(data, token_name, granularity, output_file):
#     """
#     Append fetched data to a token-specific CSV file with granularity as a row-by-row field.
#     """
#     if not data:
#         print(f"No data to append for {token_name} ({granularity})")
#         return

#     with open(output_file, "a", newline="") as f:
#         writer = csv.writer(f)

#         # Write header only if the file is empty
#         if f.tell() == 0:
#             writer.writerow(["token", "granularity", "time", "close"])

#         # Write data rows
#         for entry in data:
#             writer.writerow([token_name, granularity, entry["timestamp"], entry["price"]])
#     print(f"Appended {len(data)} rows for {token_name} ({granularity}) to {output_file}")


# def main():
#     """
#     Main function to fetch and save data for all tokens and granularities into their respective files.
#     """
#     for token_name, token_id in TOKENS.items():
#         output_file = f"TLX_{token_name}Data.csv"  # Create token-specific filename

#         # Start with an empty file for each token
#         open(output_file, "w").close()

#         for granularity in GRANULARITIES:
#             current_date = START_DATE

#             # Iterate over time range in chunks (e.g., 30-day intervals)
#             while current_date < END_DATE:
#                 next_date = current_date + timedelta(days=30)
#                 if next_date > END_DATE:
#                     next_date = END_DATE

#                 print(f"Fetching {granularity} data for {token_name} from {current_date} to {next_date}")
#                 data = fetch_data(token_id, granularity, current_date, next_date)

#                 if data:
#                     # Append data to the token-specific file
#                     append_to_csv(data, token_name, granularity, output_file)

#                 current_date = next_date  # Move to the next time range


# if __name__ == "__main__":
#     main()
