# File:      interface.py
# Time:      2025-09-11
# Author:    Fuuraiko, Gemini
# Desc:      Implementation of the simulated PID cooler instrument.

import time
import logging
from datetime import datetime

from src.instruments.base import UnifiedInstrument

logger = logging.getLogger(__name__)

class PIDCoolerSimulator:
    """
    A simulator for a PID-controlled cooling system.
    It simulates a second-order system for a realistic temperature curve.
    """
    def __init__(self):
        self._temperature = 300.0  # Start at room temperature (Kelvin)
        self._setpoint = 300.0
        self._velocity = 0.0  # Rate of temperature change
        self.last_update_time = time.time()

    def set_setpoint(self, temp: float):
        self._setpoint = float(temp)

    def get_temperature(self) -> float:
        current_time = time.time()
        dt = current_time - self.last_update_time
        if dt <= 0: return self._temperature
        self.last_update_time = current_time

        # PID constants for simulation
        P = 0.08  # Proportional gain
        D = 0.5   # Derivative gain (acts as damping on velocity)

        error = self._setpoint - self._temperature

        # A simple physics model (damped spring-mass system)
        # Force (cooling power) is proportional to the error
        force = error * P
        # Damping represents heat dissipation to the environment
        damping_force = self._velocity * D
        # Acceleration = (Force - Damping) / Mass (mass is assumed to be 1)
        acceleration = force - damping_force

        self._velocity += acceleration * dt
        self._temperature += self._velocity * dt

        return self._temperature


class InstrumentInterface(UnifiedInstrument):
    """
    A concrete instrument class for the simulated PID cooler.
    It inherits from UnifiedInstrument and implements the connection
    and data I/O methods for the simulator.
    """

    def connect(self) -> bool:
        """Initializes the simulator."""
        self.device = PIDCoolerSimulator()
        self.is_connected = True
        self.start_time = datetime.now()
        self.write_setpoint(self.target_setpoint) # Set initial setpoint
        logger.info(f"[{self.instrument_id}] Simulated PID Cooler initialized.")
        return True

    def disconnect(self) -> bool:
        """"Disconnects" from the simulator.""""
        self.device = None
        self.is_connected = False
        logger.info(f"[{self.instrument_id}] Simulator disconnected.")
        return True

    def read_temperature(self) -> float:
        """Gets the current temperature from the simulator."""
        if self.device:
            return self.device.get_temperature()
        return -1.0

    def write_setpoint(self, temp: float):
        """Sets a new setpoint in the simulator."""
        if self.device:
            self.device.set_setpoint(temp)