import json
import time
from pathlib import Path
from typing import Dict, Any

STATE_FILE = Path("latest_state.json")

def update_state(state: Dict[str, Any]):
    payload = {
        **state,
        "timestamp": int(time.time())
    }
    with STATE_FILE.open("w") as f:
        json.dump(payload, f)

def get_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {
            "timestamp": None,
            "symbol": "BTCUSDT",
            "current_regime": None,
            "confidence": None,
            "probabilities": None,
        }
    with STATE_FILE.open("r") as f:
        return json.load(f)
