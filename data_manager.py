from fetchData import (
    update_all_data as fetch_update_all_data,
    fetch_all_latest_day_close_values,
    initialize_csv as fetch_initialize_csv,
    append_to_csv as fetch_append_to_csv,
    read_csv as fetch_read_csv
)
from hmm_processor import process_data
from data_paths import get_addresses
import os

class DataManager:
    def __init__(self):
        self.addresses = get_addresses()
        self.bucket_name = os.getenv('BUCKET_NAME', 'my-csv-storage')

    def update_all_data(self):
        """
        Pobiera dane dla wszystkich adresów i zapisuje je do GCS, a następnie przetwarza te dane.
        """
        fetch_update_all_data(self.addresses)
        for filename in self.addresses.keys():
            process_data(filename)

    def get_all_latest_day_close_values(self):
        """
        Pobiera wartości 'close' z poprzedniego dnia dla wszystkich tokenów.

        :return: Słownik z nazwami tokenów i ich wartościami 'close'.
        """
        addresses1 = {
            "sol2XPriceData": "0x7d3c9c6566375d7ad6e89169ca5c01b5edc15364",
            "btc4XPriceData": "0x11b55966527ff030ca9c7b1c548b4be5e7eaee6d",
            "eth3XPriceData": "0x32b1d1bfd4b3b0cb9ff2dcd9dac757aa64d4cb69"
        }
        return fetch_all_latest_day_close_values(addresses1)

    def initialize_csv(self, blob_name, headers):
        """
        Inicjalizuje plik CSV w GCS z nagłówkami, jeśli jeszcze nie istnieje.

        :param blob_name: Nazwa pliku CSV w bucketcie GCS.
        :param headers: Lista nagłówków kolumn.
        """
        fetch_initialize_csv(blob_name, headers)

    def append_to_csv(self, blob_name, row):
        """
        Dodaje wiersz do istniejącego pliku CSV w GCS.

        :param blob_name: Nazwa pliku CSV w bucketcie GCS.
        :param row: Lista wartości do dodania jako nowy wiersz.
        """
        fetch_append_to_csv(blob_name, row)

    def read_csv(self, blob_name):
        """
        Odczytuje dane z pliku CSV w GCS.

        :param blob_name: Nazwa pliku CSV w bucketcie GCS.
        :return: Lista słowników reprezentujących wiersze CSV.
        """
        return fetch_read_csv(blob_name)

    def process_data(self, file_name, smoothing_on=True):
        """
        Przetwarza dane z pliku CSV w GCS.

        :param file_name: Nazwa pliku CSV w bucketcie GCS.
        :param smoothing_on: Flaga włączająca wygładzanie danych.
        :return: Przetworzony DataFrame Pandas.
        """
        return process_data(file_name, smoothing_on)

if __name__ == "__main__":
    manager = DataManager()
    manager.update_all_data()
