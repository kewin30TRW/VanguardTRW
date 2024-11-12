from fetchData import update_all_data
from hmm_processor import process_data

class DataManager:
    def __init__(self, addresses):
        self.addresses = addresses

    def update_all_data(self):
        update_all_data()
        for file_path in self.addresses.values():
            process_data(file_path)
