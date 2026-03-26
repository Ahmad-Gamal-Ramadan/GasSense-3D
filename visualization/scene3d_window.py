from __future__ import annotations

from PySide6.QtWidgets import QMainWindow
from visualization.scene3d import Sensor3DWidget


class Sensor3DWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("3D Sensor View")
        self.resize(900, 650)
        self.scene = Sensor3DWidget()
        self.setCentralWidget(self.scene)

    def update_state(self, gas_name: str, material_name: str, gas_ppm: float, coverage: float, time_s: float) -> None:
        self.scene.update_state(gas_name, material_name, gas_ppm, coverage, time_s)
