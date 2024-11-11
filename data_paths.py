import os

def get_addresses(data_dir):
    return {
        "sol2X": os.path.join(data_dir, "sol2XPriceData.csv"),
        "sol3X": os.path.join(data_dir, "sol3XPriceData.csv"),
        "btc2X": os.path.join(data_dir, "btc2XPriceData.csv"),
        "btc3X": os.path.join(data_dir, "btc3XPriceData.csv"),
        "btc4X": os.path.join(data_dir, "btc4XPriceData.csv"),
        "eth2X": os.path.join(data_dir, "eth2XPriceData.csv"),
        "eth3X": os.path.join(data_dir, "eth3XPriceData.csv")
    }