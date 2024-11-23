import os

def get_addresses(data_dir):
    return {
        "sol2X": os.path.join(data_dir, "sol2XPriceData.csv"),
        "sol3X": os.path.join(data_dir, "sol3XPriceData.csv"),
        "btc2X": os.path.join(data_dir, "btc2XPriceData.csv"),
        "btc3X": os.path.join(data_dir, "btc3XPriceData.csv"),
        "btc4X": os.path.join(data_dir, "btc4XPriceData.csv"),
        "eth2X": os.path.join(data_dir, "eth2XPriceData.csv"),
        "eth3X": os.path.join(data_dir, "eth3XPriceData.csv"),
        "TLX_SOL2X": os.path.join(data_dir, "TLX_SOL2XData.csv"),
        "TLX_SOL3X": os.path.join(data_dir, "TLX_SOL3XData.csv"),
        "TLX_BTC2X": os.path.join(data_dir, "TLX_BTC2XData.csv"),
        "TLX_BTC3X": os.path.join(data_dir, "TLX_BTC3XData.csv"),
        "TLX_BTC4X": os.path.join(data_dir, "TLX_BTC4XData.csv"),
        "TLX_ETH2X": os.path.join(data_dir, "TLX_ETH2XData.csv"),
        "TLX_ETH3X": os.path.join(data_dir, "TLX_ETH3XData.csv"),
    }