"""
ML time-correction predictor.

On import, tries to load a trained model from ml/model.joblib.
If the file exists, predict_corrected_time() uses the model.
If not, it falls back to the identity stub (corrected = raw).

Reloading:  call reload_model() after training a new model,
or restart the API server.
"""

import os
import time
from typing import Dict, Any

import numpy as np
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
FEATURE_COLS = ["raw_time", "water_height", "flow_rate", "turbulence", "erosion", "sediment"]

# Module-level model reference — loaded once on import.
_model = None


def reload_model():
    """Load (or reload) the trained model from disk."""
    global _model
    if os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
        print(f"[ML] Loaded model from {MODEL_PATH}")
    else:
        _model = None


# Attempt to load on first import.
reload_model()


def predict_corrected_time(sim_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given a simulator state dict, return an ML correction dict.

    If a trained model is available, it predicts the true elapsed time
    from the simulator features.  Otherwise falls back to raw_time.

    Parameters
    ----------
    sim_state : dict
        Must contain keys: raw_time, water_height, flow_rate,
        turbulence, erosion, sediment.

    Returns
    -------
    dict
        Keys: raw_time, corrected_time, system_time, error.
    """
    raw = sim_state["raw_time"]
    system = time.time()

    if _model is not None:
        features = np.array([[sim_state.get(c, 0) for c in FEATURE_COLS]])
        corrected = float(_model.predict(features)[0])
    else:
        # Fallback: no model trained yet — identity correction.
        corrected = raw

    return {
        "raw_time": raw,
        "corrected_time": corrected,
        "system_time": system,
        "error": corrected - system,
    }
