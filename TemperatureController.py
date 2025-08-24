# File:      TemperatureController.py
# Time:      2025-08-24
# Author:    Fuuraiko
# Desc:      This file defines the main controller for the temperature regulation system.
#            It manages the PID control loop, handles setpoint scheduling, and logs system events.

import time
import datetime
import logging
import sys
import os
import csv

# Import the bridge implementations
from hardware_api.simulated import SimulatedBridge
from hardware_api.visa import VisaBridge

# ==================== Configuration ====================
# This flag now acts as a switch for the factory in the controller
DEBUG_MODE = True  

# ==================== Logging Setup ====================
# (Logging setup remains the same as before)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
log_dir = "./log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
file_handler = logging.FileHandler(f"./log/controller_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ==================== Default Parameters & CSV Reader ====================
DEFAULT_SETPOINTS = [300, 298, 295]
DEFAULT_STABLE_TIMES = [10, 10, 10]

def read_schedule_from_csv(filename):
    # (Function remains the same as before)
    setpoints = DEFAULT_SETPOINTS.copy()
    stable_times = DEFAULT_STABLE_TIMES.copy()
    try:
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2 and row[0].lower() == 'setpoints':
                    setpoints = [float(x.strip()) for x in row[1:] if x.strip()]
                elif len(row) >= 2 and row[0].lower() == 'stable_times':
                    stable_times = [float(x.strip()) for x in row[1:] if x.strip()]
    except FileNotFoundError:
        logger.warning(f"File {filename} not found. Using default parameters.")
    return setpoints, stable_times

# ==================== Temperature Controller Class ====================
class TemperatureController:
    """Manages the PID control loop and setpoint schedule via a hardware bridge."""
    def __init__(self, config_file=None, is_debug_mode=True):
        """
        Initializes the Temperature Controller.

        Args:
            config_file (str, optional): Path to the CSV configuration file.
            is_debug_mode (bool): If True, uses the SimulatedBridge. Otherwise, uses the VisaBridge.
        """
        # --- Hardware Bridge Factory ---
        self.is_debug_mode = is_debug_mode
        if self.is_debug_mode:
            self.bridge = SimulatedBridge()
            logger.info("Initialized with SimulatedHardwareBridge.")
        else:
            # When using real hardware, you might pass connection details here
            self.bridge = VisaBridge(visa_address="ASRL3::INSTR")
            logger.info("Initialized with VisaHardwareBridge.")

        # --- Schedule Loading ---
        if config_file:
            self.config_file = config_file
            self.setpoint_schedule, self.setpoint_stable_times = read_schedule_from_csv(config_file)
        else:
            self.setpoint_schedule = DEFAULT_SETPOINTS.copy()
            self.setpoint_stable_times = DEFAULT_STABLE_TIMES.copy()
        
        # --- State Initialization ---
        self.temperature = self.bridge.get_temperature()
        self.schedule_index = 0
        self.target_setpoint = self.setpoint_schedule[self.schedule_index]
        self.current_stable_time = self.setpoint_stable_times[self.schedule_index]
        self.stabilization_start_time = None
        
        # --- Flags ---
        self.is_stable = False
        self.update_requested = False

        logger.info(f"Controller initialized. Target: {self.target_setpoint}K, Stability time: {self.current_stable_time}s")

    def get_temperature(self):
        return self.temperature

    def get_setpoint(self):
        return self.target_setpoint

    def get_stable_status(self):
        return self.is_stable
    
    def get_schedule_index(self):
        return self.schedule_index

    def request_update(self):
        self.update_requested = True
        logger.info("Update requested by user. Will switch to next setpoint when stable.")

    def _update_target_setpoint(self, current_time, stability_threshold=0.5):
        # This method's logic remains largely the same, as it's about schedule management
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
                    else:
                        self.schedule_index += 1
                        self.target_setpoint = self.setpoint_schedule[self.schedule_index]
                        self.current_stable_time = self.setpoint_stable_times[self.schedule_index]
                        logger.info(f"Switching to next setpoint: {self.target_setpoint}K, Stability time: {self.current_stable_time}s")
                        self.stabilization_start_time = None
                        self.is_stable = False
                        self.update_requested = False
        else:
            if self.stabilization_start_time is not None:
                logger.info(f"Temperature left stability range. Resetting timer. Current temp: {self.temperature:.4f}K")
            self.stabilization_start_time = None
            self.is_stable = False
    
    def _on_stabilized(self):
        logger.info("Executing post-stabilization measurement/action.")
        pass

    def _is_temperature_stable(self, target_temp, threshold=0.5):
        return abs(self.temperature - target_temp) <= threshold

    def update(self):
        """Executes one full control loop cycle using the hardware bridge."""
        current_time = time.time()
        # The core update call is now delegated to the bridge
        self.temperature = self.bridge.update(self.target_setpoint)
        self._update_target_setpoint(current_time)