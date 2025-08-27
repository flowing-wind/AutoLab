# File:      interface.py
# Time:      2025-08-27
# Author:    Fuuraiko
# Desc:      Implementation of the simulated PID cooler instrument.

import time
from datetime import datetime
from collections import deque
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash.html as html
import logging
import math

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
        self.setpoint_schedule = config.get("setpoints", [273, 250, 220, 200])
        
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
            self.device = PIDCoolerSimulator()
            self.device.set_setpoint(self.target_setpoint)
            self.is_connected = True
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

        stability_threshold = 0.5
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
                    "uirevision": "static" # Persist zoom state
                },
            }
            
            status_children = [
                dbc.CardHeader("Live Status"),
                dbc.CardBody([
                    html.H5(f"{self._state.get('temperature', 0):.4f} K", className="card-title"),
                    html.P(f"Setpoint: {self._state.get('setpoint', 0):.4f} K"),
                    html.P(f"Status: {'Stable' if self.is_stable else 'Cooling...'}"),
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
                self.device.set_setpoint(self.target_setpoint)
                logger.info(f"[{self.instrument_id}] Setpoint changed to: {self.target_setpoint}")
            return ""
