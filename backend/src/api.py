"""
FastAPI application for the FlowState water clock.

Endpoints
---------
GET  /state           → latest simulator state + ML correction as JSON
POST /advance?dt=1.0  → advance the simulation by dt seconds, return new state
GET  /health          → simple liveness check
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from db.storage import get_latest_state, save_tick, save_ml_result
from simulator.physics import WaterClockSimulator
from ml.predictor import predict_corrected_time

app = FastAPI(title="FlowState API", version="0.1.0")

# Allow the frontend (any origin during dev) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# A single shared simulator instance lives in the API process.
sim = WaterClockSimulator()


@app.get("/state")
def state():
    """
    Return latest persisted sim state + most recent ML correction.  
    If no ticks, return sim's initial (in-memory) state.
    """
    db_state = get_latest_state()
    if db_state is None:
        # Nothing in DB yet — return live in-memory state with stub ML
        current = sim.state
        ml = predict_corrected_time(current)
        return {**current, "corrected_time": ml["corrected_time"]}

    ml = predict_corrected_time(db_state)
    return {**db_state, "corrected_time": ml["corrected_time"]}


@app.post("/advance")
def advance(dt: float = Query(default=1.0, gt=0, le=60)):
    """
    Advance the simulation by *dt* seconds, persist new state,
    run ML correction stub, and return everything as JSON.
    """
    new_state = sim.step(dt)
    tick_id = save_tick(new_state)

    ml = predict_corrected_time(new_state)
    save_ml_result(tick_id, **ml)

    return {**new_state, "tick_id": tick_id, "corrected_time": ml["corrected_time"]}

@app.get("/health")
def health():
    """Liveness probe."""
    return {"status": "ok"}