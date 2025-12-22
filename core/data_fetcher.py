import requests
import pandas as pd

BINANCE_BASE = "https://api.binance.com"

def fetch_klines(symbol: str, interval: str, limit: int = 300) -> pd.DataFrame:
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    cols = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ]

    df = pd.DataFrame(data, columns=cols)

    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df[["timestamp", "open", "high", "low", "close", "volume"]]

def merge_timeframes(df_5m: pd.DataFrame, df_15m: pd.DataFrame) -> pd.DataFrame:
    df_5m = df_5m.copy()
    df_15m = df_15m.copy()

    df_5m = df_5m.rename(columns={
        "open": "open_5m",
        "high": "high_5m",
        "low": "low_5m",
        "close": "close_5m",
        "volume": "volume_5m",
    })

    df_15m = df_15m.rename(columns={
        "open": "open_15m",
        "high": "high_15m",
        "low": "low_15m",
        "close": "close_15m",
        "volume": "volume_15m",
    })

    merged = pd.merge_asof(
        df_5m.sort_values("timestamp"),
        df_15m.sort_values("timestamp"),
        on="timestamp",
        direction="backward"
    )

    return merged
