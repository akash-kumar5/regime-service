import sys
import os
# Adds the project root (one level up) to the top of sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
import pandas as pd
from core.compute_features import build_features

def build_lstm_input(
    merged_ohlcv_df: pd.DataFrame,
    feature_names: list,
    time_steps: int
) -> np.ndarray:
    """
    Returns np.ndarray of shape (time_steps, n_features)
    """

    # Compute features using SAME logic as training
    features_df = build_features(
        merged_ohlcv_df,
        main_tf="5m",
        context_tfs=["15m"],
        dropna=True
    )

    if len(features_df) < time_steps:
        raise ValueError(
            f"Not enough rows after feature engineering. "
            f"Need {time_steps}, got {len(features_df)}"
        )

    # Select last N rows
    window = features_df.iloc[-time_steps:]

    # Select & order columns EXACTLY as metadata
    X = window[feature_names].to_numpy(dtype=np.float32)

    return X
