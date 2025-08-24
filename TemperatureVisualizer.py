# File:      TemperatureVisualizer.py
# Time:      2025-08-24
# Author:    Fuuraiko
# Desc:      This file defines the main GUI for the temperature monitoring application using PyQt5.
#            It visualizes data in real-time and provides user controls for the simulation.

import sys
import time
from collections import deque
from PyQt5.QtWidgets import (
                             QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QGroupBox, QTextEdit)
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
import pyqtgraph as pg
import datetime
import TemperatureController

# ==================== Worker Thread ====================
class Worker(QObject):
    """
    Runs the temperature controller in a background thread to keep the GUI responsive.
    """
    data_updated = pyqtSignal(float, float, bool, int)
    log_generated = pyqtSignal(str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._is_running = True
        self._is_paused = False

    def run(self):
        """Main worker loop. Emits data signals at regular intervals."""
        while self._is_running:
            if not self._is_paused:
                self.controller.update()
                temp = self.controller.get_temperature()
                setpoint = self.controller.get_setpoint()
                is_stable = self.controller.get_stable_status()
                schedule_index = self.controller.get_schedule_index()
                self.data_updated.emit(temp, setpoint, is_stable, schedule_index)
            time.sleep(1) # Update interval

    def set_paused(self, paused):
        """Pauses or resumes the simulation loop."""
        self._is_paused = paused
        self.log_generated.emit(f"Simulation {'paused' if paused else 'resumed'}.")

    def stop(self):
        """Stops the worker loop."""
        self._is_running = False

# ==================== Main Window ====================
class TemperatureMonitor(QMainWindow):
    """The main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Temperature Monitor - Asynchronous")
        self.setGeometry(100, 100, 1200, 800)
        
        self.MAX_DATA_POINTS = 200
        self.times = deque(maxlen=self.MAX_DATA_POINTS)
        self.temperatures = deque(maxlen=self.MAX_DATA_POINTS)
        self.setpoints = deque(maxlen=self.MAX_DATA_POINTS)
        
        self._setup_ui()
        self._setup_thread()

        self.log_message("System startup complete.")
        self.log_message(f"Mode: {'Simulation' if self.controller.is_debug_mode else 'Live Instrument'}")

    def _setup_ui(self):
        """Initializes all UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left Panel - Plot
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Status Bar
        status_bar_layout = QHBoxLayout()
        self.mode_label = QLabel("Mode: Unknown")
        self.temp_label = QLabel("Current Temp: N/A")
        self.target_label = QLabel("Target Temp: N/A")
        self.stability_label = QLabel("Stability: N/A")
        
        status_bar_layout.addWidget(self.mode_label)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(self.target_label)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(self.stability_label)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(self.temp_label)
        left_layout.addLayout(status_bar_layout)
        
        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Temperature', 'K')
        self.plot_widget.setLabel('bottom', 'Time', 's')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)
        self.temp_curve = self.plot_widget.plot([], [], pen=pg.mkPen('b', width=2), name="Live Temperature")
        self.setpoint_curve = self.plot_widget.plot([], [], pen=pg.mkPen('r', width=2, style=Qt.DashLine), name="Target Temperature")
        left_layout.addWidget(self.plot_widget)
        
        # Control Buttons
        controls_layout = QHBoxLayout()
        self.pause_button = QPushButton("Pause")
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.on_pause_toggled)
        self.clear_button = QPushButton("Clear Data")
        self.clear_button.clicked.connect(self.on_clear_data_clicked)
        self.reset_button = QPushButton("Reset Simulation")
        self.reset_button.clicked.connect(self.on_reset_simulation_clicked)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addStretch()
        left_layout.addLayout(controls_layout)
        
        # Right Panel - Controls & Info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Stability Control Group
        stability_group = QGroupBox("Stability Control")
        stability_layout = QVBoxLayout(stability_group)
        self.update_button = QPushButton("Request Next Setpoint")
        self.update_button.clicked.connect(self.on_request_update_clicked)
        self.update_button.setEnabled(False)
        self.stability_status_label = QLabel("Status: Not Stable")
        self.stable_time_label = QLabel("Required Stable Time: N/A")
        stability_layout.addWidget(self.stability_status_label)
        stability_layout.addWidget(self.stable_time_label)
        stability_layout.addWidget(self.update_button)
        right_layout.addWidget(stability_group)
        
        # System Info Group
        info_group = QGroupBox("System Information")
        info_layout = QVBoxLayout(info_group)
        self.schedule_label = QLabel("Schedule File: N/A")
        self.schedule_index_label = QLabel("Current Index: N/A")
        info_layout.addWidget(self.schedule_label)
        info_layout.addWidget(self.schedule_index_label)
        right_layout.addWidget(info_group)
        
        # Log Group
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        log_layout.addWidget(self.log_text_edit)
        right_layout.addWidget(log_group)
        right_layout.addStretch()
        
        main_layout.addWidget(left_panel, 3)
        main_layout.addWidget(right_panel, 1)

    def _setup_thread(self):
        """Creates and starts the background worker thread."""
        config_filename = 'E:\\Projects\\Lab-Protocol\\config.csv'
        self.controller = TemperatureController.TemperatureController(config_filename)
        
        self.thread = QThread()
        self.worker = Worker(self.controller)
        self.worker.moveToThread(self.thread)

        self.worker.data_updated.connect(self.on_data_updated)
        self.worker.log_generated.connect(self.log_message)
        self.thread.started.connect(self.worker.run)
        
        # Initialize UI with the first data point
        self.times.append(time.time())
        self.temperatures.append(self.controller.get_temperature())
        self.setpoints.append(self.controller.get_setpoint())
        self._update_plot()
        self._update_system_info_panel(self.controller.get_schedule_index())
        self.mode_label.setText(f"Mode: {'Simulation' if self.controller.is_debug_mode else 'Live Instrument'}")

        self.thread.start()

    @pg.QtCore.pyqtSlot(str)
    def log_message(self, message):
        """Appends a message to the log text box."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text_edit.append(f"[{timestamp}] {message}")

    def on_request_update_clicked(self):
        """Handles the 'Request Next Setpoint' button click."""
        self.controller.request_update()
        self.update_button.setEnabled(False)
        self.stability_status_label.setText("Status: Update Requested")
        self.log_message("User requested next setpoint.")

    def on_pause_toggled(self):
        """Handles the pause/resume button click."""
        is_paused = self.pause_button.isChecked()
        self.worker.set_paused(is_paused)
        self.pause_button.setText("Resume" if is_paused else "Pause")

    def on_clear_data_clicked(self):
        """Clears the plot data."""
        self.times.clear()
        self.temperatures.clear()
        self.setpoints.clear()
        self.times.append(time.time())
        self.temperatures.append(self.controller.get_temperature())
        self.setpoints.append(self.controller.get_setpoint())
        self._update_plot()
        self.log_message("Plot data cleared.")

    def on_reset_simulation_clicked(self):
        """Resets the simulation by creating a new controller and worker."""
        self.log_message("Resetting simulation...")
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        
        self._setup_thread()
        self.on_clear_data_clicked()
        self.update_button.setEnabled(False)
        self.stability_status_label.setText("Status: Not Stable")
        self.log_message("Simulation reset.")

    def _update_system_info_panel(self, schedule_index):
        """Updates the labels in the system information panel."""
        self.schedule_label.setText(f"Schedule File: {self.controller.config_file}")
        self.schedule_index_label.setText(f"Current Index: {schedule_index}/{len(self.controller.setpoint_schedule)-1}")
        self.stable_time_label.setText(f"Required Stable Time: {self.controller.current_stable_time}s")

    @pg.QtCore.pyqtSlot(float, float, bool, int)
    def on_data_updated(self, temp, setpoint, is_stable, schedule_index):
        """Slot to receive data from the worker thread and update the GUI."""
        self.times.append(time.time())
        self.temperatures.append(temp)
        self.setpoints.append(setpoint)

        self.stability_label.setText(f"Stable: {is_stable}")
        if is_stable:
            self.stability_label.setStyleSheet("color: green;")
            self.stability_status_label.setText("Status: Stable, waiting for user.")
            self.update_button.setEnabled(True)
        else:
            self.stability_label.setStyleSheet("color: orange;")
            self.stability_status_label.setText("Status: Not Stable")
            self.update_button.setEnabled(False)

        self.temp_label.setText(f"Current Temp: {temp:.4f} K")
        self.target_label.setText(f"Target Temp: {setpoint:.4f} K")
        
        self._update_system_info_panel(schedule_index)
        self._update_plot()

    def _update_plot(self):
        """Updates the plot with new data."""
        if len(self.times) > 1:
            relative_times = [t - self.times[0] for t in self.times]
            self.temp_curve.setData(relative_times, list(self.temperatures))
            self.setpoint_curve.setData(relative_times, list(self.setpoints))

    def closeEvent(self, event):
        """Ensures the background thread is stopped when the window is closed."""
        self.log_message("Closing application...")
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        event.accept()

# ==================== Main Execution ====================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TemperatureMonitor()
    window.show()
    sys.exit(app.exec_())