# File:      interface.py
# Time:      2025-08-27
# Author:    Fuuraiko
# Desc:      Implementation of the simulated PID cooler instrument.

import time
from datetime import datetime
from collections import deque
from dash.dependencies import Input, Output, State
from dash import dcc
import dash_bootstrap_components as dbc
import dash.html as html
import logging
import math
import os
import pandas as pd
import csv

from src.instruments.base import Instrument

# Get the logger instance from the main app
logger = logging.getLogger(__name__)

class PIDCoolerSimulator:
    """
    A simulator for a PID-controlled cooling system.
    It simulates a second-order system to make the cooling curve look more realistic.
    """
    def __init__(self):
        self._temperature = 300.0  # Start at room temperature
        self._setpoint = 300.0
        self._velocity = 0.0  # Rate of temperature change
        self._power = 0.0
        self.last_update_time = time.time()

    def set_setpoint(self, temp):
        self._setpoint = float(temp)
        logger.info(f"[SIMULATOR] New setpoint: {self._setpoint:.2f} K")

    def get_temperature(self):
        # PID constants
        P = 0.08  # Proportional gain
        I = 0.01  # Integral gain (not used in this simple model)
        D = 0.5   # Derivative gain

        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        error = self._setpoint - self._temperature
        
        # Damping and spring constants for a second-order system
        damping = 0.2 # Represents heat dissipation to environment
        spring_stiffness = 0.1 # Represents cooling power

        # Force is proportional to the error (P-controller)
        force = error * P

        # Update velocity (rate of change) based on force and damping
        # a = F/m - cv -> dv/dt = a
        acceleration = force - self._velocity * damping
        self._velocity += acceleration * dt * spring_stiffness

        # Update temperature
        self._temperature += self._velocity * dt
        
        # Add some noise
        self._temperature += (time.time() % 0.1 - 0.05)
        
        return self._temperature

