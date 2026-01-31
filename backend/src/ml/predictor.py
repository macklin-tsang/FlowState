"""
ML time-correction stub.

In Phase 3 a scikit-learn model will be trained on (raw_time, features)
→ system_time pairs collected from the sim_state and ml_history tables.
For now this module exposes the same interface but returns the raw_time
unchanged (identity correction).

Intended flow:
    1. Simulator produces raw_time each tick.
    2. This module corrects it → corrected_time.
    3. The API exposes both values so the frontend can visualise drift.
"""

import time
from typing import Dict, Any

# scikit-learn import kept here so it's clear this is the ML module;
# the actual model will be a Pipeline(StandardScaler, Ridge/SVR).
from sklearn.linear_model import Ridge  # noqa: F401 — used in Phase 3


def predict_corrected_time(sim_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given a simulator state dict, return an ML correction dict.

    Parameters
    ----------
    sim_state : dict
        Must contain at least 'raw_time'.

    Returns
    -------
    dict
        Keys: raw_time, corrected_time, system_time, error.
    """
    raw = sim_state["raw_time"]
    system = time.time()  # wall-clock reference

    # --- STUB: identity correction (no model loaded yet) ----------------
    corrected = raw

    return {
        "raw_time": raw,
        "corrected_time": corrected,
        "system_time": system,
        "error": corrected - system,
    }
