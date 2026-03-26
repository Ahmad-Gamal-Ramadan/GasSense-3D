from __future__ import annotations

import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QWidget, QVBoxLayout


class Sensor3DWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        self.plotter.set_background("#0f172a")
        self.plotter.add_axes()
        self.plotter.show_grid(color="white")

        self.sensor_actor = None
        self.particle_actor = None
        self.text_actor = None

        self._build_scene()

    def _build_scene(self) -> None:
        self.plotter.clear()

        chamber = pv.Box(bounds=(-1.8, 1.8, -1.4, 1.4, -0.2, 2.2))
        self.plotter.add_mesh(chamber, style="wireframe", color="white", opacity=0.16, line_width=1)

        substrate = pv.Box(bounds=(-1.25, 1.25, -0.85, 0.85, -0.04, 0.0))
        self.plotter.add_mesh(substrate, color="#94a3b8", opacity=1.0)

        sensor_mesh = pv.Box(bounds=(-0.95, 0.95, -0.55, 0.55, 0.0, 0.08))
        self.sensor_actor = self.plotter.add_mesh(sensor_mesh, color="#22c55e", smooth_shading=True)

        left_e = pv.Box(bounds=(-1.15, -0.95, -0.55, 0.55, 0.01, 0.09))
        right_e = pv.Box(bounds=(0.95, 1.15, -0.55, 0.55, 0.01, 0.09))
        self.plotter.add_mesh(left_e, color="#f59e0b")
        self.plotter.add_mesh(right_e, color="#f59e0b")

        self.text_actor = self.plotter.add_text("GasSense 3D", position="upper_left", font_size=12, color="white")
        self._update_particles(gas_name="NO2", gas_ppm=0.0, coverage=0.0)
        self.plotter.camera_position = "iso"

    def _update_particles(self, gas_name: str, gas_ppm: float, coverage: float) -> None:
        if self.particle_actor is not None:
            try:
                self.plotter.remove_actor(self.particle_actor, reset_camera=False)
            except Exception:
                pass

        level = float(np.clip(coverage, 0.0, 1.0))
        gas_level = float(np.clip(gas_ppm / 500.0, 0.0, 1.0))
        density = max(level, gas_level)
        count = max(8, int(120 * density) + 10)

        rng = np.random.default_rng(123)
        x = rng.uniform(-1.5, 1.5, count)
        y = rng.uniform(-1.1, 1.1, count)

        z_top = 1.8 - 1.1 * density
        z_low = max(0.18, z_top - (0.9 + 0.25 * density))
        z = rng.uniform(z_low, max(z_top, z_low + 0.1), count)

        points = np.column_stack([x, y, z])
        poly = pv.PolyData(points)

        self.particle_actor = self.plotter.add_mesh(
            poly,
            render_points_as_spheres=True,
            point_size=10 + 18 * density,
            color="#a855f7",
            opacity=0.72,
        )

    def update_state(self, gas_name: str, material_name: str, gas_ppm: float, coverage: float, time_s: float) -> None:
        level = float(np.clip(coverage, 0.0, 1.0))
        sensor_color = "#22c55e"
        if level > 0.15:
            sensor_color = "#eab308"
        if level > 0.35:
            sensor_color = "#f97316"
        if level > 0.60:
            sensor_color = "#ef4444"

        if self.sensor_actor is not None:
            self.sensor_actor.GetProperty().SetColor(pv.Color(sensor_color).float_rgb)

        self._update_particles(gas_name=gas_name, gas_ppm=gas_ppm, coverage=coverage)

        if self.text_actor is not None:
            try:
                self.plotter.remove_actor(self.text_actor, reset_camera=False)
            except Exception:
                pass

        self.text_actor = self.plotter.add_text(
            f"t={time_s:6.1f} s | {material_name} | gas={gas_name} | ppm={gas_ppm:6.1f} | coverage={coverage:.3f}",
            position="upper_left",
            font_size=12,
            color="white",
        )
        self.plotter.render()
