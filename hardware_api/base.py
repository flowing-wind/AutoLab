# File:      base.py
# Time:      2025-08-24
# Author:    Fuuraiko
# Desc:      Defines the abstract base class for all hardware or simulation bridges.

from abc import ABC, abstractmethod

class AbstractTemperatureBridge(ABC):
    """
    An abstract base class that defines the standard interface for interacting
    with a temperature control system, whether it's a simulation or real hardware.
    The TemperatureController will use this interface to remain decoupled from the
    specifics of the underlying hardware.
    """

    @abstractmethod
    def __init__(self, **kwargs):
        """Initializes the bridge. Can accept any number of configuration parameters."""
        pass

    @abstractmethod
    def get_temperature(self) -> float:
        """Gets the current temperature from the system."""
        pass

    @abstractmethod
    def update(self, target_setpoint: float) -> float:
        """
        Executes one update cycle.

        For a simulation, this advances the simulation by one time step.
        For real hardware, this would typically involve reading the current temperature
        and sending a new power level based on a PID calculation.

        Args:
            target_setpoint (float): The desired target temperature.

        Returns:
            float: The new temperature after the update cycle.
        """
        pass
