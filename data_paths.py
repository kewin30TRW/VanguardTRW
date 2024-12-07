def get_addresses():
    """
    Zwraca słownik mapujący nazwy plików CSV na adresy tokenów.

    :return: Słownik z nazwami plików CSV jako klucze i adresami tokenów jako wartości.
    """
    return {
        "sol2XPriceData.csv": "0x7d3c9c6566375d7ad6e89169ca5c01b5edc15364",
        "sol3XPriceData.csv": "0xcc7d6ed524760539311ed0cdb41d0852b4eb77eb",
        "btc2XPriceData.csv": "0x32ad28356ef70adc3ec051d8aacdeeaa10135296",
        "btc3XPriceData.csv": "0xb03818de4992388260b62259361778cf98485dfe",
        "btc4XPriceData.csv": "0x11b55966527ff030ca9c7b1c548b4be5e7eaee6d",
        "eth2XPriceData.csv": "0x9573c7b691cdcebbfa9d655181f291799dfb7cf5",
        "eth3XPriceData.csv": "0x32b1d1bfd4b3b0cb9ff2dcd9dac757aa64d4cb69"
    }
