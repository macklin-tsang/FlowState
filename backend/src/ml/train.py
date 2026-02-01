"""
Train the ML time-correction model.

Pulls all sim_state rows from the database, trains a scikit-learn
pipeline to predict true elapsed_time from the simulator's noisy
features, and saves the model to disk as a .joblib file.

Usage:
    cd backend/src
    python -m ml.train              # train using DB data
    python -m ml.train --generate N # generate N fresh ticks first, then train

The trained model is saved to  ml/model.joblib  and automatically
picked up by ml/predictor.py on the next import / server restart.
"""

import argparse
import os
import sys
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Features the model uses to predict elapsed_time.
FEATURE_COLS = ["raw_time", "water_height", "flow_rate", "turbulence", "erosion", "sediment"]
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")


def generate_training_data(n_ticks: int = 500, dt: float = 1.0):
    """Run the simulator for n_ticks and persist every tick to the DB."""
    from simulator.physics import WaterClockSimulator
    from db.storage import save_tick

    sim = WaterClockSimulator()
    print(f"Generating {n_ticks} training ticks (dt={dt}s) ...")
    for _ in range(n_ticks):
        state = sim.step(dt)
        save_tick(state)
    print(f"Done — {n_ticks} ticks saved to the database.")


def load_training_data():
    """Pull all sim_state rows from the DB and return feature/target arrays."""
    from db.storage import get_all_states

    rows = get_all_states()
    if len(rows) < 10:
        print(f"Only {len(rows)} rows in DB — need at least 10 to train.")
        print("Run with --generate 500 to create training data first.")
        sys.exit(1)

    X = np.array([[r[c] for c in FEATURE_COLS] for r in rows])
    y = np.array([r["elapsed_time"] for r in rows])

    print(f"Loaded {len(rows)} rows from sim_state.")
    return X, y


def train_model(X, y):
    """
    Fit a Ridge regression pipeline and return it along with test metrics.

    Pipeline:
        1. StandardScaler — normalise each feature to zero-mean unit-variance
        2. Ridge          — L2-regularised linear regression (robust, fast)

    Ridge is a good starting point because the relationship between
    raw_time and elapsed_time is nearly linear (the drift is small).
    A more complex model (SVR, gradient boosting) can be swapped in
    later without changing the rest of the code.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=1.0)),
    ])
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"Test MAE:  {mae:.6f} seconds")
    print(f"Test R²:   {r2:.8f}")

    return pipe


def save_model(pipe):
    """Persist the trained pipeline to disk."""
    joblib.dump(pipe, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Train the FlowState ML model")
    parser.add_argument(
        "--generate", type=int, default=0, metavar="N",
        help="Generate N fresh simulation ticks before training",
    )
    args = parser.parse_args()

    if args.generate > 0:
        generate_training_data(n_ticks=args.generate)

    X, y = load_training_data()
    pipe = train_model(X, y)
    save_model(pipe)
    print("\nThe predictor will use this model on the next server restart.")


if __name__ == "__main__":
    main()
