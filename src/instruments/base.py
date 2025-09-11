# File:      base.py
# Time:      2025-09-11
# Author:    Fuuraiko, Gemini
# Desc:      Defines the unified base class for all instrument modules,
#            containing shared logic for UI, state management, and data handling.

import os
import csv
import time
import pandas as pd
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import logging

logger = logging.getLogger(__name__)

class UnifiedInstrument(ABC):
    """
    A unified, abstract base class for instruments.

    This class provides a complete, shared structure for handling:
    - Connection and state management.
    - Automatic schedule execution (setpoint stepping).
    - Data history for plotting.
    - CSV data logging with automatic trimming.
    - A standardized Dash UI layout.
    - All required Dash callbacks for the UI.

    Concrete instrument classes must implement the abstract methods:
    - connect()
    - disconnect()
    - read_temperature() -> float
    - write_setpoint(temp: float)
    """

    def __init__(self, instrument_id: str, config: Dict[str, Any]):
        """
        Initializes the instrument with shared logic.
        """
        self.instrument_id = instrument_id
        self.config = config

        # --- Schedule and Setpoint ---
        self.schedule = config.get("schedule", [{"setpoint": 300, "dwell_time": 5}])
        self.setpoint_schedule = [item["setpoint"] for item in self.schedule]
        self.schedule_index = 0
        self.target_setpoint = self.schedule[0]["setpoint"]
        self.dwell_time = self.schedule[0]["dwell_time"]

        # --- State Management ---
        self.is_connected = False
        self.is_stable = False
        self.stabilization_start_time = None
        self.stable_duration = 0
        self.start_time = None
        self.auto_mode = True
        self._state: Dict[str, Any] = {}

        # --- Data History for Plotting ---
        self.time_history = deque(maxlen=600)  # Approx 10 minutes of data at 1s interval
        self.temp_history = deque(maxlen=600)
        self.setpoint_history = deque(maxlen=600)

        # --- Data Logging ---
        self.log_dir = "log"
        self.log_file = os.path.join(self.log_dir, f"{self.instrument_id}_data.csv")
        self.log_max_size_mb = 5
        self.log_write_interval = 100  # Check file size every 100 writes
        self.log_write_counter = 0
        self._last_logged_second = None
        self._init_log_file()

    # --- Abstract Methods for Concrete Implementations ---

    @abstractmethod
    def connect(self) -> bool:
        """Establishes connection to the physical/simulated instrument."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnects from the instrument."""
        pass

    @abstractmethod
    def read_temperature(self) -> float:
        """Reads the current temperature from the instrument."""
        pass

    @abstractmethod
    def write_setpoint(self, temp: float):
        """Sends the setpoint to the instrument."""
        pass

    # --- Shared Core Logic ---

    def update_state(self):
        """
        Reads data from the instrument, updates state, and handles schedule logic.
        This is the main periodic update method.
        """
        if not self.is_connected:
            return

        current_temp = self.read_temperature()
        current_time = time.time()
        datetime_obj = datetime.fromtimestamp(current_time)

        # Update data for plotting
        self.time_history.append(datetime_obj)
        self.temp_history.append(current_temp)
        self.setpoint_history.append(self.target_setpoint)

        # Log data to file
        self._log_data(datetime_obj, current_temp, self.target_setpoint)

        # Check for temperature stability
        stability_threshold = self.config.get("stability_threshold", 1.0)
        if abs(current_temp - self.target_setpoint) <= stability_threshold:
            if self.stabilization_start_time is None:
                self.stabilization_start_time = current_time
            self.stable_duration = current_time - self.stabilization_start_time

            # If stable for the required duration, advance the schedule if in auto mode
            if not self.is_stable and self.stable_duration >= self.dwell_time:
                self.is_stable = True
                if self.auto_mode:
                    self._go_to_next_setpoint()
        else:
            # Reset stability if temperature moves out of range
            self.stabilization_start_time = None
            self.stable_duration = 0
            self.is_stable = False

        # Update internal state dictionary
        self._state = {
            "temperature": current_temp,
            "setpoint": self.target_setpoint,
            "is_stable": self.is_stable,
            "stable_duration": self.stable_duration,
            "is_connected": self.is_connected,
            "schedule_index": self.schedule_index,
            "dwell_time": self.dwell_time,
        }

    def get_state(self) -> Dict[str, Any]:
        """Returns the last known state of the instrument."""
        return self._state

    def _go_to_next_setpoint(self):
        """Advances to the next setpoint in the schedule."""
        self.schedule_index = (self.schedule_index + 1) % len(self.schedule)
        current_schedule_item = self.schedule[self.schedule_index]
        self.target_setpoint = current_schedule_item["setpoint"]
        self.dwell_time = current_schedule_item["dwell_time"]
        self.write_setpoint(self.target_setpoint)

        # Reset stability state
        self.is_stable = False
        self.stabilization_start_time = None
        self.stable_duration = 0
        logger.info(f"[{self.instrument_id}] Setpoint changed to: {self.target_setpoint} K, Dwell Time: {self.dwell_time}s")

    # --- Data Logging ---

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

    def _log_data(self, timestamp: datetime, temperature: float, setpoint: float):
        """Appends a data row to the CSV log, ensuring one entry per second."""
        current_second_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        if self._last_logged_second == current_second_str:
            return  # Skip if already logged this second

        try:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([current_second_str, temperature, setpoint])
            self._last_logged_second = current_second_str

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
                num_rows_to_drop = int(len(df) * 0.25)
                df_trimmed = df.iloc[num_rows_to_drop:]
                df_trimmed.to_csv(self.log_file, index=False)
        except (IOError, pd.errors.EmptyDataError) as e:
            logger.error(f"Error trimming log file {self.log_file}: {e}")

    # --- Dash UI and Callbacks ---

    def get_layout(self) -> dbc.Container:
        """Generates the standardized Dash UI layout for the instrument."""
        return dbc.Container(
            fluid=True,
            className="instrument-card mb-4",
            children=[
                html.Div(id=f"{self.instrument_id}-dummy-output", style={'display': 'none'}),
                dcc.Download(id=f'{self.instrument_id}-download-csv'),
                dbc.Row([
                    dbc.Col(dcc.Graph(id=f"{self.instrument_id}-graph", animate=True, config={'scrollZoom': True, 'displaylogo': False}), width=8),
                    dbc.Col([
                        dbc.Card(id=f"{self.instrument_id}-status-card", color="light", className="mb-3"),
                        dbc.Card(dbc.CardBody([
                            dbc.Button("Next Setpoint", id=f"{self.instrument_id}-next-btn", color="primary", className="me-2"),
                            dbc.Switch(id=f"{self.instrument_id}-auto-switch", label="Auto Mode: ON", value=True, className="mt-2"),
                        ]), color="light", className="mb-3"),
                        dbc.Card([
                            dbc.CardHeader("Export Data"),
                            dbc.CardBody([
                                dcc.DatePickerSingle(id=f'{self.instrument_id}-start-date-picker', placeholder='Start Date', className="w-100 mb-2"),
                                dcc.Input(id=f'{self.instrument_id}-start-time-input', type='text', placeholder='Start Time (HH:MM)', className="w-100 mb-2"),
                                dcc.DatePickerSingle(id=f'{self.instrument_id}-end-date-picker', placeholder='End Date', className="w-100 mb-2"),
                                dcc.Input(id=f'{self.instrument_id}-end-time-input', type='text', placeholder='End Time (HH:MM)', className="w-100 mb-2"),
                                dbc.Button("Download CSV", id=f'{self.instrument_id}-download-btn', color="success", className="w-100"),
                            ])
                        ], color="light"),
                    ], width=4)
                ])
            ]
        )

    def register_callbacks(self, app: Any):
        """Registers all Dash callbacks for the instrument's UI."""

        @app.callback(
            [
                Output(f"{self.instrument_id}-graph", "figure"),
                Output(f"{self.instrument_id}-status-card", "children"),
                Output(f"{self.instrument_id}-next-btn", "disabled"),
            ],
            [Input("main-update-interval", "n_intervals")]
        )
        def update_display(_):
            self.update_state()

            # Define Y-axis range for the graph
            y_padding = 5.0
            if self.setpoint_schedule and self.temp_history:
                min_val = min(min(self.temp_history), min(self.setpoint_schedule))
                max_val = max(max(self.temp_history), max(self.setpoint_schedule))
                if min_val != max_val:
                    data_range = max_val - min_val
                    y_padding = (data_range / 0.90 - data_range) / 2
                yaxis_range = [min_val - y_padding, max_val + y_padding]
            else:
                yaxis_range = None

            # Define X-axis range (sliding window)
            if self.start_time and self.is_connected:
                now = datetime.fromtimestamp(time.time())
                if (now - self.start_time).total_seconds() < 600:
                    left_edge = self.start_time
                else:
                    left_edge = now - timedelta(minutes=10)
                xaxis_range = [left_edge, now + timedelta(seconds=5)]
            else:
                xaxis_range = None

            figure = {
                "data": [
                    {"x": list(self.time_history), "y": list(self.temp_history), "type": "scatter", "name": "Temperature", "mode": "lines"},
                    {"x": list(self.time_history), "y": list(self.setpoint_history), "type": "scatter", "name": "Setpoint", "mode": "lines", "line": {"dash": "dash"}},
                ],
                "layout": {
                    "title": f"{self.instrument_id} Temperature",
                    "xaxis": {"title": "Time", "range": xaxis_range},
                    "yaxis": {"title": "Temperature (K)", "range": yaxis_range},
                    "uirevision": "static" # Persist zoom level
                },
            }

            next_setpoint = self.schedule[(self.schedule_index + 1) % len(self.schedule)]["setpoint"]
            status_children = [
                dbc.CardHeader("Live Status"),
                dbc.CardBody([
                    html.H5(f"{self._state.get('temperature', 0):.4f} K", className="card-title"),
                    html.P(f"Current Setpoint: {self._state.get('setpoint', 0):.4f} K"),
                    html.P(f"Next Target: {next_setpoint:.2f} K"),
                    html.P(f"Stability: {'Stable' if self.is_stable else 'Waiting'} ({self.stable_duration:.1f}s / {self.dwell_time}s)"),
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
            Output(f"{self.instrument_id}-auto-switch", "label"),
            [Input(f"{self.instrument_id}-auto-switch", "value")],
            prevent_initial_call=True
        )
        def on_auto_mode_toggle(is_on):
            self.auto_mode = is_on
            logger.info(f"[{self.instrument_id}] Auto mode set to: {self.auto_mode}")
            if self.auto_mode and self.is_stable:
                self._go_to_next_setpoint()
            return "Auto Mode: ON" if self.auto_mode else "Auto Mode: OFF"

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
                return None

            def _parse_time(time_str, default_hour, default_minute):
                if time_str:
                    try:
                        h, m = map(int, time_str.split(':'))
                        if 0 <= h <= 23 and 0 <= m <= 59:
                            return h, m
                    except (ValueError, TypeError):
                        pass
                return default_hour, default_minute

            try:
                start_h, start_m = _parse_time(start_time_str, 0, 0)
                end_h, end_m = _parse_time(end_time_str, 23, 59)

                start_dt = pd.to_datetime(start_date).replace(hour=start_h, minute=start_m)
                end_dt = pd.to_datetime(end_date).replace(hour=end_h, minute=end_m)

                df = pd.read_csv(self.log_file, parse_dates=['timestamp'])
                mask = (df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)
                filtered_df = df.loc[mask]

                if filtered_df.empty:
                    return None

                filename = f"{self.instrument_id}_data_{start_dt.strftime('%Y%m%d%H%M')}_to_{end_dt.strftime('%Y%m%d%H%M')}.csv"
                return dcc.send_data_frame(filtered_df.to_csv, filename, index=False)
            except Exception as e:
                logger.error(f"Error during data export: {e}", exc_info=True)
                return None