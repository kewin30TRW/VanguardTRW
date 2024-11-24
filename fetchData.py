import requests
import pandas as pd
from datetime import datetime, timezone
import os

DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

url = "https://api-v2.dhedge.org/graphql"
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

period = "1y"
interval = "4h"

def fetch_data(address):
    query = """
    query GetTokenPriceCandles($address: String!, $period: String!, $interval: String) {
      tokenPriceCandles(address: $address, period: $period, interval: $interval) {
        timestamp
        open
        close
        max
        min
      }
    }
    """
    variables = {"address": address, "period": period, "interval": interval}
    response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
    data = response.json()
    candles = data.get("data", {}).get("tokenPriceCandles", [])
    return candles


def save_to_csv(address, filename):
    candles = fetch_data(address)
    rows = []
    for candle in candles:
        time = datetime.fromtimestamp(int(candle['timestamp']) / 1000, timezone.utc).strftime('%d/%m/%Y %H:%M')
        open_price = float(candle['open']) / 1e18
        high_price = float(candle['max']) / 1e18
        low_price = float(candle['min']) / 1e18
        close_price = float(candle['close']) / 1e18
        rows.append([time, open_price, high_price, low_price, close_price])

    df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close'])
    df.to_csv(filename, index=False)

addresses = {
    os.path.join(DATA_DIR, "sol2XPriceData.csv"): "0x7d3c9c6566375d7ad6e89169ca5c01b5edc15364",
    os.path.join(DATA_DIR, "sol3XPriceData.csv"): "0xcc7d6ed524760539311ed0cdb41d0852b4eb77eb",
    os.path.join(DATA_DIR, "btc2XPriceData.csv"): "0x32ad28356ef70adc3ec051d8aacdeeaa10135296",
    os.path.join(DATA_DIR, "btc3XPriceData.csv"): "0xb03818de4992388260b62259361778cf98485dfe",
    os.path.join(DATA_DIR, "btc4XPriceData.csv"): "0x11b55966527ff030ca9c7b1c548b4be5e7eaee6d",
    os.path.join(DATA_DIR, "eth2XPriceData.csv"): "0x9573c7b691cdcebbfa9d655181f291799dfb7cf5",
    os.path.join(DATA_DIR, "eth3XPriceData.csv"): "0x32b1d1bfd4b3b0cb9ff2dcd9dac757aa64d4cb69"
}

addresses1 = {
    "sol2XPriceData": "0x7d3c9c6566375d7ad6e89169ca5c01b5edc15364",
    "btc4XPriceData": "0x11b55966527ff030ca9c7b1c548b4be5e7eaee6d",
    "eth3XPriceData": "0x32b1d1bfd4b3b0cb9ff2dcd9dac757aa64d4cb69"
}

def update_all_data():
    for filename, address in addresses.items():
        save_to_csv(address, filename)

def fetch_latest_day_close_values(address):
    """
    Fetch the latest day's `close` values for a given token address.
    """
    query = """
    query GetTokenPriceCandles($address: String!, $period: String!, $interval: String!) {
      tokenPriceCandles(address: $address, period: $period, interval: $interval) {
        timestamp
        close
      }
    }
    """
    variables = {
        "address": address,
        "period": "1d",  # Fetch data from the last 7 days
        "interval": "1h"
    }

    try:
        response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
        response.raise_for_status()

        data = response.json()
        candles = data.get("data", {}).get("tokenPriceCandles", [])

        # Debugging logs
        print(f"Raw API Response for {address}: {candles}")

        # Process candles and extract close values for the current day
        now = datetime.now(timezone.utc).date()
        latest_day_closes = []
        for candle in candles:
            timestamp = datetime.fromtimestamp(int(candle['timestamp']) / 1000, timezone.utc)
            if timestamp.date() == now:
                close_value = float(candle['close']) / 1e18
                latest_day_closes.append(close_value)
                print(f"Timestamp: {timestamp}, Close: {close_value}")

        print(f"Filtered close values for {address}: {latest_day_closes}")
        return latest_day_closes
    except Exception as e:
        print(f"Error fetching data for {address}: {e}")
        return []
    
def fetch_all_latest_day_close_values():
    """
    Fetch the latest day's `close` values for all token addresses.

    :return: Dictionary of token names to their latest day's `close` values.
    """
    all_close_values = {}
    for name, address in addresses1.items():
        print(f"Fetching close values for {name} ({address})")
        all_close_values[name] = fetch_latest_day_close_values(address)
    return all_close_values
