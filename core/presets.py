from __future__ import annotations
from core.models import Gas, SensorMaterial

GAS_PRESETS = {
    "NO2": Gas("NO2", 100.0),
    "NH3": Gas("NH3", 50.0),
    "H2": Gas("H2", 200.0),
    "Ethanol": Gas("Ethanol", 100.0),
}

MATERIAL_PRESETS = {
    "Graphene": SensorMaterial("Graphene", 450.0, 4.0, 0.22, 0.045),
    "ZnO": SensorMaterial("ZnO", 900.0, 2.8, 0.12, 0.030),
    "SnO2": SensorMaterial("SnO2", 1200.0, 2.4, 0.10, 0.025),
    "WO3": SensorMaterial("WO3", 1500.0, 2.0, 0.085, 0.020),
}
