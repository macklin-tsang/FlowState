"""
Main entry point for FlowState backend.

Can be run in two modes:
    1. `python main.py serve`   – start the FastAPI server (default)
    2. `python main.py demo`    – run a quick 20-tick simulation loop
                                  that prints state and saves to the DB

The demo mode is useful for verifying the DB connection and seeing
the simulator output without needing to call the API.
"""

import sys
import time


def run_demo(ticks: int = 20, dt: float = 1.0):
    """Run a short simulation, printing and persisting each tick."""
    from simulator.physics import WaterClockSimulator
    from ml.predictor import predict_corrected_time
    from db.storage import save_tick, save_ml_result

    sim = WaterClockSimulator()
    print(f"Running {ticks} ticks (dt={dt}s) …\n")

    for i in range(1, ticks + 1):
        state = sim.step(dt)
        tick_id = save_tick(state)

        ml = predict_corrected_time(state)
        save_ml_result(tick_id, **ml)

        print(
            f"tick {tick_id:>4d} | "
            f"height={state['water_height']:.6f} m | "
            f"flow={state['flow_rate']:.8f} m³/s | "
            f"raw_time={state['raw_time']:.2f} s | "
            f"corrected={ml['corrected_time']:.2f} s"
        )

    print("\nDone — all ticks persisted to the flowstate database.")


def run_server():
    """Start the FastAPI server via uvicorn."""
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


def run_train(n_generate: int = 500):
    """Generate training data, then train and save the ML model."""
    from ml.train import generate_training_data, load_training_data, train_model, save_model

    if n_generate > 0:
        generate_training_data(n_ticks=n_generate)

    X, y = load_training_data()
    pipe = train_model(X, y)
    save_model(pipe)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if mode == "demo":
        run_demo()
    elif mode == "train":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 500
        run_train(n_generate=n)
    else:
        run_server()