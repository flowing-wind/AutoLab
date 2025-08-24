# Lab-Protocol: Temperature Control System

## Introduction

This project is a temperature control and monitoring application designed for laboratory environments. It provides a graphical user interface to visualize and manage a cryogenic system's temperature in real-time. The application can run in a simulation mode for development and testing, or be connected to live instruments.

The core logic is built to be robust and asynchronous, ensuring the user interface remains responsive while the controller manages temperature setpoints and stability in a background process.

## Features

- **Real-Time Visualization**: Plots live temperature and setpoint data on a graph.
- **Setpoint Scheduling**: Load a sequence of target temperatures and required stabilization times from an external `config.csv` file.
- **Stability Control**: Automatically detects when the system temperature has stabilized within a given threshold for a specified time.
- **Asynchronous Operations**: The control loop runs in a separate thread to keep the GUI from freezing.
- **Simulation Mode**: A built-in physics model (`CryoSystem.py`) simulates the temperature dynamics for testing without hardware.
- **Modular & Refactored Code**: The codebase is written in English, follows PEP 8 standards, and is documented with docstrings.
- **Unit Testing**: Includes a `tests` module for verifying core functionality.

## Directory Structure

```
Lab-Protocol/
├── .gitignore
├── CryoSystem.py           # The physical model for the temperature simulation.
├── TemperatureController.py  # The main control logic (PID, scheduling).
├── TemperatureVisualizer.py  # The PyQt5 GUI application.
├── config.csv              # Configuration file for setpoints and stable times.
├── environment.yaml        # Conda environment dependencies.
├── GEMINI.md               # Project log and protocol for AI collaboration.
├── README.md               # This file.
├── log/                    # Directory for runtime log files (auto-generated).
└── tests/
    └── test_controller.py  # Unit tests for the controller.
```

## Usage / Installation

1.  **Set up the Environment**: Make sure you have Conda installed. Create and activate the environment using the provided file:
    ```bash
    # Create the environment from the file
    conda env create -f environment.yaml

    # Activate the new environment
    conda activate Lab-Protocol
    ```

2.  **Configure the Schedule (Optional)**: Open `config.csv` to edit the temperature setpoints and the required time (in seconds) to hold at each temperature.
    - `setpoints`: A comma-separated list of target temperatures in Kelvin.
    - `stable_times`: A comma-separated list of times in seconds.

3.  **Run the Application**: Execute the visualizer script from the project root directory.
    ```bash
    python TemperatureVisualizer.py
    ```

4.  **Run Tests (Optional)**: To run the unit tests, navigate to the `tests` directory and run the test file.
    ```bash
    python -m unittest discover tests
    ```