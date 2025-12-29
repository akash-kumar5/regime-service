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
from telegram.bot import load_settings
from telegram.notifier import send_message

settings = load_settings()

REGIMES = [
    "Choppy High-Vol",
    "Range",
    "Squeeze",
    "Strong Trend",
    "Volatility Spike",
    "Weak Trend",
]

SYMBOL = "BTCUSDT"
SLEEP_SECONDS = 120  # 2 minutes

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
            

            update_state({
                "symbol": SYMBOL,
                **result,
                "alerts":alerts
            })

            print("Updated state:", result)

        except Exception as e:
            print("Worker error:", e)

        time.sleep(SLEEP_SECONDS)

        for chat_id, prefs in settings.items():
            # A. alert-based notifications
            for alert in alerts:
                if prefs["alerts"].get(alert):
                    send_message(
                        chat_id,
                        f"⚠️ *{alert.replace('_', ' ')}*\n"
                        f"Regime: {current_regime}\n"
                        f"Confidence: {confidence:.2f}"
                    )

            # B. regime-entry notifications
            if prefs["regime_notify"].get(current_regime):
                send_message(
                    chat_id,
                    f"📊 *Market entered {current_regime}*\n"
                    f"Confidence: {confidence:.2f}"
            )

if __name__ == "__main__":
    run_worker()
