import requests
import datetime
import pytz

def fetch_previous_close(symbol: str) -> float:
    """
    Fetches the previous day's closing price for a given symbol.

    Args:
        symbol (str): The trading pair symbol, e.g., BTCUSDT.

    Returns:
        float: Closing price from yesterday.

    Raises:
        RuntimeError: If unable to fetch the price from all sources.
    """
    PROXIES = {
        "http": "http://34.116.149.45:3128", 
        "https": "http://34.116.149.45:3128" 
    }

    def fetch_from_bybit(symbol: str) -> float:
        """Fetches the price from Bybit API."""
        try:
            bybit_symbol = symbol.replace("/", "").upper()
            utc_now = datetime.datetime.now(datetime.timezone.utc)
            yesterday = utc_now - datetime.timedelta(days=1)
            yesterday_date = yesterday.date()

            url = "https://api.bybit.com/v5/market/kline"
            params = {
                "category": "linear",
                "symbol": bybit_symbol,
                "interval": "D",
                "limit": 3,
            }

            headers = {"Accept": "application/json"}
            response = requests.get(url, params=params, headers=headers, proxies=PROXIES, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("retCode") != 0:
                raise ValueError(f"Bybit API error: {data.get('retMsg', 'No error message')}")

            candles = data.get("result", {}).get("list", [])
            if not candles:
                raise ValueError(f"No candles found for symbol {bybit_symbol}.")

            for candle in candles:
                candle_timestamp_ms = int(candle[0])
                candle_start = datetime.datetime.fromtimestamp(candle_timestamp_ms / 1000, datetime.timezone.utc).date()
                if candle_start == yesterday_date:
                    return float(candle[4])

            raise ValueError(f"Candle not found for date: {yesterday_date}.")

        except Exception as e:
            raise RuntimeError(f"Bybit API failure for {symbol}: {e}")

    def fetch_from_binance(symbol: str) -> float:
        """Fetches the price from Binance API."""
        try:
            utc_now = datetime.datetime.now(datetime.timezone.utc)
            yesterday = utc_now - datetime.timedelta(days=1)
            yesterday_timestamp = int(yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)

            url = f"https://api1.binance.com/api/v3/klines"
            params = {
                "symbol": symbol.upper(),
                "interval": "1d",
                "startTime": yesterday_timestamp,
                "limit": 1
            }

            headers = {"Accept": "application/json"}
            response = requests.get(url, params=params, headers=headers, proxies=PROXIES, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data:
                raise ValueError(f"No data returned for symbol {symbol} on Binance.")

            close_price = float(data[0][4]) 
            return close_price

        except Exception as e:
            raise RuntimeError(f"Binance API failure for {symbol}: {e}")

    try:
        return fetch_from_binance(symbol)
    except Exception as primary_error:
        try:
            return fetch_from_bybit(symbol)
        except Exception as secondary_error:
            raise RuntimeError(f"Failed to fetch price for {symbol}. Bybit error: {primary_error}, Binance error: {secondary_error}")
