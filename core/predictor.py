# core/predictor.py
import json
import numpy as np
from pathlib import Path
import joblib
from tensorflow.keras.models import load_model

MODELS_DIR = Path("models")

MODEL_PATH = MODELS_DIR / "lstm_regime_model.keras"
SCALER_PATH = MODELS_DIR / "scaler.joblib"
META_PATH = MODELS_DIR / "lstm_model_metadata.json"

class RegimePredictor:
    def __init__(self):
        # Load model + scaler
        self.model = load_model(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)

        # Load metadata
        with open(META_PATH, "r") as f:
            self.meta = json.load(f)

        self.time_steps = self.meta["time_steps"]
        self.features = self.meta["features"]

        # Build index → regime mapping
        regime_map = self.meta["regime_map"]
        self.index_to_regime = {
            idx: name for name, idx in regime_map.items()
        }

        self.n_features = len(self.features)

        print(
            f"[Predictor] Loaded LSTM | "
            f"time_steps={self.time_steps}, "
            f"features={self.n_features}, "
            f"regimes={len(self.index_to_regime)}"
        )

    def predict(self, feature_sequence: np.ndarray):
        """
        feature_sequence shape: (time_steps, n_features)
        """
        if feature_sequence.shape != (self.time_steps, self.n_features):
            raise ValueError(
                f"Expected shape {(self.time_steps, self.n_features)}, "
                f"got {feature_sequence.shape}"
            )

        # Scale per timestep
        scaled = self.scaler.transform(feature_sequence)

        # Add batch dimension
        X = scaled[np.newaxis, :, :]  # (1, 64, 14)

        probs = self.model.predict(X, verbose=0)[0]

        prob_map = {
            self.index_to_regime[i]: float(probs[i])
            for i in range(len(probs))
        }
        
        prob_map = {k: round(v, 6) for k, v in prob_map.items()}

        current = max(prob_map, key=prob_map.get)

        return {
            "current_regime": current,
            "confidence": prob_map[current],
            "probabilities": prob_map,
        }


# Singleton instance (model loads ONCE)
predictor = RegimePredictor()
