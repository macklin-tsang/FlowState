"""
Wrapper for SQLAlchemy as a persistent helper which aids in saving, loading and
session management.
"""

from typing import Optional, Dict, Any, List
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
            temperature=state.get("temperature", 20.0),
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
            "temperature": row.temperature,
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
                "temperature": r.temperature,
            }
            for r in rows
        ]
    finally:
        session.close()



def get_history(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Return paginated sim_state rows (newest first) for playback."""
    session = get_session()
    try:
        rows = (
            session.query(SimState)
            .order_by(SimState.tick_id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            {
                "tick_id": r.tick_id,
                "timestamp": r.timestamp.isoformat(),
                "water_height": r.water_height,
                "flow_rate": r.flow_rate,
                "turbulence": r.turbulence,
                "erosion": r.erosion,
                "sediment": r.sediment,
                "raw_time": r.raw_time,
                "elapsed_time": r.elapsed_time,
                "temperature": r.temperature,
            }
            for r in reversed(rows)  # return in chronological order
        ]
    finally:
        session.close()


def get_drift_log(limit: int = 200) -> List[Dict[str, Any]]:
    """
    Return recent ticks with their ML corrections joined together,
    useful for visualising how drift evolves over time.
    """
    session = get_session()
    try:
        rows = (
            session.query(SimState, MLHistory)
            .join(MLHistory, SimState.tick_id == MLHistory.tick_id)
            .order_by(SimState.tick_id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "tick_id": s.tick_id,
                "elapsed_time": s.elapsed_time,
                "raw_time": s.raw_time,
                "corrected_time": m.corrected_time,
                "drift": s.raw_time - s.elapsed_time,
                "correction_error": m.corrected_time - s.elapsed_time,
                "temperature": s.temperature,
            }
            for s, m in reversed(rows)
        ]
    finally:
        session.close()


def count_ticks() -> int:
    """Return total number of sim_state rows."""
    session = get_session()
    try:
        return session.query(SimState).count()
    finally:
        session.close()


def clear_all_data() -> None:
    """Delete all rows from ml_history and sim_state (in FK order)."""
    session = get_session()
    try:
        session.query(MLHistory).delete()
        session.query(SimState).delete()
        session.commit()
    finally:
        session.close()