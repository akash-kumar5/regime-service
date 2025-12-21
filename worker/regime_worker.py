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

REGIMES = [
    "STRONG_UPTREND",
    "WEAK_UPTREND",
    "RANGE",
    "SQUEEZE",
    "WEAK_DOWNTREND",
    "STRONG_DOWNTREND"
]

# def run_worker():
#     print("Regime worker started...")
#     while True:
#         regime = random.choice(REGIMES)
#         probs = {r: round(random.random(), 3) for r in REGIMES}

#         total = sum(probs.values())
#         probs = {k: v / total for k, v in probs.items()}

#         state = {
#             "symbol": "BTCUSDT",
#             "current_regime": regime,
#             "confidence": probs[regime],
#             "probabilities": probs
#         }

#         update_state(state)
#         # print("Updated state:", state)

#         time.sleep(5)  # simulate 5 min later



DATA_PATH = "data/BTCUSDT_combined_klines_20221107_20251106.csv"

def run_worker():
    print("Regime worker started (REAL FEATURES)")

    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])

    while True:
        X = build_lstm_input(
            merged_ohlcv_df=df,
            feature_names=predictor.features,
            time_steps=predictor.time_steps
        )

        result = predictor.predict(X)

        state = {
            "symbol": "BTCUSDT",
            **result
        }

        update_state(state)
        print("Updated state:", state)

        time.sleep(10)  # temporary

if __name__ == "__main__":
    run_worker()
