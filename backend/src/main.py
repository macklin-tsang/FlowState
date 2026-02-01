"""
Main entry point for FlowState backend.

Modes:
    python main.py serve          → start API server (simulation loop runs automatically)
    python main.py demo [N]       → run N ticks with formatted output (default 30)
    python main.py train [N]      → generate N ticks + train ML model (default 500)
"""

import sys
import os

# ---------- ANSI formatting helpers (no external deps) ----------------------

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[37m"

BAR_WIDTH = 30  # characters for the water-level progress bar


def _bar(fraction: float, width: int = BAR_WIDTH) -> str:
    """Render a simple ASCII progress bar."""
    filled = int(fraction * width)
    filled = max(0, min(filled, width))
    return f"{CYAN}{'█' * filled}{DIM}{'░' * (width - filled)}{RESET}"


def _header():
    print()
    print(f"{BOLD}{'─' * 78}{RESET}")
    print(f"{BOLD}{CYAN}  ⏳  FlowState Water Clock Simulator{RESET}")
    print(f"{BOLD}{'─' * 78}{RESET}")
    print()


def _tick_line(tick_id, state, ml, sim_obj=None):
    """Print one richly-formatted tick line."""
    raw = state["raw_time"]
    corrected = ml["corrected_time"]
    elapsed = state.get("elapsed_time", 0)
    drift = raw - elapsed
    correction_err = corrected - elapsed
    temp = state.get("temperature", 20.0)

    # Water level bar (fraction of 0.375 m max basin height)
    frac = min(state["water_height"] / 0.375, 1.0)
    bar = _bar(frac)

    # Drift direction indicator
    if abs(drift) < 0.5:
        drift_color = GREEN
        drift_icon = "~"
    elif drift > 0:
        drift_color = YELLOW
        drift_icon = "+"
    else:
        drift_color = RED
        drift_icon = "-"

    print(
        f"  {DIM}tick{RESET} {WHITE}{tick_id:>5d}{RESET}  "
        f"{bar}  "
        f"{DIM}raw{RESET} {YELLOW}{raw:>8.1f}s{RESET}  "
        f"{DIM}corrected{RESET} {GREEN}{corrected:>8.1f}s{RESET}  "
        f"{DIM}true{RESET} {CYAN}{elapsed:>8.1f}s{RESET}  "
        f"{drift_color}{drift_icon}{abs(drift):>5.1f}s{RESET}  "
        f"{DIM}{temp:>5.1f}°C{RESET}"
    )


def _summary(sim_obj, total_ticks, ml_result):
    """Print a summary block after the run."""
    state = sim_obj.state
    raw = state["raw_time"]
    corrected = ml_result["corrected_time"]
    elapsed = state["elapsed_time"]

    print()
    print(f"{BOLD}{'─' * 78}{RESET}")
    print(f"  {BOLD}Summary after {total_ticks} ticks:{RESET}")
    print()
    print(f"    {DIM}Elapsed (true):{RESET}   {CYAN}{elapsed:.2f} s{RESET}")
    print(f"    {DIM}Raw clock time:{RESET}   {YELLOW}{raw:.2f} s{RESET}   "
          f"({YELLOW}drift: {raw - elapsed:+.2f} s{RESET})")
    print(f"    {DIM}ML corrected:{RESET}     {GREEN}{corrected:.2f} s{RESET}   "
          f"({GREEN}error: {corrected - elapsed:+.2f} s{RESET})")
    print(f"    {DIM}Temperature:{RESET}      {state['temperature']:.2f} °C")
    print(f"    {DIM}Basin height:{RESET}     {state['water_height']:.6f} m")
    print(f"    {DIM}Erosion:{RESET}          {state['erosion']:.2e} m")
    print(f"    {DIM}Sediment:{RESET}         {state['sediment']:.2e} m")
    print(f"{BOLD}{'─' * 78}{RESET}")
    print()


# ---------- modes ------------------------------------------------------------

def run_demo(ticks: int = 30, dt: float = 1.0):
    """Run a simulation with pretty-printed output and DB persistence."""
    from simulator.physics import WaterClockSimulator
    from ml.predictor import predict_corrected_time
    from db.storage import save_tick, save_ml_result

    sim = WaterClockSimulator()
    _header()

    print(f"  {DIM}Running {ticks} ticks (dt={dt}s){RESET}")
    print()
    print(
        f"  {DIM}{'tick':>9s}  {'basin level':<{BAR_WIDTH+2}s}  "
        f"{'raw':>10s}  {'corrected':>13s}  {'true':>10s}  "
        f"{'drift':>7s}  {'temp':>6s}{RESET}"
    )
    print(f"  {DIM}{'─' * 72}{RESET}")

    ml_result = None
    for i in range(1, ticks + 1):
        state = sim.step(dt)
        tick_id = save_tick(state)

        ml_result = predict_corrected_time(state)
        save_ml_result(tick_id, **ml_result)

        _tick_line(tick_id, state, ml_result, sim)

    if ml_result:
        _summary(sim, ticks, ml_result)

    print(f"  {GREEN}All {ticks} ticks persisted to the flowstate database.{RESET}")
    print()


def run_train(n_generate: int = 500):
    """Generate training data, then train and save the ML model."""
    from ml.train import generate_training_data, load_training_data, train_model, save_model

    _header()
    print(f"  {BOLD}Mode: TRAIN{RESET}")
    print()

    if n_generate > 0:
        generate_training_data(n_ticks=n_generate)

    X, y = load_training_data()
    pipe = train_model(X, y)
    save_model(pipe)

    print()
    print(f"  {GREEN}Model ready — the predictor will use it on next server start.{RESET}")
    print()


def run_server():
    """Start the FastAPI server via uvicorn."""
    import uvicorn

    _header()
    print(f"  {BOLD}Mode: SERVE{RESET}")
    print(f"  {DIM}The simulation loop runs automatically in the background.{RESET}")
    print(f"  {DIM}ML model auto-retrains every 200 ticks.{RESET}")
    print()

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


# ---------- entry point ------------------------------------------------------

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if mode == "demo":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        run_demo(ticks=n)
    elif mode == "train":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 500
        run_train(n_generate=n)
    else:
        run_server()
