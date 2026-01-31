"""
SQLAlchemy ORM models that mirror the tables in migrations/schema.sql.

SimState  – one row per simulation tick (physics outputs).
MLHistory – one row per ML correction (linked to the same tick).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from .connection import Base


class SimState(Base):
    """Stores the physics simulator output for a single tick."""

    __tablename__ = "sim_state"

    tick_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    water_height = Column(Float, nullable=False)
    flow_rate = Column(Float, nullable=False)
    turbulence = Column(Float, nullable=False)
    erosion = Column(Float, nullable=False)
    sediment = Column(Float, nullable=False)
    raw_time = Column(Float, nullable=False)


class MLHistory(Base):
    """Stores ML-corrected time with raw simulator time."""

    __tablename__ = "ml_history"

    tick_id = Column(Integer, ForeignKey("sim_state.tick_id"), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    raw_time = Column(Float, nullable=False)
    corrected_time = Column(Float, nullable=False)
    system_time = Column(Float, nullable=False)
    error = Column(Float, nullable=False)
