"""
Module for database connection.

connection.py creates one SQLAlchemy engine + session factory that points to the local
PostgreSQL 'flowstate db where every other module imports 'get_session' from here
that communicates to the DB.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://macklin@localhost/flowstate")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_session():
    return SessionLocal()
