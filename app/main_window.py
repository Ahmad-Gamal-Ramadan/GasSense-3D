from __future__ import annotations

import sys
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from analysis.export import ResultExporter
from core.presets import GAS_PRESETS, MATERIAL_PRESETS
from core.response_model import GasSensorResponseModel, SimulationResult
from visualization.scene3d_window import Sensor3DWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GasSense 3D - Live Animation")
        self.resize(1500, 950)

        self.model = GasSensorResponseModel()
        self.current_result: SimulationResult | None = None
        self.current_gas_name = "NO2"
        self.current_material_name = "Graphene"

        self.anim_index = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._advance_animation)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        self.scene3d_window = Sensor3DWindow()
        self.scene3d_window.show()

        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()

        root.addWidget(left_panel, 0)
        root.addWidget(right_panel, 1)

        self._load_defaults()
        self.run_simulation()

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        panel.setMaximumWidth(380)
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        title = QLabel("Simulation Controls")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        layout.addWidget(title)

        box = QGroupBox("Experiment Parameters")
        form = QFormLayout(box)

        self.gas_combo = QComboBox()
        self.gas_combo.addItems(GAS_PRESETS.keys())

        self.material_combo = QComboBox()
        self.material_combo.addItems(MATERIAL_PRESETS.keys())

        self.concentration_spin = self._double_spin(1, 5000, 1, " ppm", 100)
        self.temperature_spin = self._double_spin(0, 600, 1, " °C", 250)
        self.humidity_spin = self._double_spin(0, 100, 1, " %", 10)
        self.exposure_spin = self._double_spin(1, 300, 1, " s", 30)
        self.recovery_spin = self._double_spin(1, 300, 1, " s", 40)
        self.dt_spin = self._double_spin(0.01, 5.0, 0.01, " s", 0.1, decimals=2)
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(1, 20)
        self.cycles_spin.setValue(4)

        self.response_exp_spin = self._double_spin(0.2, 4.0, 0.1, "", 1.4, decimals=2)
        self.noise_spin = self._double_spin(0.0, 200.0, 0.05, " Ω", 0.2, decimals=3)
        self.drift_spin = self._double_spin(0.0, 0.01, 0.00001, "", 0.00005, decimals=6)
        self.incomplete_spin = self._double_spin(0.0, 0.95, 0.01, "", 0.01, decimals=3)
        self.anim_speed_spin = QSpinBox()
        self.anim_speed_spin.setRange(10, 500)
        self.anim_speed_spin.setValue(40)
        self.anim_speed_spin.setSuffix(" ms")

        form.addRow("Gas", self.gas_combo)
        form.addRow("Sensor material", self.material_combo)
        form.addRow("Concentration", self.concentration_spin)
        form.addRow("Temperature", self.temperature_spin)
        form.addRow("Humidity", self.humidity_spin)
        form.addRow("Exposure time", self.exposure_spin)
        form.addRow("Recovery time", self.recovery_spin)
        form.addRow("Time step", self.dt_spin)
        form.addRow("Cycles", self.cycles_spin)
        form.addRow("Response exponent", self.response_exp_spin)
        form.addRow("Noise level", self.noise_spin)
        form.addRow("Drift rate", self.drift_spin)
        form.addRow("Incomplete recovery", self.incomplete_spin)
        form.addRow("Animation speed", self.anim_speed_spin)
        layout.addWidget(box)

        btn_row1 = QHBoxLayout()
        run_btn = QPushButton("Run Simulation")
        run_btn.clicked.connect(self.run_simulation)
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self.export_csv)
        btn_row1.addWidget(run_btn)
        btn_row1.addWidget(export_btn)
        layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        self.play_btn = QPushButton("Play 3D")
        self.play_btn.clicked.connect(self.play_animation)
        pause_btn = QPushButton("Pause 3D")
        pause_btn.clicked.connect(self.pause_animation)
        open3d_btn = QPushButton("Show 3D Window")
        open3d_btn.clicked.connect(self.show_3d_window)
        btn_row2.addWidget(self.play_btn)
        btn_row2.addWidget(pause_btn)
        btn_row2.addWidget(open3d_btn)
        layout.addLayout(btn_row2)

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.valueChanged.connect(self._slider_changed)
        layout.addWidget(QLabel("Animation Timeline"))
        layout.addWidget(self.frame_slider)

        self.frame_info_label = QLabel("Frame: 0")
        layout.addWidget(self.frame_info_label)

        self.summary_label = QLabel("No results yet.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.summary_label.setStyleSheet(
            "background:#f3f6fb; border:1px solid #cbd5e1; border-radius:10px; padding:12px; font-size:14px;"
        )
        layout.addWidget(self.summary_label)
        layout.addStretch(1)
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        info = QLabel(
            ""
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size:14px; color:#334155;")
        layout.addWidget(info)

        self.gas_plot = self._make_plot("Gas Concentration vs Time", "Gas", "ppm")
        self.response_plot = self._make_plot("Normalized Response vs Time", "Response", "")
        self.coverage_plot = self._make_plot("Surface Coverage vs Time", "Coverage", "")
        self.resistance_plot = self._make_plot("Resistance vs Time", "Resistance", "Ω")

        layout.addWidget(self.gas_plot)
        layout.addWidget(self.response_plot)
        layout.addWidget(self.coverage_plot)
        layout.addWidget(self.resistance_plot)
        return panel

    def _make_plot(self, title: str, left_label: str, unit: str) -> pg.PlotWidget:
        plot = pg.PlotWidget(title=title)
        plot.showGrid(x=True, y=True, alpha=0.25)
        plot.setLabel("left", left_label, units=unit)
        plot.setLabel("bottom", "Time", units="s")
        plot.setMinimumHeight(170)
        return plot

    def _double_spin(self, mn, mx, step, suffix, value, decimals=1) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(mn, mx)
        spin.setDecimals(decimals)
        spin.setSingleStep(step)
        spin.setSuffix(suffix)
        spin.setValue(value)
        return spin

    def _load_defaults(self) -> None:
        self.gas_combo.setCurrentText("NO2")
        self.material_combo.setCurrentText("Graphene")

    def show_3d_window(self) -> None:
        self.scene3d_window.show()
        self.scene3d_window.raise_()
        self.scene3d_window.activateWindow()

    def run_simulation(self) -> None:
        self.pause_animation()

        gas = GAS_PRESETS[self.gas_combo.currentText()]
        material = MATERIAL_PRESETS[self.material_combo.currentText()]
        self.current_gas_name = gas.name
        self.current_material_name = material.name

        concentration = self.concentration_spin.value() or gas.default_concentration_ppm

        result = self.model.simulate(
            concentration_ppm=concentration,
            temperature_c=self.temperature_spin.value(),
            humidity_percent=self.humidity_spin.value(),
            exposure_time_s=self.exposure_spin.value(),
            recovery_time_s=self.recovery_spin.value(),
            dt_s=self.dt_spin.value(),
            cycles=self.cycles_spin.value(),
            base_resistance_ohm=material.base_resistance_ohm,
            sensitivity=material.sensitivity,
            adsorption_rate=material.adsorption_rate,
            desorption_rate=material.desorption_rate,
            response_exponent=self.response_exp_spin.value(),
            drift_rate=self.drift_spin.value(),
            noise_ohm=self.noise_spin.value(),
            incomplete_recovery=self.incomplete_spin.value(),
        )

        self.current_result = result
        self.anim_index = 0
        self.frame_slider.blockSignals(True)
        self.frame_slider.setMaximum(max(0, len(result.time_s) - 1))
        self.frame_slider.setValue(0)
        self.frame_slider.blockSignals(False)

        self._update_plots(result)
        self._update_summary(result)
        self._apply_frame(0)

    def _update_plots(self, result: SimulationResult) -> None:
        plots = [self.gas_plot, self.response_plot, self.coverage_plot, self.resistance_plot]
        for p in plots:
            p.clear()

        self.gas_plot.plot(result.time_s, result.gas_ppm, pen=pg.mkPen(width=2))
        self.response_plot.plot(result.time_s, result.response, pen=pg.mkPen(width=2))
        self.coverage_plot.plot(result.time_s, result.coverage, pen=pg.mkPen(width=2))
        self.resistance_plot.plot(result.time_s, result.resistance_ohm, pen=pg.mkPen(width=2))

    def _update_summary(self, result: SimulationResult) -> None:
        peak_idx = int(result.response.argmax())
        self.summary_label.setText(
            f"Gas: {self.current_gas_name}\n"
            f"Material: {self.current_material_name}\n"
            f"Peak response: {float(result.response.max()):.4f}\n"
            f"Peak resistance: {float(result.resistance_ohm.max()):.2f} Ω\n"
            f"Time to peak: {float(result.time_s[peak_idx]):.2f} s\n"
            f"Max surface coverage: {float(result.coverage.max()):.4f}\n"
            f"Frames: {len(result.time_s)}"
        )

    def _apply_frame(self, index: int) -> None:
        if self.current_result is None:
            return
        idx = max(0, min(index, len(self.current_result.time_s) - 1))
        self.anim_index = idx
        self.frame_info_label.setText(
            f"Frame: {idx} | t = {self.current_result.time_s[idx]:.2f} s | "
            f"gas = {self.current_result.gas_ppm[idx]:.1f} ppm | "
            f"coverage = {self.current_result.coverage[idx]:.3f}"
        )

        self.scene3d_window.update_state(
            gas_name=self.current_gas_name,
            material_name=self.current_material_name,
            gas_ppm=float(self.current_result.gas_ppm[idx]),
            coverage=float(self.current_result.coverage[idx]),
            time_s=float(self.current_result.time_s[idx]),
        )

    def _advance_animation(self) -> None:
        if self.current_result is None:
            return
        next_idx = self.anim_index + 1
        if next_idx >= len(self.current_result.time_s):
            self.pause_animation()
            return
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(next_idx)
        self.frame_slider.blockSignals(False)
        self._apply_frame(next_idx)

    def _slider_changed(self, value: int) -> None:
        self._apply_frame(value)

    def play_animation(self) -> None:
        if self.current_result is None:
            return
        self.show_3d_window()
        self.animation_timer.start(self.anim_speed_spin.value())

    def pause_animation(self) -> None:
        self.animation_timer.stop()

    def export_csv(self) -> None:
        if self.current_result is None:
            QMessageBox.warning(self, "No data", "Run a simulation first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            str(Path.home() / "gas_sensor_results.csv"),
            "CSV Files (*.csv)",
        )
        if not path:
            return

        ResultExporter.to_csv(path, self.current_result)
        QMessageBox.information(self, "Export complete", f"Saved to:\n{path}")


def run() -> None:
    app = QApplication(sys.argv)
    pg.setConfigOptions(antialias=True)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
