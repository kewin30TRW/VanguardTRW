import requests
import pandas as pd
from datetime import datetime, timezone
import os
from google.cloud import storage
from io import StringIO
import csv
import logging

logging.basicConfig(level=logging.DEBUG)

ENV = os.getenv("ENV", "local")
BUCKET_NAME = os.getenv('BUCKET_NAME', 'my-csv-storage')

# Lokalne katalogi dla danych
DATA_FILES_DIR = os.path.join(os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__))), "data")

if ENV == "production":
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
else:
    # Upewnij się, że katalog data istnieje
    if not os.path.exists(DATA_FILES_DIR):
        os.makedirs(DATA_FILES_DIR)

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

def save_to_csv(address, filename):
    """
    Zapisuje dane tokena do pliku CSV w GCS lub lokalnie.

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

    if ENV == "production":
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()

        blob = bucket.blob(filename)
        blob.upload_from_string(csv_content, content_type='text/csv')

        logging.info(f"Plik {filename} został zapisany w bucket {BUCKET_NAME}.")
    else:
        local_path = os.path.join(DATA_FILES_DIR, filename)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        df.to_csv(local_path, index=False)
        logging.info(f"Plik {filename} został zapisany lokalnie w {local_path}.")

def update_all_data(addresses):
    """
    Aktualizuje dane dla wszystkich adresów tokenów.

    :param addresses: Słownik mapujący nazwy plików CSV na adresy tokenów.
    """
    for filename, address in addresses.items():
        save_to_csv(address, filename)

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
                logging.info(f"Timestamp: {timestamp}, Close: {close_value}")
                return close_value
        return None
    except Exception as e:
        logging.error(f"Error fetching latest close value for address {address}: {e}")
        return None

def fetch_all_latest_day_close_values(addresses1):
    """
    Pobiera wartości 'close' z poprzedniego dnia dla wszystkich tokenów.

    :param addresses1: Słownik mapujący nazwy tokenów na ich adresy.
    :return: Słownik z nazwami tokenów i ich wartościami 'close'.
    """
    all_close_values = {}
    for name, address in addresses1.items():
        logging.info(f"Fetching close values for {name} ({address})")
        close_value = fetch_latest_day_close_values(address)
        if close_value is not None:
            all_close_values[name] = close_value
        else:
            logging.warning(f"No data found for {name} on the previous day.")
    return all_close_values

def initialize_csv(blob_name, headers):
    """
    Inicjalizuje plik CSV w GCS lub lokalnie z nagłówkami, jeśli jeszcze nie istnieje.

    :param blob_name: Nazwa pliku CSV w bucketcie GCS lub w lokalnym katalogu.
    :param headers: Lista nagłówków kolumn.
    """
    if ENV == "production":
        blob = bucket.blob(blob_name)
        if not blob.exists():
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(headers)
            blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")
            logging.info(f"Initialized CSV file {blob_name} in bucket {BUCKET_NAME}.")
    else:
        local_path = os.path.join(DATA_FILES_DIR, blob_name)
        if not os.path.exists(local_path):
            empty_df = pd.DataFrame(columns=headers)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            empty_df.to_csv(local_path, index=False)
            logging.info(f"Initialized CSV file {local_path} locally.")

def append_to_csv(blob_name, row):
    """
    Dodaje wiersz do istniejącego pliku CSV w GCS lub lokalnie.

    :param blob_name: Nazwa pliku CSV w bucketcie GCS lub w lokalnym katalogu.
    :param row: Lista wartości do dodania jako nowy wiersz.
    """
    if ENV == "production":
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
        logging.info(f"Appended row to CSV file {blob_name} in bucket {BUCKET_NAME}.")
    else:
        local_path = os.path.join(DATA_FILES_DIR, blob_name)
        if os.path.exists(local_path):
            df = pd.read_csv(local_path)
        else:
            df = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close'])
        df.loc[len(df)] = row
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        df.to_csv(local_path, index=False)
        logging.info(f"Appended row to CSV file {local_path} locally.")

def read_csv(blob_name):
    """
    Odczytuje dane z pliku CSV w GCS lub lokalnie.

    :param blob_name: Nazwa pliku CSV w bucketcie GCS lub w lokalnym katalogu.
    :return: Lista słowników reprezentujących wiersze CSV.
    """
    if ENV == "production":
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return []
        csv_content = blob.download_as_text()
        reader = csv.DictReader(StringIO(csv_content))
        return [row for row in reader]
    else:
        local_path = os.path.join(DATA_FILES_DIR, blob_name)
        if not os.path.exists(local_path):
            return []
        df = pd.read_csv(local_path)
        return df.to_dict(orient='records')
