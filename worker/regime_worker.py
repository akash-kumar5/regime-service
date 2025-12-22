# worker/regime_worker.py
import sys
import os

# Adds the project root (one level up) to the top of sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import pandas as pd
from core.predictor import predictor
from core.state import update_state
from core.feature_engineering import build_lstm_input
from core.data_fetcher import fetch_klines, merge_timeframes

REGIMES = [
    "STRONG_UPTREND",
    "WEAK_UPTREND",
    "RANGE",
    "SQUEEZE",
    "WEAK_DOWNTREND",
    "STRONG_DOWNTREND"
]


DATA_PATH = "data/BTCUSDT_combined_klines_20221107_20251106.csv"

SYMBOL = "BTCUSDT"
SLEEP_SECONDS = 100  # 5 minutes

def run_worker():
    print("Regime worker started (LIVE BINANCE)")

    while True:
        try:
            df_5m = fetch_klines(SYMBOL, "5m", limit=300)
            df_15m = fetch_klines(SYMBOL, "15m", limit=300)

            merged = merge_timeframes(df_5m, df_15m)

            X = build_lstm_input(
                merged_ohlcv_df=merged,
                feature_names=predictor.features,
                time_steps=predictor.time_steps
            )

            result = predictor.predict(X)

            update_state({
                "symbol": SYMBOL,
                **result
            })

            print("Updated state:", result)

        except Exception as e:
            print("Worker error:", e)

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    run_worker()
