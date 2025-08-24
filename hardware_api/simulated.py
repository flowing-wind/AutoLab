# File:      simulated.py
# Time:      2025-08-24
# Author:    Fuuraiko
# Desc:      The simulated implementation of the temperature bridge.

from .base import AbstractTemperatureBridge
from .CryoSystem import CryoSystem

class SimulatedBridge(AbstractTemperatureBridge):
    """
    A simulated temperature bridge that uses the CryoSystem model to generate
    temperature data. This allows for full application testing without any hardware.
    """

    def __init__(self, **kwargs):
        """Initializes the simulated bridge and the underlying CryoSystem."""
        super().__init__(**kwargs)
        self.cryo_system = CryoSystem()

    def get_temperature(self) -> float:
        """Gets the current temperature from the simulation."""
        return self.cryo_system.get_temperature()

    def update(self, target_setpoint: float) -> float:
        """
        Advances the simulation by one time step.

        Args:
            target_setpoint (float): The desired target temperature for the simulation.

        Returns:
            float: The new simulated temperature.
        """
        return self.cryo_system.update_temperature(target_setpoint)
