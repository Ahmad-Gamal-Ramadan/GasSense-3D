from __future__ import annotations
from pathlib import Path
import pandas as pd
from core.response_model import SimulationResult


class ResultExporter:
    @staticmethod
    def to_csv(filepath: str | Path, result: SimulationResult) -> Path:
        path = Path(filepath)
        df = pd.DataFrame(
            {
                "time_s": result.time_s,
                "gas_ppm": result.gas_ppm,
                "coverage": result.coverage,
                "response": result.response,
                "resistance_ohm": result.resistance_ohm,
            }
        )
        df.to_csv(path, index=False)
        return path
