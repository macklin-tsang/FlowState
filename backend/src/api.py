"""
FastAPI application for the FlowState water clock.

Endpoints
---------
GET  /state                → latest simulator state + ML correction
POST /advance?dt=1.0       → manually advance simulation by dt seconds
POST /train?n_ticks=500    → generate data, train ML model, hot-reload
POST /reload-model         → reload ML model from disk
GET  /health               → liveness check
GET  /params               → current tunable simulator parameters
POST /params               → update simulator parameters at runtime
GET  /history?limit=100    → paginated historical sim states
GET  /drift?limit=200      → drift log (raw vs corrected vs true)
GET  /stats                → summary statistics of the simulation run

Phase 5: A background task runs the simulation continuously at 1 tick/s,
persists every tick, and auto-retrains the ML model every RETRAIN_INTERVAL
ticks.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from db.storage import (
    get_latest_state, save_tick, save_ml_result,
    get_history, get_drift_log, count_ticks,
)
from simulator.physics import WaterClockSimulator
from ml.predictor import predict_corrected_time, reload_model

# ----- configuration -------------------------------------------------------

TICK_DT = 1.0             # seconds per simulation tick
TICK_INTERVAL = 1.0       # real seconds between ticks (wall-clock pace)
RETRAIN_INTERVAL = 200    # retrain ML model every N ticks

# ----- shared state ---------------------------------------------------------

sim = WaterClockSimulator()
_loop_running = False
_ticks_since_retrain = 0


async def simulation_loop():
    """
    Phase 5 continuous loop: step → predict → persist → serve.

    Runs as a background asyncio task inside the uvicorn event loop.
    Auto-retrains the ML model every RETRAIN_INTERVAL ticks.
    """
    global _loop_running, _ticks_since_retrain
    _loop_running = True

    while _loop_running:
        # Step the simulation
        state = sim.step(TICK_DT)
        tick_id = save_tick(state)

        # ML prediction
        ml = predict_corrected_time(state)
        save_ml_result(tick_id, **ml)

        _ticks_since_retrain += 1

        # Phase 6: online retraining
        if _ticks_since_retrain >= RETRAIN_INTERVAL:
            await _retrain_model()
            _ticks_since_retrain = 0

        await asyncio.sleep(TICK_INTERVAL)


async def _retrain_model():
    """Run ML training in a thread so we don't block the event loop."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _retrain_sync)


def _retrain_sync():
    """Synchronous retraining — called from executor."""
    from ml.train import load_training_data, train_model, save_model
    try:
        X, y = load_training_data()
        pipe = train_model(X, y)
        save_model(pipe)
        reload_model()
        print("[Auto-retrain] Model updated successfully.")
    except Exception as e:
        print(f"[Auto-retrain] Failed: {e}")


# ----- lifespan (start/stop background loop) --------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the simulation loop on server boot, cancel on shutdown."""
    task = asyncio.create_task(simulation_loop())
    yield
    global _loop_running
    _loop_running = False
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ----- app ------------------------------------------------------------------

app = FastAPI(title="FlowState API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- endpoints ------------------------------------------------------------

@app.get("/state")
def state():
    """
    Return the latest persisted simulator state together with the
    most recent ML correction.
    """
    db_state = get_latest_state()
    if db_state is None:
        current = sim.state
        ml = predict_corrected_time(current)
        return {**current, "corrected_time": ml["corrected_time"]}

    ml = predict_corrected_time(db_state)
    return {**db_state, "corrected_time": ml["corrected_time"]}


@app.post("/advance")
def advance(dt: float = Query(default=1.0, gt=0, le=60)):
    """Manually advance the simulation by dt seconds (on top of the loop)."""
    new_state = sim.step(dt)
    tick_id = save_tick(new_state)

    ml = predict_corrected_time(new_state)
    save_ml_result(tick_id, **ml)

    return {**new_state, "tick_id": tick_id, "corrected_time": ml["corrected_time"]}


@app.post("/train")
def train(n_ticks: int = Query(default=500, ge=10, le=10000)):
    """Generate training data, train the ML model, hot-reload."""
    from ml.train import generate_training_data, load_training_data, train_model, save_model

    generate_training_data(n_ticks=n_ticks)
    X, y = load_training_data()
    pipe = train_model(X, y)
    save_model(pipe)
    reload_model()

    return {"status": "trained", "n_ticks": n_ticks}


@app.post("/reset")
def reset_sim():
    """Reset the simulator to initial conditions so the demo can be re-run."""
    global _ticks_since_retrain
    sim.reset()
    _ticks_since_retrain = 0
    return {"status": "reset", "state": sim.state}


@app.post("/reload-model")
def reload():
    """Reload the ML model from disk without retraining."""
    reload_model()
    return {"status": "reloaded"}


@app.get("/params")
def get_params():
    """Return current tunable simulator parameters."""
    return sim.get_params()


@app.post("/params")
def set_params(
    erosion_rate: float = Query(default=None, ge=0),
    sediment_rate: float = Query(default=None, ge=0),
    turbulence_sigma: float = Query(default=None, ge=0, le=1),
    temp_drift_rate: float = Query(default=None),
    discharge_coeff: float = Query(default=None, ge=0.1, le=1.0),
):
    """
    Update simulator parameters at runtime.  Only provided values
    are changed — omitted parameters keep their current value.
    Useful for a frontend dropdown/slider control panel.
    """
    updates = {}
    if erosion_rate is not None:
        updates["erosion_rate"] = erosion_rate
    if sediment_rate is not None:
        updates["sediment_rate"] = sediment_rate
    if turbulence_sigma is not None:
        updates["turbulence_sigma"] = turbulence_sigma
    if temp_drift_rate is not None:
        updates["temp_drift_rate"] = temp_drift_rate
    if discharge_coeff is not None:
        updates["discharge_coeff"] = discharge_coeff

    sim.set_params(**updates)
    return {"status": "updated", "params": sim.get_params()}


@app.get("/history")
def history(
    limit: int = Query(default=100, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
):
    """Paginated historical sim states (chronological order)."""
    rows = get_history(limit=limit, offset=offset)
    return {"count": len(rows), "ticks": rows}


@app.get("/drift")
def drift(limit: int = Query(default=200, ge=1, le=5000)):
    """
    Drift log — for each tick returns raw_time, corrected_time,
    elapsed_time, and the computed drift / correction error.
    Useful for charting how the clock drifts over time.
    """
    rows = get_drift_log(limit=limit)
    return {"count": len(rows), "drift": rows}


@app.get("/stats")
def stats():
    """High-level simulation statistics."""
    total = count_ticks()
    latest = get_latest_state()
    return {
        "total_ticks": total,
        "latest": latest,
        "loop_running": _loop_running,
        "retrain_interval": RETRAIN_INTERVAL,
        "ticks_until_retrain": RETRAIN_INTERVAL - _ticks_since_retrain,
    }


@app.get("/health")
def health():
    """Liveness probe."""
    return {"status": "ok"}
