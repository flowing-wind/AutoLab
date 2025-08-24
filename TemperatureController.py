# File:      TemperatureController.py
# Time:      2025-08-24
# Author:    Fuuraiko
# Desc:      This file defines the main controller for the temperature regulation system.
#            It manages the PID control loop, handles setpoint scheduling, and logs system events.

import CryoSystem
import csv
import time
import datetime
import logging
import sys
import os

# ==================== Configuration ====================
DEBUG_MODE = True  # Set to False to use real instruments, True for simulation mode

# ==================== Logging Setup ====================
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler and set level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

log_dir = "./log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create file handler and set level
file_handler = logging.FileHandler(f"./log/controller_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ==================== Default Parameters & CSV Reader ====================

DEFAULT_SETPOINTS = [300, 298, 295]
DEFAULT_STABLE_TIMES = [10, 10, 10]

def read_schedule_from_csv(filename):
    """Reads the setpoint schedule and corresponding stability times from a CSV file."""
    setpoints = DEFAULT_SETPOINTS.copy()
    stable_times = DEFAULT_STABLE_TIMES.copy()
    
    try:
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2 and row[0].lower() == 'setpoints':
                    try:
                        setpoints = [float(x.strip()) for x in row[1:] if x.strip()]
                    except ValueError:
                        logger.warning(f"Could not parse setpoint schedule: {row[1:]}. Using default values.")
                
                elif len(row) >= 2 and row[0].lower() == 'stable_times':
                    try:
                        stable_times = [float(x.strip()) for x in row[1:] if x.strip()]
                    except ValueError:
                        logger.warning(f"Could not parse stability times: {row[1:]}. Using default values.")
    
    except FileNotFoundError:
        logger.warning(f"File {filename} not found. Using default parameters.")
    except Exception as e:
        logger.warning(f"Error reading CSV file: {e}. Using default parameters.")
    
    if len(stable_times) != len(setpoints):
        logger.warning("Mismatch between number of setpoints and stable times. Using default time for all.")
        stable_times = [DEFAULT_STABLE_TIMES[0]] * len(setpoints)
    
    return setpoints, stable_times


# ==================== Temperature Controller Class ====================
class TemperatureController:
    """Manages the PID control loop and setpoint schedule."""
    def __init__(self, config_file=None):
        """
        Initializes the Temperature Controller.

        Args:
            config_file (str, optional): Path to the CSV configuration file. Defaults to None.
        """
        if config_file:
            self.config_file = config_file
            self.setpoint_schedule, self.setpoint_stable_times = read_schedule_from_csv(config_file)
        else:
            self.setpoint_schedule = DEFAULT_SETPOINTS.copy()
            self.setpoint_stable_times = DEFAULT_STABLE_TIMES.copy()
        
        self.cryo_system = CryoSystem.CryoSystem()
        self.temperature = self.cryo_system.get_temperature()
        self.integral_sum = 0.0
        self.schedule_index = 0
        self.target_setpoint = self.setpoint_schedule[self.schedule_index]
        self.current_stable_time = self.setpoint_stable_times[self.schedule_index]
        self.stabilization_start_time = None
        
        # Flags
        self.is_stable = False
        self.update_requested = False
        self.is_debug_mode = True  # Default to simulation mode

        logger.info(f"Controller initialized. Target: {self.target_setpoint}K, Stability time: {self.current_stable_time}s")

    def set_debug_mode(self, is_debug):
        """Sets the debug mode for the controller."""
        self.is_debug_mode = is_debug

    def get_temperature(self):
        """Gets the current temperature."""
        return self.temperature

    def get_setpoint(self):
        """Gets the current target setpoint."""
        return self.target_setpoint

    def get_stable_status(self):
        """Gets the stability status flag."""
        return self.is_stable
    
    def get_schedule_index(self):
        """Gets the current index in the setpoint schedule."""
        return self.schedule_index

    def request_update(self):
        """Requests a switch to the next setpoint if the system is stable."""
        if self.is_debug_mode:
            self.update_requested = True
            logger.info("Update requested by user. Will switch to next setpoint when stable.")
        else:
            # Handle real instrument logic here
            pass

    def _update_target_setpoint(self, current_time, stability_threshold=0.5):
        """Checks for stability and updates the target setpoint if conditions are met."""
        is_last_setpoint = self.schedule_index >= len(self.setpoint_schedule) - 1

        if self._is_temperature_stable(self.target_setpoint, stability_threshold):
            if self.stabilization_start_time is None:
                self.stabilization_start_time = current_time
                logger.info(f"Temperature has entered stability range around {self.target_setpoint}K. Starting timer.")
            
            elif (current_time - self.stabilization_start_time) >= self.current_stable_time:
                if not self.is_stable:
                    self.is_stable = True
                    logger.info(f"System is now stable at {self.target_setpoint}K.")
                    self._on_stabilized()
                
                if self.update_requested:
                    if is_last_setpoint:
                        logger.info("All setpoints have been processed.")
                        # Optional: Add logic to end the process or loop
                    else:
                        self.schedule_index += 1
                        self.target_setpoint = self.setpoint_schedule[self.schedule_index]
                        self.current_stable_time = self.setpoint_stable_times[self.schedule_index]
                        logger.info(f"Switching to next setpoint: {self.target_setpoint}K, Stability time: {self.current_stable_time}s")

                        # Reset for next setpoint
                        self.stabilization_start_time = None
                        self.integral_sum = 0.0
                        self.is_stable = False
                        self.update_requested = False
        else:
            if self.stabilization_start_time is not None:
                logger.info(f"Temperature left stability range. Resetting timer. Current temp: {self.temperature:.4f}K")
            self.stabilization_start_time = None
            self.is_stable = False
    
    def _on_stabilized(self):
        """Placeholder for actions to be performed once the temperature is stable."""
        logger.info("Executing post-stabilization measurement/action.")
        pass

    def _is_temperature_stable(self, target_temp, threshold=0.5):
        """Checks if the current temperature is within the threshold of the target."""
        return abs(self.temperature - target_temp) <= threshold

    def update(self):
        """Executes one full control loop cycle."""
        current_time = time.time()
        self.temperature = self.cryo_system.update_temperature(self.target_setpoint)
        self._update_target_setpoint(current_time)
