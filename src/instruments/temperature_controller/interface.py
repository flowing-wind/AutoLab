# File:      interface.py
# Time:      2025-08-27
# Author:    Fuuraiko
# Desc:      Implementation of the real VISA-based temperature controller instrument.

import time
import pyvisa
from collections import deque
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash.html as html
import logging

from src.instruments.base import Instrument

# Get the logger instance from the main app
logger = logging.getLogger(__name__)

class InstrumentInterface(Instrument):
    """
    The concrete implementation for a real temperature controller using VISA.
    """
    def __init__(self, instrument_id: str, config: dict):
        super().__init__(instrument_id, config)
        self.visa_address = config.get("visa_address")
        if not self.visa_address:
            raise ValueError("VISA address is required for this instrument.")
            
        self.setpoint_schedule = config.get("setpoints", [300])
        
        # Instrument state
        self.device = None
        self.is_connected = False
        self.schedule_index = 0
        self.target_setpoint = self.setpoint_schedule[0]
        self.is_stable = False
        self.stabilization_start_time = None
        self.stable_duration = 0
        
        # Data history for plotting
        self.time_history = deque(maxlen=500)
        self.temp_history = deque(maxlen=500)
        self.setpoint_history = deque(maxlen=500)

    def connect(self) -> bool:
        """Establishes connection to the instrument."""
        try:
            rm = pyvisa.ResourceManager()
            self.device = rm.open_resource(self.visa_address)
            self.device.baud_rate = 115200
            # You might need to configure the device here, e.g., baud rate
            # This query is a standard SCPI command to identify the instrument.
            identity = self.device.query('*IDN?').strip()
            logger.info(f"Connected to {identity}")
            
            self.is_connected = True
            # Set the initial setpoint on the device
            self.set_setpoint_on_device(self.target_setpoint)
            return True
        except pyvisa.errors.VisaIOError as e:
            logger.error(f"VISA Error connecting to {self.instrument_id} at {self.visa_address}: {e}", exc_info=True)
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Generic error connecting to {self.instrument_id}: {e}", exc_info=True)
            self.is_connected = False
            return False

    def disconnect(self) -> bool:
        """Disconnects from the instrument."""
        try:
            if self.device:
                self.device.close()
            self.is_connected = False
            logger.info(f"Disconnected from {self.instrument_id}.")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from {self.instrument_id}: {e}", exc_info=True)
            return False

    def get_temperature_from_device(self) -> float:
        """
        Queries the instrument for the current temperature.

        !! This is a placeholder !!
        You must replace the command with the correct SCPI command for your specific device.
        
        Returns:
            float: The current temperature.
        """
        # Example: return float(self.device.query('MEAS:TEMP?'))
        return float(self.device.query('KRDG? A'))
        # logger.warning("Using dummy temperature value. Implement `get_temperature_from_device`.")
        # return 300.0 + (time.time() % 10 - 5) # Dummy value

    def set_setpoint_on_device(self, temp: float):
        """
        Sends the command to the instrument to set a new temperature setpoint.

        !! This is a placeholder !!
        You must replace the command with the correct SCPI command for your specific device.

        Args:
            temp (float): The target temperature.
        """
        # Example: self.device.write(f'SOUR:TEMP {temp}')
        self.device.write(f'SETP 1,{temp}')
        # logger.warning(f"Using dummy setpoint. Implement `set_setpoint_on_device` for {temp:.2f}K.")
        # pass

    def update_state(self):
        """
        Reads data from the instrument and updates the internal state.
        """
        if not self.is_connected:
            return

        current_temp = self.get_temperature_from_device()
        
        current_time = time.time()
        self.time_history.append(current_time)
        self.temp_history.append(current_temp)
        self.setpoint_history.append(self.target_setpoint)

        stability_threshold = 1.0
        if abs(current_temp - self.target_setpoint) <= stability_threshold:
            if self.stabilization_start_time is None:
                self.stabilization_start_time = current_time
            self.stable_duration = current_time - self.stabilization_start_time
            required_stable_time = 5 
            if self.stable_duration >= required_stable_time:
                self.is_stable = True
        else:
            self.stabilization_start_time = None
            self.stable_duration = 0
            self.is_stable = False
            
        self._state = {
            "temperature": current_temp,
            "setpoint": self.target_setpoint,
            "is_stable": self.is_stable,
            "stable_duration": self.stable_duration,
            "is_connected": self.is_connected,
            "schedule_index": self.schedule_index
        }

    def get_layout(self):
        """
        Returns the Dash layout for this instrument.
        """
        from . import layout
        return layout.get_layout(self.instrument_id, self)

    def register_callbacks(self, app):
        """Registers all callbacks for this instrument."""
        
        @app.callback(
            [
                Output(f"{self.instrument_id}-graph", "figure"),
                Output(f"{self.instrument_id}-status-card", "children"),
            ],
            [Input("main-update-interval", "n_intervals")]
        )
        def update_display(n):
            self.update_state()

            figure = {
                "data": [
                    {"x": list(self.time_history), "y": list(self.temp_history), "type": "scatter", "name": "Temperature"},
                    {"x": list(self.time_history), "y": list(self.setpoint_history), "type": "scatter", "name": "Setpoint", "mode": "lines", "line": {"dash": "dash"}},
                ],
                "layout": {
                    "title": f"{self.instrument_id} Temperature",
                    "xaxis": {"title": "Time"},
                    "yaxis": {"title": "Temperature (K)"},
                    "uirevision": "static"
                },
            }
            
            status_children = [
                dbc.CardHeader("Live Status"),
                dbc.CardBody([
                    html.H5(f"{self._state.get('temperature', 0):.4f} K", className="card-title"),
                    html.P(f"Setpoint: {self._state.get('setpoint', 0):.4f} K"),
                    html.P(f"Status: {'Stable' if self.is_stable else 'Unstable'}"),
                    html.P(f"Time Stable: {self.stable_duration:.1f}s"),
                ])
            ]

            return figure, status_children

        @app.callback(
            Output(f"{self.instrument_id}-dummy-output", "children"),
            [Input(f"{self.instrument_id}-next-btn", "n_clicks")],
        )
        def on_next_setpoint(n_clicks):
            if n_clicks:
                self.schedule_index = (self.schedule_index + 1) % len(self.setpoint_schedule)
                self.target_setpoint = self.setpoint_schedule[self.schedule_index]
                self.set_setpoint_on_device(self.target_setpoint)
                logger.info(f"[{self.instrument_id}] Setpoint changed to: {self.target_setpoint}")
            return ""
