# worker/regime_worker.py
import sys
import os
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

SYMBOL = "BTCUSDT"
SLEEP_SECONDS = 100  # 5 minutes

prev_regime = None
prev_confidence = None

def run_worker():
    global prev_regime, prev_confidence
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
            current_regime = result["current_regime"]
            confidence = result["confidence"]

            alerts = []

            # A. Strong trend confirmation
            if (
                current_regime == "Strong Trend"
                and confidence >= 0.65
                and prev_regime != "Strong Trend"
            ):
                alerts.append("STRONG_TREND_CONFIRMED")

            # B. Chop warning
            if (
                current_regime == "Choppy High-Vol"
                and confidence >= 0.6
                and prev_regime != "Choppy High-Vol"
            ):
                alerts.append("CHOPPY_MARKET_WARNING")

            # C. Regime flip
            if (
                prev_regime is not None
                and current_regime != prev_regime
                and confidence >= 0.55
            ):
                alerts.append(f"REGIME_CHANGE {prev_regime} → {current_regime}")

            # Print alerts (for now)
            for a in alerts:
                print("[ALERT]", a)

            # update previous state
            prev_regime = current_regime
            prev_confidence = confidence

            update_state({
                "symbol": SYMBOL,
                **result,
                "alerts":alerts
            })

            print("Updated state:", result)

        except Exception as e:
            print("Worker error:", e)

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    run_worker()
