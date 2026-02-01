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
    - Water temperature affecting viscosity and therefore flow
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

# Temperature model — water viscosity changes with temperature which
# scales the discharge coefficient.  At 20 C the factor is 1.0.
TEMP_INIT = 20.0            # starting water temperature (Celsius)
TEMP_DRIFT_RATE = 0.002     # degrees per tick of slow ambient drift
TEMP_NOISE_SIGMA = 0.05     # random fluctuation per tick (degrees)
TEMP_REFERENCE = 20.0       # reference temperature for viscosity=1.0
TEMP_VISCOSITY_COEFF = -0.02  # each +1 C reduces viscosity ~2% → faster flow

# Default tuning ranges used by the /params endpoint.
PARAM_DEFAULTS = {
    "erosion_rate": EROSION_RATE,
    "sediment_rate": SEDIMENT_RATE,
    "turbulence_sigma": TURBULENCE_SIGMA,
    "temp_drift_rate": TEMP_DRIFT_RATE,
    "discharge_coeff": DISCHARGE_COEFF,
}


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
        self.h_upper: float = UPPER_HEIGHT_INIT
        self.h_basin: float = 0.0
        self.nozzle_radius: float = NOZZLE_RADIUS_INIT
        self.cumulative_erosion: float = 0.0
        self.cumulative_sediment: float = 0.0
        self.tick: int = 0
        self.elapsed: float = 0.0
        self.temperature: float = TEMP_INIT

        # Tunable parameters (can be changed at runtime via API)
        self.erosion_rate: float = EROSION_RATE
        self.sediment_rate: float = SEDIMENT_RATE
        self.turbulence_sigma: float = TURBULENCE_SIGMA
        self.temp_drift_rate: float = TEMP_DRIFT_RATE
        self.discharge_coeff: float = DISCHARGE_COEFF

        # Cache latest computed values for the API
        self._flow_rate: float = 0.0
        self._turbulence: float = 0.0

    # ---- runtime parameter tuning --------------------------------------

    def set_params(self, **kwargs):
        """
        Update tunable simulation parameters at runtime.

        Accepted keys: erosion_rate, sediment_rate, turbulence_sigma,
        temp_drift_rate, discharge_coeff.
        """
        for key, value in kwargs.items():
            if hasattr(self, key) and key in PARAM_DEFAULTS:
                setattr(self, key, float(value))

    def get_params(self) -> dict:
        """Return current tunable parameters."""
        return {k: getattr(self, k) for k in PARAM_DEFAULTS}

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
            erosion, sediment, raw_time, elapsed_time, temperature.
        """
        self.tick += 1
        self.elapsed += dt

        # --- temperature drift ------------------------------------------
        self.temperature += self.temp_drift_rate * dt
        self.temperature += self.rng.normal(0, TEMP_NOISE_SIGMA)
        self.temperature = max(self.temperature, 0.5)  # don't freeze

        # Viscosity factor: warmer → less viscous → faster flow
        temp_factor = 1.0 + TEMP_VISCOSITY_COEFF * (self.temperature - TEMP_REFERENCE)
        temp_factor = max(temp_factor, 0.5)  # clamp to reasonable range

        # --- nozzle degradation -----------------------------------------
        self.cumulative_erosion += self.erosion_rate * dt
        self.cumulative_sediment += self.sediment_rate * dt
        effective_radius = max(
            self.nozzle_radius + self.cumulative_erosion - self.cumulative_sediment,
            1e-6,
        )
        nozzle_area = np.pi * effective_radius ** 2

        # --- Torricelli outflow from upper vessel -----------------------
        if self.h_upper > 0:
            v_out = np.sqrt(2 * GRAVITY * self.h_upper)
            ideal_flow = self.discharge_coeff * nozzle_area * v_out * temp_factor

            # stochastic turbulence (multiplicative noise)
            noise = self.rng.normal(loc=1.0, scale=self.turbulence_sigma)
            noise = max(noise, 0.0)
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
            "temperature": round(self.temperature, 3),
        }

    @property
    def is_empty(self) -> bool:
        """True when the upper vessel has fully drained."""
        return self.h_upper <= 0.0
