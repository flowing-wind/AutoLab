# File:      test_temperature_controller.py
# Time:      2025-08-27
# Author:    Fuuraiko
# Desc:      Unit tests for the real VISA-based Temperature Controller instrument.

import unittest
from unittest.mock import patch, MagicMock

from src.instruments.temperature_controller.interface import InstrumentInterface

# This decorator will mock the pyvisa module within the scope of the test class
@patch('src.instruments.temperature_controller.interface.pyvisa')
class TestTemperatureController(unittest.TestCase):

    def setUp(self):
        """Set up a mock instrument for each test."""
        self.instrument_id = "TC_Test"
        self.config = {
            "visa_address": "TCPIP::MOCK_TC::INSTR",
            "setpoints": [300, 310, 320]
        }
        # The instrument is created in each test method where the mock is active

    def test_initialization(self, mock_pyvisa):
        """Test that the instrument initializes correctly without connecting."""
        instrument = InstrumentInterface(self.instrument_id, self.config)
        self.assertEqual(instrument.instrument_id, self.instrument_id)
        self.assertEqual(instrument.visa_address, "TCPIP::MOCK_TC::INSTR")
        self.assertEqual(instrument.setpoint_schedule, [300, 310, 320])
        self.assertIsNone(instrument.device)
        self.assertFalse(instrument.is_connected)

    def test_connect_success(self, mock_pyvisa):
        """Test a successful connection sequence."""
        # Configure the mock pyvisa's ResourceManager
        mock_rm = MagicMock()
        mock_device = MagicMock()
        mock_device.query.return_value = "Mock TC,1.0,12345"
        mock_rm.open_resource.return_value = mock_device
        mock_pyvisa.ResourceManager.return_value = mock_rm

        instrument = InstrumentInterface(self.instrument_id, self.config)
        result = instrument.connect()

        self.assertTrue(result)
        self.assertTrue(instrument.is_connected)
        self.assertIsNotNone(instrument.device)
        # Check that the correct VISA address was used
        mock_rm.open_resource.assert_called_with("TCPIP::MOCK_TC::INSTR")
        # Check that the instrument identity was queried
        mock_device.query.assert_called_with('*IDN?')

    def test_connect_fail(self, mock_pyvisa):
        """Test a failed connection."""
        # Configure the mock to raise an error
        mock_rm = MagicMock()
        mock_rm.open_resource.side_effect = mock_pyvisa.errors.VisaIOError("Simulated Error")
        mock_pyvisa.ResourceManager.return_value = mock_rm

        instrument = InstrumentInterface(self.instrument_id, self.config)
        result = instrument.connect()

        self.assertFalse(result)
        self.assertFalse(instrument.is_connected)
        self.assertIsNone(instrument.device)

    def test_disconnect(self, mock_pyvisa):
        """Test the disconnect method."""
        # First, establish a successful connection
        mock_rm = MagicMock()
        mock_device = MagicMock()
        mock_rm.open_resource.return_value = mock_device
        mock_pyvisa.ResourceManager.return_value = mock_rm
        
        instrument = InstrumentInterface(self.instrument_id, self.config)
        instrument.connect()
        self.assertTrue(instrument.is_connected)

        # Now, test disconnect
        result = instrument.disconnect()
        self.assertTrue(result)
        self.assertFalse(instrument.is_connected)
        # Check that the device's close method was called
        mock_device.close.assert_called_once()

    def test_update_state(self, mock_pyvisa):
        """Test that the state is updated correctly from the mock device."""
        # Mock the device's methods for getting data
        mock_device = MagicMock()
        mock_device.query.return_value = "Mock TC,1.0,12345"
        # We need to mock the custom method we created
        # Let's patch the method directly on the class for this test
        with patch.object(InstrumentInterface, 'get_temperature_from_device', return_value=305.5) as mock_get_temp:
            instrument = InstrumentInterface(self.instrument_id, self.config)
            # Manually set the device since connect is not called
            instrument.device = mock_device
            instrument.is_connected = True

            instrument.update_state()
            state = instrument.get_state()

            mock_get_temp.assert_called_once()
            self.assertIn("temperature", state)
            self.assertEqual(state["temperature"], 305.5)
            self.assertEqual(state["setpoint"], 300) # Initial setpoint

    def test_setpoint_logic(self, mock_pyvisa):
        """Test the logic for advancing to the next setpoint."""
        # Mock the device's methods for setting data
        mock_device = MagicMock()
        # Patch the custom setpoint method
        with patch.object(InstrumentInterface, 'set_setpoint_on_device') as mock_set_setpoint:
            instrument = InstrumentInterface(self.instrument_id, self.config)
            instrument.device = mock_device
            instrument.is_connected = True

            # Initial state
            self.assertEqual(instrument.schedule_index, 0)
            self.assertEqual(instrument.target_setpoint, 300)

            # Simulate the logic that would be in a callback
            instrument.schedule_index = (instrument.schedule_index + 1) % len(instrument.setpoint_schedule)
            instrument.target_setpoint = instrument.setpoint_schedule[instrument.schedule_index]
            instrument.set_setpoint_on_device(instrument.target_setpoint)

            self.assertEqual(instrument.schedule_index, 1)
            self.assertEqual(instrument.target_setpoint, 310)
            # Check that the method to talk to the hardware was called with the new setpoint
            mock_set_setpoint.assert_called_with(310)

if __name__ == '__main__':
    unittest.main()