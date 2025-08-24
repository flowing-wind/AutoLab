# File:      CryoSystem.py
# Time:      2025-08-24
# Author:    Fuuraiko
# Desc:      This file defines the physical model of the cryogenic system. 
#            It simulates temperature changes based on cooling power and environmental factors.

import numpy as np

# --- Simulation Constants ---
DEFAULT_KP = -130.0
DEFAULT_KI = -1.5
DEFAULT_KD = -600.0

class CryoSystem:
    """
    Represents the physical model of the cryogenic system.
    This class is responsible for updating the system's temperature based on various physical parameters.
    """
    def __init__(self, initial_temp=300.0):
        """
        Initializes the cryogenic system.

        Args:
            initial_temp (float): The starting temperature of the system in Kelvin.
        """
        self.temperature = initial_temp
        self.cooling_power = 0
        self.filtered_temp = initial_temp
        self.last_filtered_temp = initial_temp
        self.target_setpoint = initial_temp
        
        # PID parameters
        self.kp = DEFAULT_KP
        self.ki = DEFAULT_KI
        self.kd = DEFAULT_KD

        # Simulation parameters
        self.ambient_temp = 300.0
        self.parasitic_heat_load = 0.1
        self.heat_loss_coeff = 0.0001
        self.cooling_effect_factor = 2.0
        self.noise_level = 0.1
        self.filter_alpha = 0.2
        self.integral_sum = 0.0
        
    def update_temperature(self, target_setpoint):
        """
        Updates the system temperature for one time step.

        Args:
            target_setpoint (float): The target temperature for the current control cycle.

        Returns:
            float: The new temperature of the system after the update.
        """
        self.target_setpoint = target_setpoint
        
        # Simulate sensor reading with noise
        noise = np.random.normal(0, self.noise_level)
        current_temp_reading = self.temperature + noise
        
        # Apply a low-pass filter to the noisy reading
        self.filtered_temp = (self.filter_alpha * current_temp_reading) + (1 - self.filter_alpha) * self.filtered_temp

        # Calculate PID terms based on the filtered temperature
        error = self.target_setpoint - self.filtered_temp
        
        # Accumulate integral term with anti-windup
        if 0 < self.cooling_power < 100:
            self.integral_sum += error * 1.0
        
        # Calculate derivative term
        derivative = (self.filtered_temp - self.last_filtered_temp) / 1.0
        
        # Calculate total output and clamp it between 0 and 100
        output = (self.kp * error) + (self.ki * self.integral_sum) - (self.kd * derivative)
        control_output = max(0, min(100, output))
        
        # Apply the control output to the physical system
        self.cooling_power = control_output
        
        # Update the system temperature based on the physics model
        radiative_heat_transfer = self.heat_loss_coeff * (self.ambient_temp - self.temperature)
        active_cooling = -self.cooling_effect_factor * self.cooling_power / 100.0
        self.temperature += (radiative_heat_transfer + self.parasitic_heat_load + active_cooling) * 1.0
        self.temperature = max(0, self.temperature)
        
        # Update state variables for the next cycle
        self.last_filtered_temp = self.filtered_temp
        
        return self.temperature
    
    def get_temperature(self):
        """Returns the current temperature of the system."""
        return self.temperature
    
    def get_filtered_temperature(self):
        """Returns the filtered temperature of the system."""
        return self.filtered_temp