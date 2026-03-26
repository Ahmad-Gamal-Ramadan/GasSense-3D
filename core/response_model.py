from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class SimulationResult:
    time_s: np.ndarray
    gas_ppm: np.ndarray
    coverage: np.ndarray
    response: np.ndarray
    resistance_ohm: np.ndarray


class GasSensorResponseModel:
    @staticmethod
    def _gas_profile(
        time_s: np.ndarray,
        on_time: float,
        off_time: float,
        cycles: int,
        concentration_ppm: float,
    ) -> np.ndarray:
        profile = np.zeros_like(time_s, dtype=float)
        period = on_time + off_time
        if period <= 0:
            return profile

        for i, t in enumerate(time_s):
            cycle = int(t // period)
            if cycle >= cycles:
                profile[i] = 0.0
                continue
            pos = t % period
            profile[i] = concentration_ppm if pos < on_time else 0.0
        return profile

    def simulate(
        self,
        concentration_ppm: float,
        temperature_c: float,
        humidity_percent: float,
        exposure_time_s: float,
        recovery_time_s: float,
        dt_s: float,
        cycles: int,
        base_resistance_ohm: float,
        sensitivity: float,
        adsorption_rate: float,
        desorption_rate: float,
        response_exponent: float = 1.4,
        drift_rate: float = 0.0,
        noise_ohm: float = 0.0,
        incomplete_recovery: float = 0.0,
        seed: int = 7,
    ) -> SimulationResult:
        total_time = max(dt_s, cycles * (exposure_time_s + recovery_time_s))
        time_s = np.arange(0.0, total_time + dt_s, dt_s)

        gas_ppm = self._gas_profile(
            time_s=time_s,
            on_time=exposure_time_s,
            off_time=recovery_time_s,
            cycles=cycles,
            concentration_ppm=concentration_ppm,
        )

        coverage = np.zeros_like(time_s, dtype=float)
        conc_scaled = gas_ppm / 1000.0

        temp_factor_ads = max(0.2, 1.0 + 0.0025 * (temperature_c - 25.0))
        temp_factor_des = max(0.2, 1.0 + 0.0015 * (temperature_c - 25.0))
        humidity_factor = max(0.25, 1.0 - 0.006 * humidity_percent)

        k_ads = adsorption_rate * temp_factor_ads * humidity_factor
        k_des = desorption_rate * temp_factor_des

        floor = float(np.clip(incomplete_recovery, 0.0, 0.95))

        for i in range(1, len(time_s)):
            prev = coverage[i - 1]
            dtheta = k_ads * conc_scaled[i] * (1.0 - prev) - k_des * max(prev - floor, 0.0)
            coverage[i] = np.clip(prev + dtheta * dt_s, floor, 1.0)

        response = sensitivity * np.power(coverage, response_exponent)
        baseline = base_resistance_ohm * (1.0 + drift_rate * time_s)
        resistance_ohm = baseline * (1.0 + response)

        if noise_ohm > 0.0:
            rng = np.random.default_rng(seed)
            resistance_ohm = resistance_ohm + rng.normal(0.0, noise_ohm, size=resistance_ohm.shape)

        return SimulationResult(
            time_s=time_s,
            gas_ppm=gas_ppm,
            coverage=coverage,
            response=response,
            resistance_ohm=resistance_ohm,
        )
