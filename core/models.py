from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Gas:
    name: str
    default_concentration_ppm: float


@dataclass(frozen=True)
class SensorMaterial:
    name: str
    base_resistance_ohm: float
    sensitivity: float
    adsorption_rate: float
    desorption_rate: float
