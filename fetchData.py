import requests
import pandas as pd
from datetime import datetime, timezone
import os
from google.cloud import storage
from io import StringIO
import csv

BUCKET_NAME = os.getenv('BUCKET_NAME', 'my-csv-storage')

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

url = "https://api-v2.dhedge.org/graphql"
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

period = "1y"
interval = "4h"

def fetch_data(address):
    """
    Pobiera dane tokena z API.
    
    :param address: Adres tokena.
    :return: Lista świec (candles) z danymi cenowymi.
    """
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
    response.raise_for_status()
    data = response.json()
    candles = data.get("data", {}).get("tokenPriceCandles", [])
    return candles

def save_to_csv_gcs(address, filename):
    """
    Zapisuje dane tokena do pliku CSV w GCS.

    :param address: Adres tokena.
    :param filename: Nazwa pliku CSV.
    """
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

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()

    blob = bucket.blob(filename)
    blob.upload_from_string(csv_content, content_type='text/csv')

    print(f"Plik {filename} został zapisany w bucket {BUCKET_NAME}.")

def update_all_data(addresses):
    """
    Aktualizuje dane dla wszystkich adresów tokenów.

    :param addresses: Słownik mapujący nazwy plików CSV na adresy tokenów.
    """
    for filename, address in addresses.items():
        save_to_csv_gcs(address, filename)

def fetch_latest_day_close_values(address):
    """
    Pobiera wartość 'close' z poprzedniego dnia dla danego adresu tokena.

    :param address: Adres tokena.
    :return: Wartość 'close' z poprzedniego dnia lub None, jeśli nie znaleziono.
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
        "period": "2d",
        "interval": "1d"
    }

    try:
        response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
        response.raise_for_status()

        data = response.json()
        candles = data.get("data", {}).get("tokenPriceCandles", [])

        yesterday = (datetime.now(timezone.utc) - pd.Timedelta(days=1)).date()

        for candle in candles:
            timestamp = datetime.fromtimestamp(int(candle['timestamp']) / 1000, timezone.utc)
            if timestamp.date() == yesterday:
                close_value = float(candle['close']) / 1e18
                print(f"Timestamp: {timestamp}, Close: {close_value}")
                return close_value
        return None
    except Exception:
        return None

def fetch_all_latest_day_close_values(addresses1):
    """
    Pobiera wartości 'close' z poprzedniego dnia dla wszystkich tokenów.

    :param addresses1: Słownik mapujący nazwy tokenów na ich adresy.
    :return: Słownik z nazwami tokenów i ich wartościami 'close'.
    """
    all_close_values = {}
    for name, address in addresses1.items():
        print(f"Fetching close values for {name} ({address})")
        close_value = fetch_latest_day_close_values(address)
        if close_value is not None:
            all_close_values[name] = close_value
        else:
            print(f"No data found for {name} on the previous day.")
    return all_close_values

def initialize_csv(blob_name, headers):
    """
    Inicjalizuje plik CSV w GCS z nagłówkami, jeśli jeszcze nie istnieje.

    :param blob_name: Nazwa pliku CSV w bucketcie GCS.
    :param headers: Lista nagłówków kolumn.
    """
    blob = bucket.blob(blob_name)
    if not blob.exists():
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(headers)
        blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")
        print(f"Initialized CSV file {blob_name} in bucket {BUCKET_NAME}.")

def append_to_csv(blob_name, row):
    """
    Dodaje wiersz do istniejącego pliku CSV w GCS.

    :param blob_name: Nazwa pliku CSV w bucketcie GCS.
    :param row: Lista wartości do dodania jako nowy wiersz.
    """
    blob = bucket.blob(blob_name)
    if blob.exists():
        csv_content = blob.download_as_text()
        csv_buffer = StringIO(csv_content)
        reader = csv.reader(csv_buffer)
        rows = list(reader)
    else:
        rows = []
    rows.append(row)
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerows(rows)
    blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")
    print(f"Appended row to CSV file {blob_name} in bucket {BUCKET_NAME}.")

def read_csv(blob_name):
    """
    Odczytuje dane z pliku CSV w GCS.

    :param blob_name: Nazwa pliku CSV w bucketcie GCS.
    :return: Lista słowników reprezentujących wiersze CSV.
    """
    blob = bucket.blob(blob_name)
    if not blob.exists():
        return []
    csv_content = blob.download_as_text()
    reader = csv.DictReader(StringIO(csv_content))
    return [row for row in reader]
