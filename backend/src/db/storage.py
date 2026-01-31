"""
Wrapper for SQLAlchemy as a persistent helper which aids in saving, loading and
session management.
"""

from typing import Optional, Dict, Any
from .connection import get_session
from .models import SimState, MLHistory

def save_tick(state: Dict[str, float]) -> int:
    """
    Storage for one sim tick to the sim_state table.

    Parameters
    ----------
    state : dict
        Must contain necessary keys: water_height, flow_rate, turbulence,
        erosion, sediment, raw_time.

    Returns
    -------
    int
        The auto-generated tick_id for this row.
    """

    session = get_session()

    try:
        row = SimState(
            water_height=state["water_height"],
            flow_rate=state["flow_rate"],
            turbulence=state["turbulence"],
            erosion=state["erosion"],
            sediment=state["sediment"],
            raw_time=state["raw_time"],
            elapsed_time=state.get("elapsed_time", 0),
        )

        session.add(row)
        session.commit()
        tick_id = row.tick_id
        
        return tick_id

    finally:
        session.close()

def save_ml_result(tick_id: int, raw_time: float, corrected_time: float,
                   system_time: float, error: float) -> None:
    """
    Storing one ML correction to the ml_history table.

    Parameters
    ----------
    tick_id        : matching sim_state tick
    raw_time       : uncorrected time from the simulator
    corrected_time : ML-corrected time
    system_time    : wall-clock reference time
    error          : corrected_time − system_time
    """

    session = get_session()

    try:
        row = MLHistory(
            tick_id=tick_id,
            raw_time=raw_time,
            corrected_time=corrected_time,
            system_time=system_time,
            error=error,
        )

        session.add(row)

        session.commit()
    finally:
        session.close()

def get_latest_state() -> Optional[Dict[str, Any]]:
    """
    Returns most recent sim_state row as plain dict, or None if
    the table is empty.
    """
    session = get_session()

    try:
        row = (
            session.query(SimState)
            .order_by(SimState.tick_id.desc())
            .first()
        )

        if row is None:
            return None

        return {
            "tick_id": row.tick_id,
            "timestamp": row.timestamp.isoformat(),
            "water_height": row.water_height,
            "flow_rate": row.flow_rate,
            "turbulence": row.turbulence,
            "erosion": row.erosion,
            "sediment": row.sediment,
            "raw_time": row.raw_time,
            "elapsed_time": row.elapsed_time,
        }

    finally:
        session.close()


def get_all_states():
    """Return all sim_state rows as a list of dicts (for ML training)."""
    session = get_session()
    try:
        rows = session.query(SimState).order_by(SimState.tick_id).all()
        return [
            {
                "tick_id": r.tick_id,
                "water_height": r.water_height,
                "flow_rate": r.flow_rate,
                "turbulence": r.turbulence,
                "erosion": r.erosion,
                "sediment": r.sediment,
                "raw_time": r.raw_time,
                "elapsed_time": r.elapsed_time,
            }
            for r in rows
        ]
    finally:
        session.close()


def get_latest_ml() -> Optional[Dict[str, Any]]:
    """
    Return the most recent ml_history row as a plain dict, or None.
    """

    session = get_session()

    try:
        row = (
            session.query(MLHistory)
            .order_by(MLHistory.tick_id.desc())
            .first()
        )

        if row is None:
            return None

        return {
            "tick_id": row.tick_id,
            "timestamp": row.timestamp.isoformat(),
            "raw_time": row.raw_time,
            "corrected_time": row.corrected_time,
            "system_time": row.system_time,
            "error": row.error,
        }

    finally:
        session.close()