# File:      TemperatureVisualizer.py
# Time:      2025-08-24
# Author:    Fuuraiko
# Desc:      This file defines the main GUI for the temperature monitoring application using PyQt5.
#            It visualizes data in real-time and provides user controls for the simulation.

import sys
import time
import csv
import datetime
from PyQt5.QtWidgets import (
                             QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QGroupBox, QTextEdit, QFileDialog)
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
import pyqtgraph as pg
import TemperatureController

# ==================== Worker Thread ====================
class Worker(QObject):
    """
    Runs the temperature controller in a background thread to keep the GUI responsive.
    """
    data_updated = pyqtSignal(float, float, bool, int, float)
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
                stable_duration = self.controller.get_stable_duration()
                self.data_updated.emit(temp, setpoint, is_stable, schedule_index, stable_duration)
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
        
        # Use standard lists to store all historical data
        self.times = []
        self.temperatures = []
        
        self.is_auto_range_enabled = True # Flag for plot auto-ranging

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
        self.final_target_label = QLabel("Final Target: N/A")
        self.setpoint_label = QLabel("Current Setpoint: N/A")
        self.temp_label = QLabel("Current Temp: N/A")
        
        status_bar_layout.addWidget(self.mode_label)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(QLabel("|"))
        status_bar_layout.addWidget(self.final_target_label)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(QLabel("|"))
        status_bar_layout.addWidget(self.setpoint_label)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(QLabel("|"))
        status_bar_layout.addWidget(self.temp_label)
        left_layout.addLayout(status_bar_layout)
        
        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Temperature', 'K')
        self.plot_widget.setLabel('bottom', 'Time', 's')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.getViewBox().setLimits(xMin=0) # Prevent negative time axis
        self.plot_widget.sigRangeChanged.connect(self.on_plot_range_changed)
        self.temp_curve = self.plot_widget.plot([], [], pen=pg.mkPen('b', width=2), name="Live Temperature")
        # Enable auto-downsampling for performance with large datasets
        self.temp_curve.setDownsampling(auto=True, ds='auto')
        
        left_layout.addWidget(self.plot_widget)
        
        # Control Buttons
        controls_layout = QHBoxLayout()
        self.auto_mode_checkbox = QPushButton("Auto Mode")
        self.auto_mode_checkbox.setCheckable(True)
        self.auto_mode_checkbox.clicked.connect(self.on_auto_mode_toggled)
        self.pause_button = QPushButton("Pause")
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.on_pause_toggled)
        self.reset_button = QPushButton("Reset Simulation")
        self.reset_button.clicked.connect(self.on_reset_simulation_clicked)
        self.reset_view_button = QPushButton("Reset View")
        self.reset_view_button.clicked.connect(self.on_reset_view_clicked)
        controls_layout.addWidget(self.auto_mode_checkbox)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(self.reset_view_button)
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
        self.stability_timer_label = QLabel("Time Stable: 0.0s")
        stability_layout.addWidget(self.stability_status_label)
        stability_layout.addWidget(self.stable_time_label)
        stability_layout.addWidget(self.stability_timer_label)
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
        
        # Data Management Group
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout(data_group)
        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.on_export_data_clicked)
        data_layout.addWidget(self.export_button)
        right_layout.addWidget(data_group)

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
        self.controller = TemperatureController.TemperatureController(config_filename, is_debug_mode=TemperatureController.DEBUG_MODE)
        
        self.thread = QThread()
        self.worker = Worker(self.controller)
        self.worker.moveToThread(self.thread)

        self.worker.data_updated.connect(self.on_data_updated)
        self.worker.log_generated.connect(self.log_message)
        self.thread.started.connect(self.worker.run)
        
        # Initialize UI with the first data point
        self.times.append(time.time())
        self.temperatures.append(self.controller.get_temperature())
        self._update_plot()
        self._update_system_info_panel(self.controller.get_schedule_index())
        self.mode_label.setText(f"Mode: {'Simulation' if self.controller.is_debug_mode else 'Live Instrument'}")
        self.final_target_label.setText(f"Final Target: {self.controller.get_final_target():.2f} K")

        self.thread.start()
        self.auto_mode_checkbox.click() # Start in auto mode by default

    @pg.QtCore.pyqtSlot(str)
    def log_message(self, message):
        """Appends a message to the log text box."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text_edit.append(f"[{timestamp}] {message}")

    def on_request_update_clicked(self):
        """Handles the 'Request Next Setpoint' button click in manual mode."""
        if not self.controller.is_auto_mode():
            self.controller.request_update()
            self.update_button.setEnabled(False)
            self.stability_status_label.setText("Status: Update Requested")
            self.log_message("User requested next setpoint.")

    def on_auto_mode_toggled(self):
        """Handles the auto/manual mode button click."""
        is_auto = self.auto_mode_checkbox.isChecked()
        self.controller.set_auto_mode(is_auto)
        self.log_message(f"Switched to {'Auto' if is_auto else 'Manual'} mode.")
        
        if is_auto:
            self.auto_mode_checkbox.setText("Switch to Manual")
            self.update_button.setText("Auto-advancing...")
            self.update_button.setEnabled(False)
        else:
            self.auto_mode_checkbox.setText("Switch to Auto")
            self.update_button.setText("Request Next Setpoint")
            self.update_button.setEnabled(self.controller.get_stable_status())

    def on_pause_toggled(self):
        """Handles the pause/resume button click."""
        is_paused = self.pause_button.isChecked()
        self.worker.set_paused(is_paused)
        self.pause_button.setText("Resume" if is_paused else "Pause")

    def on_reset_simulation_clicked(self):
        """Resets the simulation by creating a new controller and worker."""
        self.log_message("Resetting simulation...")
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        
        self.times.clear()
        self.temperatures.clear()

        self._setup_thread() 
        
        self.on_reset_view_clicked() # Reset plot view to auto-range
        self.update_button.setEnabled(False)
        self.stability_status_label.setText("Status: Not Stable")
        self.stability_timer_label.setText("Time Stable: 0.0s")
        self.log_message("Simulation reset.")

    def on_plot_range_changed(self):
        """Disables auto-ranging when the user manually pans or zooms."""
        self.is_auto_range_enabled = False

    def on_reset_view_clicked(self):
        """Resets the plot view to auto-ranging."""
        self.is_auto_range_enabled = True
        self._update_plot()

    def on_export_data_clicked(self):
        """Opens a file dialog to save all collected temperature data to a CSV file."""
        if not self.times:
            self.log_message("No data to export.")
            return

        default_filename = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Data", default_filename, "CSV Files (*.csv);;All Files (*)", options=options)

        if filePath:
            try:
                with open(filePath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Timestamp', 'Temperature (K)'])
                    for i in range(len(self.times)):
                        # Convert unix timestamp to human-readable format
                        readable_time = datetime.datetime.fromtimestamp(self.times[i]).strftime('%Y-%m-%d %H:%M:%S')
                        writer.writerow([readable_time, self.temperatures[i]])
                self.log_message(f"Data successfully exported to {filePath}")
            except Exception as e:
                self.log_message(f"Error exporting data: {e}")

    def _update_system_info_panel(self, schedule_index):
        """Updates the labels in the system information panel."""
        self.schedule_label.setText(f"Schedule File: {self.controller.config_file}")
        self.schedule_index_label.setText(f"Current Index: {schedule_index}/{len(self.controller.setpoint_schedule)-1}")
        self.stable_time_label.setText(f"Required Stable Time: {self.controller.current_stable_time}s")

    @pg.QtCore.pyqtSlot(float, float, bool, int, float)
    def on_data_updated(self, temp, setpoint, is_stable, schedule_index, stable_duration):
        """Slot to receive data from the worker thread and update the GUI."""
        self.times.append(time.time())
        self.temperatures.append(temp)

        self.stability_timer_label.setText(f"Time Stable: {stable_duration:.1f}s")

        if is_stable:
            self.stability_status_label.setText("Status: Stable")
            self.stability_status_label.setStyleSheet("color: green;")
            if self.controller.is_auto_mode():
                self.update_button.setEnabled(False)
                self.stability_status_label.setText("Status: Stable, auto-advancing...")
            else:
                self.update_button.setEnabled(True)
                self.stability_status_label.setText("Status: Stable, waiting for user.")
        else:
            self.stability_status_label.setText("Status: Not Stable")
            self.stability_status_label.setStyleSheet("color: orange;")
            self.update_button.setEnabled(False)

        self.temp_label.setText(f"Current Temp: {temp:.4f} K")
        self.setpoint_label.setText(f"Current Setpoint: {setpoint:.4f} K")
        
        self._update_system_info_panel(schedule_index)
        self._update_plot()

    def _update_plot(self):
        """Updates the plot with new data, ensuring all data is visible."""
        if not self.times:
            self.temp_curve.setData([], [])
            if self.is_auto_range_enabled:
                self.plot_widget.setXRange(0, 100)
            return

        start_time = self.times[0]
        relative_times = [t - start_time for t in self.times]
        self.temp_curve.setData(relative_times, self.temperatures)

        if self.is_auto_range_enabled:
            # Temporarily disconnect the signal to prevent a feedback loop
            try:
                self.plot_widget.sigRangeChanged.disconnect(self.on_plot_range_changed)
            except (TypeError, RuntimeError):
                # This can happen if the signal was already disconnected
                pass

            try:
                # Set Y-axis range based on the full temperature schedule
                start_temp = self.controller.get_initial_temperature()
                final_temp = self.controller.get_final_target()
                min_val = min(start_temp, final_temp)
                max_val = max(start_temp, final_temp)
                padding = (max_val - min_val) * 0.1
                self.plot_widget.setYRange(min_val - padding, max_val + padding if padding > 0 else max_val + 1)

                # Set X-axis to show all data from 0 to the latest time, with a small right-side padding
                current_max_time = relative_times[-1] if relative_times else 0
                # Ensure a minimum visible range, then add padding
                visible_range = max(100, current_max_time * 1.05) 
                self.plot_widget.setXRange(0, visible_range, padding=0)
            finally:
                # Always reconnect the signal
                self.plot_widget.sigRangeChanged.connect(self.on_plot_range_changed)

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
