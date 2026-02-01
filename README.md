# FlowState
*A Self Correcting Water Clock*

---

## Summary

Flowstate is a self-learning, live clepsydra (ancient water clock) that measures accuracy and calibrates the live clock.

Drawing inspiration from ancient technology, this project aims to provide clear visuals for simulation.
This will be done accounting for the water properties where the machine learning base will adapt and correct the perception of time.

## Structure

The project will function via a feedback loop:

Water Simulation -> Internal Clock -> ML-Powered Adjustments -> Corrected Water Simulation

## Technologies Used

Frontend:

Backend:
- **Python 3.11**: Base language for backend development
- **NumPy**: Arithmetic handling (ie. square root, random noise, floating-point arrays)
- **FastAPI**: Web framework to expose simulator state to frontend via JSON
- **Uvicorn**: Lightweight server that runs FastAPI and listens for HTTP requests
- **SQLAlchemy**: ORM (Object-Relational Mapper) that reads/writes  PostgreSQL database using Python objects instead of raw SQL
- **PostgreSQL**: Relational database where every simulation tick and every ML prediction is permanently stored
- **scikit-learn**: ML library that corrects the simulator drift against real wall-clock reference time
