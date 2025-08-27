# File:      test_pid_cooler_simulator.py
# Time:      2025-08-27
# Author:    Fuuraiko
# Desc:      Unit tests for the Simulated PID Cooler instrument.

import unittest
import time
from unittest.mock import MagicMock

from src.instruments.pid_cooler_simulator.interface import InstrumentInterface

class TestPIDCoolerSimulator(unittest.TestCase):

    def setUp(self):
        """Set up a simulated instrument for each test."""
        self.instrument_id = "SIM_COOLER_Test"
        self.config = {
            "visa_address": "SIMULATED", # This is ignored by the simulator, but good practice
            "setpoints": [280, 260, 240]
        }
        self.instrument = InstrumentInterface(self.instrument_id, self.config)

    def test_initialization(self):
        """Test that the instrument initializes with the correct config."""
        self.assertEqual(self.instrument.instrument_id, self.instrument_id)
        self.assertEqual(self.instrument.setpoint_schedule, [280, 260, 240])
        self.assertIsNone(self.instrument.device)
        self.assertFalse(self.instrument.is_connected)

    def test_connect_and_disconnect(self):
        """Test the connect and disconnect methods."""
        result = self.instrument.connect()
        self.assertTrue(result)
        self.assertTrue(self.instrument.is_connected)
        self.assertIsNotNone(self.instrument.device)
        
        # Check if it's the simulator class
        from src.instruments.pid_cooler_simulator.interface import PIDCoolerSimulator
        self.assertIsInstance(self.instrument.device, PIDCoolerSimulator)

        # Test disconnect
        result = self.instrument.disconnect()
        self.assertTrue(result)
        self.assertFalse(self.instrument.is_connected)

    def test_update_state_cooling(self):
        """Test that the state is updated and the temperature cools down."""
        self.instrument.connect()
        self.instrument.target_setpoint = 280
        self.instrument.device.set_setpoint(280)
        
        # Let the simulation run for a few steps
        initial_temp = self.instrument.get_state().get("temperature", 300)
        time.sleep(0.1) # Allow time for the simulation to advance
        self.instrument.update_state()
        new_temp = self.instrument.get_state()["temperature"]

        self.assertLess(new_temp, initial_temp)
        self.assertEqual(self.instrument.get_state()["setpoint"], 280)

    def test_setpoint_logic(self):
        """Test the logic for advancing to the next setpoint."""
        self.instrument.connect()
        
        # Initial state
        self.assertEqual(self.instrument.schedule_index, 0)
        self.assertEqual(self.instrument.target_setpoint, 280)

        # Mock the button click by directly calling the logic
        self.instrument.schedule_index = (self.instrument.schedule_index + 1) % len(self.instrument.setpoint_schedule)
        self.instrument.target_setpoint = self.instrument.setpoint_schedule[self.instrument.schedule_index]
        self.instrument.device.set_setpoint(self.instrument.target_setpoint)

        self.assertEqual(self.instrument.schedule_index, 1)
        self.assertEqual(self.instrument.target_setpoint, 260)
        # Check if the simulator's internal setpoint was updated
        self.assertEqual(self.instrument.device._setpoint, 260)

if __name__ == '__main__':
    unittest.main()
