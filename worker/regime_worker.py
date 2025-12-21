# worker/regime_worker.py
import sys
import os

# Adds the project root (one level up) to the top of sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import random
from core.state import update_state

REGIMES = [
    "STRONG_UPTREND",
    "WEAK_UPTREND",
    "RANGE",
    "SQUEEZE",
    "WEAK_DOWNTREND",
    "STRONG_DOWNTREND"
]

def run_worker():
    print("Regime worker started...")
    while True:
        regime = random.choice(REGIMES)
        probs = {r: round(random.random(), 3) for r in REGIMES}

        total = sum(probs.values())
        probs = {k: v / total for k, v in probs.items()}

        state = {
            "symbol": "BTCUSDT",
            "current_regime": regime,
            "confidence": probs[regime],
            "probabilities": probs
        }

        update_state(state)
        # print("Updated state:", state)

        time.sleep(5)  # simulate 5 min later

if __name__ == "__main__":
    run_worker()
