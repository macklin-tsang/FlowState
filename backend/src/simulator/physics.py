"""
Water clock physics simulator.

Models a clepsydra (water clock) where water drains from an upper
vessel through a nozzle into a lower collection basin.  The water
height in the basin is the timekeeping signal.

Key physics modelled (simplified):
    - Torricelli outflow:  v = sqrt(2 * g * h_upper)
    - Nozzle flow rate with discharge coefficient
    - Turbulence as random fluctuation around laminar flow
    - Erosion that slowly widens the nozzle over many ticks
    - Sediment accumulation that partially clogs the nozzle
    - raw_time derived from collected water height in the basin

All state is held in a plain NumPy array so the simulator has zero
dependency on the database or API layers.
"""

import numpy as np

# ----- Physical constants & tuning knobs --------------------------------

GRAVITY = 9.81              # m/s^2
NOZZLE_RADIUS_INIT = 0.003  # 3 mm starting nozzle radius (m)
DISCHARGE_COEFF = 0.61      # typical sharp-edged orifice
UPPER_VESSEL_AREA = 0.01    # cross-section of upper vessel (m^2)
BASIN_AREA = 0.008          # cross-section of collection basin (m^2)
UPPER_HEIGHT_INIT = 0.30    # starting water level in upper vessel (m)
EROSION_RATE = 1e-9         # nozzle radius growth per tick (m)
SEDIMENT_RATE = 5e-10       # effective radius reduction per tick (m)
TURBULENCE_SIGMA = 0.02     # std-dev of flow noise (fraction of flow)
TIME_PER_UNIT_HEIGHT = 3600 # seconds of "clock time" per metre of basin height


class WaterClockSimulator:
    """
    Deterministic + stochastic water clock simulation.

    Call `step(dt)` to advance the simulation by `dt` seconds of
    real-world time.  Read the `.state` property to get the current
    physics outputs as a plain dict (ready for DB storage or API).
    """

    def __init__(self, seed: int = 42):
        """
        Initialise the simulator to its starting conditions.

        Parameters
        ----------
        seed : int
            NumPy random seed for reproducible turbulence noise.
        """
        self.rng = np.random.default_rng(seed)

        # Dynamic state
        self.h_upper: float = UPPER_HEIGHT_INIT   # water level in upper vessel
        self.h_basin: float = 0.0                  # water level in basin (our "clock hand")
        self.nozzle_radius: float = NOZZLE_RADIUS_INIT
        self.cumulative_erosion: float = 0.0
        self.cumulative_sediment: float = 0.0
        self.tick: int = 0
        self.elapsed: float = 0.0                  # real seconds elapsed

        # Cache latest computed values for the API
        self._flow_rate: float = 0.0
        self._turbulence: float = 0.0

    # ---- core integration step -----------------------------------------

    def step(self, dt: float = 1.0) -> dict:
        """
        Advance the simulation by dt seconds (Euler integration).

        Parameters
        ----------
        dt : float
            Time step in seconds.  Default is 1 s.

        Returns
        -------
        dict
            Snapshot with keys: water_height, flow_rate, turbulence,
            erosion, sediment, raw_time.
        """
        self.tick += 1
        self.elapsed += dt

        # --- nozzle degradation -----------------------------------------
        self.cumulative_erosion += EROSION_RATE * dt
        self.cumulative_sediment += SEDIMENT_RATE * dt
        effective_radius = max(
            self.nozzle_radius + self.cumulative_erosion - self.cumulative_sediment,
            1e-6,  # never fully clog
        )
        nozzle_area = np.pi * effective_radius ** 2

        # --- Torricelli outflow from upper vessel -----------------------
        if self.h_upper > 0:
            v_out = np.sqrt(2 * GRAVITY * self.h_upper)
            ideal_flow = DISCHARGE_COEFF * nozzle_area * v_out  # m^3/s

            # stochastic turbulence (multiplicative noise)
            noise = self.rng.normal(loc=1.0, scale=TURBULENCE_SIGMA)
            noise = max(noise, 0.0)  # flow can't reverse
            actual_flow = ideal_flow * noise
            self._turbulence = abs(noise - 1.0)
        else:
            actual_flow = 0.0
            self._turbulence = 0.0

        self._flow_rate = actual_flow

        # --- update water levels ----------------------------------------
        volume_transferred = actual_flow * dt
        dh_upper = volume_transferred / UPPER_VESSEL_AREA
        self.h_upper = max(self.h_upper - dh_upper, 0.0)
        self.h_basin += volume_transferred / BASIN_AREA

        return self.state

    # ---- read-only accessors -------------------------------------------

    @property
    def state(self) -> dict:
        """Return the current physics state as a plain dict."""
        return {
            "water_height": round(self.h_basin, 8),
            "flow_rate": round(self._flow_rate, 10),
            "turbulence": round(self._turbulence, 6),
            "erosion": round(self.cumulative_erosion, 12),
            "sediment": round(self.cumulative_sediment, 12),
            "raw_time": round(self.h_basin * TIME_PER_UNIT_HEIGHT, 4),
            "elapsed_time": round(self.elapsed, 4),
        }

    @property
    def is_empty(self) -> bool:
        """True when the upper vessel has fully drained."""
        return self.h_upper <= 0.0
