# api/app.py
import sys
import os

# Adds the project root (one level up) to the top of sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi import FastAPI
from core.state import get_state

app = FastAPI(title="Crypto Regime Service")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/current-regime")
def current_regime():
    return get_state()

@app.get("/alerts")
def get_alerts():
    state = get_state()
    return {
        "timestamp": state.get("timestamp"),
        "alerts": state.get("alerts", [])
    }