class InstrumentInterface(Instrument):
    """
    The concrete implementation for the simulated PID cooler.
    """
    def __init__(self, instrument_id: str, config: dict):
        super().__init__(instrument_id, config)
        # Setpoints for a cooling schedule
        self.schedule = config.get("schedule", [])
        if not self.schedule:
            logger.warning(f"[{self.instrument_id}] No schedule found in config. Using default.")
            self.schedule = [{"setpoint": 273, "dwell_time": 10}] # Default schedule for simulator

        self.setpoint_schedule = [item["setpoint"] for item in self.schedule]
        
        # Instrument state
        self.device = None
        self.is_connected = False
        self.schedule_index = 0
        self.target_setpoint = self.schedule[0]["setpoint"]
        self.dwell_time = self.schedule[0]["dwell_time"] # Current dwell time for the active setpoint
        self.is_stable = False
        self.stabilization_start_time = None
        self.stable_duration = 0
        self.start_time = None
        self.auto_mode = True # Default to Auto Mode ON
        
        # Data history for plotting (last 10 minutes)
        self.time_history = deque(maxlen=600)
        self.temp_history = deque(maxlen=600)
        self.setpoint_history = deque(maxlen=600)

        # Data logging
        self.log_dir = "log"
        self.log_file = os.path.join(self.log_dir, f"{self.instrument_id}_data.csv")
        self.log_max_size_mb = 5
        self.log_write_interval = 100 # Check file size every 100 writes
        self.log_write_counter = 0
        self._last_logged_second = None # Track the last second a data point was logged
        self._init_log_file()

    def _init_log_file(self):
        """Ensures log directory and file exist with a header."""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "temperature", "setpoint"])
        except IOError as e:
            logger.error(f"Error initializing log file {self.log_file}: {e}")

    def connect(self) -> bool:
        """Establishes connection to the instrument."""
        try:
            self.device = PIDCoolerSimulator()
            self.device.set_setpoint(self.target_setpoint)
            self.is_connected = True
            self.start_time = datetime.now()
            logger.info(f"Initialized Simulated PID Cooler: {self.instrument_id}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to {self.instrument_id}: {e}", exc_info=True)
            return False

    def disconnect(self) -> bool:
        """Disconnects from the instrument."""
        self.is_connected = False
        logger.info(f"Disconnected from {self.instrument_id}.")
        return True

    def _log_data(self, timestamp, temperature, setpoint):
        """Appends a new data row to the CSV log file and handles trimming, ensuring only one entry per second."""
        current_second_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')

        # Only log if this second hasn't been logged yet, or if it's a new second
        if self._last_logged_second == current_second_str:
            return # Skip logging if data for this second has already been recorded

        try:
            # Append data
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([current_second_str, temperature, setpoint])
            
            self._last_logged_second = current_second_str # Update the last logged second

            # Check for trimming periodically
            self.log_write_counter += 1
            if self.log_write_counter >= self.log_write_interval:
                self.log_write_counter = 0
                self._trim_log_file()
        except IOError as e:
            logger.error(f"Error writing to log file {self.log_file}: {e}")

    def _trim_log_file(self):
        """Checks log file size and trims it if it exceeds the max size."""
        try:
            if os.path.getsize(self.log_file) > self.log_max_size_mb * 1024 * 1024:
                logger.info(f"Log file {self.log_file} exceeds {self.log_max_size_mb}MB. Trimming.")
                df = pd.read_csv(self.log_file)
                
                # Drop the oldest 25% of rows to make space
                num_rows_to_drop = int(len(df) * 0.25)
                df_trimmed = df.iloc[num_rows_to_drop:]
                
                # Rewrite the file with the trimmed data
                df_trimmed.to_csv(self.log_file, index=False)
        except (IOError, pd.errors.EmptyDataError) as e:
            logger.error(f"Error trimming log file {self.log_file}: {e}")

    def _go_to_next_setpoint(self):
        """Advances to the next setpoint in the schedule."""
        self.schedule_index = (self.schedule_index + 1) % len(self.schedule)
        current_schedule_item = self.schedule[self.schedule_index]
        self.target_setpoint = current_schedule_item["setpoint"]
        self.dwell_time = current_schedule_item["dwell_time"]
        self.device.set_setpoint(self.target_setpoint)
        # Reset stability state
        self.is_stable = False
        self.stabilization_start_time = None
        self.stable_duration = 0
        logger.info(f"[{self.instrument_id}] Setpoint changed to: {self.target_setpoint} K, Dwell Time: {self.dwell_time}s")

    def update_state(self):
        """
        Reads data from the instrument and updates the internal state.
        """
        if not self.is_connected:
            return

        current_temp = self.device.get_temperature()
        
        current_time = time.time()
        datetime_obj = datetime.fromtimestamp(current_time)
        
        self.time_history.append(datetime_obj)
        self.temp_history.append(current_temp)
        self.setpoint_history.append(self.target_setpoint)

        # Log data to file
        self._log_data(datetime_obj, current_temp, self.target_setpoint)

        stability_threshold = 0.5
        # Check for stability
        if abs(current_temp - self.target_setpoint) <= stability_threshold:
            if self.stabilization_start_time is None:
                self.stabilization_start_time = current_time
            self.stable_duration = current_time - self.stabilization_start_time
            
            # If stable for the required duration, mark as stable and advance if in auto mode
            if not self.is_stable and self.stable_duration >= self.dwell_time:
                self.is_stable = True
                if self.auto_mode:
                    self._go_to_next_setpoint()
        else:
            # Reset stability if temperature moves out of range
            self.stabilization_start_time = None
            self.stable_duration = 0
            self.is_stable = False
            
        self._state = {
            "temperature": current_temp,
            "setpoint": self.target_setpoint,
            "is_stable": self.is_stable,
            "stable_duration": self.stable_duration,
            "is_connected": self.is_connected,
            "schedule_index": self.schedule_index,
            "dwell_time": self.dwell_time # Include current dwell time in state
        }

    def get_layout(self):
        """
        Returns the Dash layout for this instrument.
        """
        from . import layout
        return layout.get_layout(self.instrument_id, self)

    def _parse_time(self, time_str, default_hour, default_minute):
        """Helper to parse HH:MM time string, with fallback to defaults."""
        if not time_str:
            return default_hour, default_minute
        try:
            h, m = map(int, time_str.split(':'))
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h, m
        except (ValueError, TypeError):
            pass
        logger.warning(f"Invalid time format '{time_str}'. Using default {default_hour:02d}:{default_minute:02d}.")
        return default_hour, default_minute

    def register_callbacks(self, app):
        """Registers all callbacks for this instrument."""
        from datetime import datetime, timedelta
        
        @app.callback(
            [
                Output(f"{self.instrument_id}-graph", "figure"),
                Output(f"{self.instrument_id}-status-card", "children"),
                Output(f"{self.instrument_id}-next-btn", "disabled"),
            ],
            [Input("main-update-interval", "n_intervals")]
        )
        def update_display(n):
            self.update_state()

            yaxis_range = None # Default to auto-scaling
            if self.setpoint_schedule and self.temp_history:
                min_val = min(min(self.temp_history), min(self.setpoint_schedule))
                max_val = max(max(self.temp_history), max(self.setpoint_schedule))
                y_padding = 5.0
                if min_val != max_val:
                    data_range = max_val - min_val
                    y_padding = (data_range / 0.90 - data_range) / 2
                yaxis_range = [min_val - y_padding, max_val + y_padding]

            if self.start_time and self.is_connected:
                now = datetime.fromtimestamp(time.time())
                padding = timedelta(seconds=5) # 5-second padding on the right

                elapsed_seconds = (now - self.start_time).total_seconds()

                if elapsed_seconds < 600: # For the first 10 minutes, show everything from the start
                    left_edge = self.start_time
                else: # After 10 minutes, use a sliding window
                    left_edge = now - timedelta(minutes=10)
                
                xaxis_range = [left_edge, now + padding]
            else:
                xaxis_range = None # Fallback to auto-scaling

            figure = {
                "data": [
                    {"x": list(self.time_history), "y": list(self.temp_history), "type": "scatter", "name": "Temperature", "mode": "lines"},
                    {"x": list(self.time_history), "y": list(self.setpoint_history), "type": "scatter", "name": "Setpoint", "mode": "lines", "line": {"dash": "dash"}},
                ],
                "layout": {
                    "title": f"{self.instrument_id} Temperature",
                    "xaxis": {"title": "Time", "range": xaxis_range},
                    "yaxis": {"title": "Temperature (K)", "range": yaxis_range},
                    "uirevision": "static"
                },
            }
            
            next_schedule_index = (self.schedule_index + 1) % len(self.schedule)
            next_setpoint_item = self.schedule[next_schedule_index]
            next_setpoint = next_setpoint_item["setpoint"]

            status_children = [
                dbc.CardHeader("Live Status"),
                dbc.CardBody([
                    html.H5(f"{self._state.get('temperature', 0):.4f} K", className="card-title"),
                    html.P(f"Current Setpoint: {self._state.get('setpoint', 0):.4f} K"),
                    html.P(f"Next Target: {next_setpoint:.2f} K"),
                    html.P(f"Stability Status: {'Stable' if self.is_stable else 'Waiting for Stability'}"),
                    html.P(f"Time in Stable Range: {self.stable_duration:.1f}s"),
                    html.P(f"Required Dwell Time: {self.dwell_time}s"),
                ])
            ]

            return figure, status_children, self.auto_mode

        @app.callback(
            Output(f"{self.instrument_id}-dummy-output", "children"),
            [Input(f"{self.instrument_id}-next-btn", "n_clicks")],
            prevent_initial_call=True
        )
        def on_next_setpoint(n_clicks):
            if n_clicks and not self.auto_mode:
                self._go_to_next_setpoint()
            return ""

        @app.callback(
            [
                Output(f"{self.instrument_id}-auto-switch", "value"),
                Output(f"{self.instrument_id}-auto-switch", "label"),
            ],
            [Input(f"{self.instrument_id}-auto-switch", "value")],
            prevent_initial_call=True
        )
        def on_auto_mode_toggle(is_on):
            self.auto_mode = is_on
            logger.info(f"[{self.instrument_id}] Auto mode set to: {self.auto_mode}")
            
            label = "Auto Mode: ON" if self.auto_mode else "Auto Mode: OFF"

            # When turning on auto mode, if the system is already stable, advance immediately.
            if self.auto_mode and self.is_stable:
                self._go_to_next_setpoint()

            return self.auto_mode, label

        @app.callback(
            Output(f"{self.instrument_id}-download-csv", "data"),
            Input(f"{self.instrument_id}-download-btn", "n_clicks"),
            [
                State(f"{self.instrument_id}-start-date-picker", "date"),
                State(f"{self.instrument_id}-end-date-picker", "date"),
                State(f"{self.instrument_id}-start-time-input", "value"),
                State(f"{self.instrument_id}-end-time-input", "value"),
            ],
            prevent_initial_call=True,
        )
        def export_data_to_csv(n_clicks, start_date, end_date, start_time_str, end_time_str):
            if not start_date or not end_date:
                logger.warning("Data export failed: Start or end date not selected.")
                return None

            try:
                start_hour, start_minute = self._parse_time(start_time_str, 0, 0)
                end_hour, end_minute = self._parse_time(end_time_str, 23, 59)

                start_date_dt = pd.to_datetime(start_date).replace(hour=start_hour, minute=start_minute)
                end_date_dt = pd.to_datetime(end_date).replace(hour=end_hour, minute=end_minute)

                df = pd.read_csv(self.log_file, parse_dates=['timestamp'])
                
                mask = (df['timestamp'] >= start_date_dt) & (df['timestamp'] <= end_date_dt)
                filtered_df = df.loc[mask]

                if filtered_df.empty:
                    logger.warning(f"No data found for the selected date range: {start_date_dt} to {end_date_dt}")
                    return None

                start_str = start_date_dt.strftime('%Y%m%d-%H%M')
                end_str = end_date_dt.strftime('%Y%m%d-%H%M')
                filename = f"{self.instrument_id}_data_{start_str}_to_{end_str}.csv"

                return dcc.send_data_frame(filtered_df.to_csv, filename, index=False)

            except FileNotFoundError:
                logger.error(f"Log file not found for export: {self.log_file}")
                return None
            except Exception as e:
                logger.error(f"An unexpected error occurred during data export: {e}", exc_info=True)
                return None

        
