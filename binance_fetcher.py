import ccxt
import datetime
import pytz

def fetch_previous_close(symbol: str) -> float:
    """
    Fetches the CLOSE value of the previous daily bar for the given symbol from Binance.
    
    Args:
        symbol (str): The trading pair symbol (e.g., 'XLMUSDT').

    Returns:
        float: The CLOSE value of the previous bar.
    """
    try:
        binance = ccxt.binance({
            "rateLimit": 1200,
            "enableRateLimit": True,
        })

        binance_symbol = symbol.replace("/", "")

        utc_now = datetime.datetime.now(pytz.utc)

        start_of_previous_day = (utc_now - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_previous_day = start_of_previous_day + datetime.timedelta(days=1)

        since_timestamp = int(start_of_previous_day.timestamp() * 1000)
        ohlcv = binance.fetch_ohlcv(binance_symbol, timeframe='1d', since=since_timestamp)

        if not ohlcv:
            raise ValueError(f"No OHLCV data available for {symbol}")

        previous_day_bar = [
            bar for bar in ohlcv
            if start_of_previous_day.timestamp() * 1000 <= bar[0] < end_of_previous_day.timestamp() * 1000
        ]

        if not previous_day_bar:
            raise ValueError(f"No data for the previous day for {symbol}")

        close_price = previous_day_bar[0][4]

        return close_price

    except Exception as e:
        raise RuntimeError(f"Failed to fetch data for {symbol}: {e}")
