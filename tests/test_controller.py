# File:      test_controller.py
# Time:      2025-08-24
# Author:    Fuuraiko
# Desc:      Unit tests for the TemperatureController class.

import unittest
import os
import sys

# Add the project root to the Python path to allow importing the main modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from TemperatureController import TemperatureController, DEFAULT_SETPOINTS

class TestTemperatureController(unittest.TestCase):
    """Test suite for the TemperatureController."""

    def test_initialization_with_defaults(self):
        """Test that the controller initializes correctly with default values when no config file is provided."""
        # Instantiate the controller without a config file
        controller = TemperatureController()

        # Assert that the setpoint schedule matches the default constants
        self.assertEqual(controller.setpoint_schedule, DEFAULT_SETPOINTS)

        # Assert that the initial target setpoint is the first one from the schedule
        self.assertEqual(controller.target_setpoint, DEFAULT_SETPOINTS[0])

        # Assert that the controller starts in a non-stable state
        self.assertFalse(controller.is_stable)

if __name__ == '__main__':
    unittest.main()
