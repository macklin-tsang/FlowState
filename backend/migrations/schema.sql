-- FlowState database schema
-- Run once against the 'flowstate' PostgreSQL database.

CREATE TABLE IF NOT EXISTS sim_state (
    tick_id      SERIAL PRIMARY KEY,
    timestamp    TIMESTAMP NOT NULL DEFAULT now(),
    water_height DOUBLE PRECISION NOT NULL,
    flow_rate    DOUBLE PRECISION NOT NULL,
    turbulence   DOUBLE PRECISION NOT NULL,
    erosion      DOUBLE PRECISION NOT NULL,
    sediment     DOUBLE PRECISION NOT NULL,
    raw_time     DOUBLE PRECISION NOT NULL,
    elapsed_time DOUBLE PRECISION NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ml_history (
    tick_id        INTEGER PRIMARY KEY REFERENCES sim_state(tick_id),
    timestamp      TIMESTAMP NOT NULL DEFAULT now(),
    raw_time       DOUBLE PRECISION NOT NULL,
    corrected_time DOUBLE PRECISION NOT NULL,
    system_time    DOUBLE PRECISION NOT NULL,
    error          DOUBLE PRECISION NOT NULL
);
