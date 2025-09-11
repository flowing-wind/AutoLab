# File:      interface.py
# Time:      2025-09-11
# Author:    Fuuraiko, Gemini
# Desc:      Implementation of the real VISA-based temperature controller.

import pyvisa
import logging
from datetime import datetime

from src.instruments.base import UnifiedInstrument

logger = logging.getLogger(__name__)

class InstrumentInterface(UnifiedInstrument):
    """
    A concrete instrument class for a real temperature controller using VISA.
    It inherits all common logic from UnifiedInstrument and only implements
    the hardware-specific communication methods.
    """

    def connect(self) -> bool:
        """Establishes a VISA connection to the physical instrument."""
        visa_address = self.config.get("visa_address")
        if not visa_address:
            logger.error(f"[{self.instrument_id}] VISA address is not configured.")
            return False

        try:
            rm = pyvisa.ResourceManager()
            self.device = rm.open_resource(visa_address)
            # Note: Device-specific settings like baud rate might be needed here.
            # self.device.baud_rate = 115200
            identity = self.device.query('*IDN?').strip()
            logger.info(f"[{self.instrument_id}] Connected to: {identity}")

            self.is_connected = True
            self.start_time = datetime.now()
            self.write_setpoint(self.target_setpoint) # Send initial setpoint
            return True
        except pyvisa.errors.VisaIOError as e:
            logger.error(f"[{self.instrument_id}] VISA Error at {visa_address}: {e}", exc_info=True)
            self.is_connected = False
            return False

    def disconnect(self) -> bool:
        """Closes the VISA connection."""
        if self.device:
            self.device.close()
        self.is_connected = False
        logger.info(f"[{self.instrument_id}] Disconnected.")
        return True

    def read_temperature(self) -> float:
        """
        Queries the instrument for the current temperature.
        ! IMPORTANT: The command 'KRDG? A' is a placeholder.
        ! You must replace it with the correct SCPI command for your device.
        """
        try:
            # Example SCPI commands: 'MEAS:TEMP?', 'READ:TEMP?', 'KRDG? A'
            temp_str = self.device.query('KRDG? A').strip()
            return float(temp_str)
        except (pyvisa.errors.VisaIOError, ValueError) as e:
            logger.error(f"[{self.instrument_id}] Failed to read temperature: {e}")
            # Return a value that indicates error, or re-raise
            return -1.0

    def write_setpoint(self, temp: float):
        """
        Sends the command to set a new temperature setpoint.
        ! IMPORTANT: The command 'SETP 1,{temp}' is a placeholder.
        ! You must replace it with the correct SCPI command for your device.
        """
        try:
            # Example SCPI commands: 'SOUR:TEMP {temp}', 'SETP 1,{temp}'
            self.device.write(f'SETP 1,{temp}')
        except pyvisa.errors.VisaIOError as e:
            logger.error(f"[{self.instrument_id}] Failed to write setpoint: {e}")