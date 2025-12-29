# worker/regime_worker.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from core.predictor import predictor
from core.state import update_state
from core.feature_engineering import build_lstm_input
from core.data_fetcher import fetch_klines, merge_timeframes
from tg.bot import load_settings
from tg.notifier import send_message

SYMBOL = "BTCUSDT"
SLEEP_SECONDS = 120

prev_regime = None

def run_worker():
    global prev_regime
    print("Regime worker started (LIVE BINANCE)")

    while True:
        try:
            # ---- fetch data
            df_5m = fetch_klines(SYMBOL, "5m", limit=300)
            df_15m = fetch_klines(SYMBOL, "15m", limit=300)
            merged = merge_timeframes(df_5m, df_15m)

            # ---- model
            X = build_lstm_input(
                merged_ohlcv_df=merged,
                feature_names=predictor.features,
                time_steps=predictor.time_steps
            )

            result = predictor.predict(X)
            current_regime = result["current_regime"]
            confidence = result["confidence"]

            alerts = []

            if (
                current_regime == "Strong Trend"
                and confidence >= 0.65
                and prev_regime != "Strong Trend"
            ):
                alerts.append("STRONG_TREND_CONFIRMED")

            if (
                current_regime == "Choppy High-Vol"
                and confidence >= 0.6
                and prev_regime != "Choppy High-Vol"
            ):
                alerts.append("CHOPPY_MARKET_WARNING")

            if (
                prev_regime is not None
                and current_regime != prev_regime
                and confidence >= 0.55
            ):
                alerts.append(f"REGIME_CHANGE {prev_regime} → {current_regime}")

            # ---- update state
            update_state({
                "symbol": SYMBOL,
                **result,
                "alerts": alerts
            })

            print("Updated state:", result)

            # ---- TELEGRAM NOTIFICATIONS (IMPORTANT PART)
            settings = load_settings()  # reload every loop

            for chat_id, prefs in settings.items():
                # alert-based
                for alert in alerts:
                    if prefs["alerts"].get(alert):
                        send_message(
                            chat_id,
                            f"⚠️ *{alert.replace('_', ' ')}*\n"
                            f"Regime: {current_regime}\n"
                            f"Confidence: {confidence:.2f}"
                        )

                # regime-entry
                if (
                    current_regime != prev_regime
                    and prefs["regime_notify"].get(current_regime)
                ):
                    send_message(
                        chat_id,
                        f"📊 *Market entered {current_regime}*\n"
                        f"Confidence: {confidence:.2f}"
                    )

            prev_regime = current_regime

        except Exception as e:
            print("Worker error:", e)

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    run_worker()
