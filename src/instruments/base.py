# File:      base.py
# Time:      2025-08-27
# Author:    Fuuraiko
# Desc:      Defines the abstract base class for all instrument modules.

from abc import ABC, abstractmethod
from typing import Dict, Any

class Instrument(ABC):
    """
    Abstract base class for an instrument. It defines a common interface
    for all instrument modules in the system.
    """

    def __init__(self, instrument_id: str, config: Dict[str, Any]):
        """
        Initializes the instrument.

        Args:
            instrument_id (str): The unique identifier for the instrument.
            config (Dict[str, Any]): A dictionary containing configuration
                                     parameters for the instrument, loaded
                                     from the main config file.
        """
        self.instrument_id = instrument_id
        self.config = config
        self._state = {}

    @abstractmethod
    def connect(self) -> bool:
        """
        Establishes connection to the physical instrument.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnects from the physical instrument.

        Returns:
            bool: True if disconnection is successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_layout(self) -> Any:
        """
        Returns the Dash layout components for this instrument.
        The layout should be a self-contained component that can be
        embedded into the main application UI.

        Returns:
            Any: A Dash component or a list of Dash components.
        """
        pass

    @abstractmethod
    def register_callbacks(self, app: Any):
        """
        Registers all Dash callbacks required for the instrument's UI
        to function.

        Args:
            app (Any): The main Dash application instance.
        """
        pass

    @abstractmethod
    def update_state(self):
        """
        Reads the current state from the physical instrument and updates
        the internal state dictionary. This method is called periodically
        by the main application loop.
        """
        pass

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the last known state of the instrument.

        Returns:
            Dict[str, Any]: A dictionary representing the instrument's state.
        """
        return self._state
