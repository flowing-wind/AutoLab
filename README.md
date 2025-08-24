# Lab-Protocol: Temperature Control System

## Introduction

This project is a temperature control and monitoring application designed for laboratory environments. It provides a graphical user interface to visualize and manage a system's temperature in real-time. 

The application is built on a clean, decoupled architecture, featuring a hardware abstraction layer. This allows the core control logic to remain independent from the specific hardware (or simulation) it is controlling. The application's asynchronous design ensures the user interface remains responsive at all times.

## Features

- **High-Performance Real-Time Visualization**: Plots live temperature data on a high-performance graph that remains smooth even with thousands of data points. The plot view automatically scales to show the full temperature range of the current schedule.
- **Modern User Interface (NEW)**: Features a clean, modern design inspired by Google's Material Design, with a blue color palette and subtle animations for an enhanced user experience.
- **Complete History View**: The plot's time axis dynamically expands to show the entire run from T=0, ensuring no data is ever scrolled off-screen.
- **Advanced Plot Control**: The plot's auto-scaling is disabled on manual zoom/pan. A "Reset View" button restores the default auto-scaling behavior.
- **Data Export (UPDATED)**: Easily export all collected data to a timestamped CSV file for external analysis, with temperature values formatted to four decimal places.
- **Setpoint Scheduling**: Load a sequence of target temperatures and required stabilization times from an external `config.csv` file.
- **Stability Control (UPDATED)**: The UI displays "Stable" as soon as the temperature difference is within ±1.0K of the setpoint, and a real-time timer shows how long this condition has been met. The core system stability for setpoint advancement is determined by the `stable_times` defined in `config.csv`.
- **Automatic & Manual Control**:
    - **Manual Mode**: Manually advance to the next temperature setpoint with the click of a button after the system is stable.
    - **Auto Mode**: The application defaults to this mode. It automatically proceeds through the entire temperature schedule, advancing to the next setpoint as soon as stability is achieved.
    - **Reset Behavior (UPDATED)**: The "Reset Simulation" button now automatically sets the system back to "Auto Mode" after restarting the simulation.
- **Hardware Abstraction Layer (HAL)**: A plug-and-play architecture that separates the main control logic from the hardware interface. Switch between simulation and real hardware by changing a single flag.
- **Asynchronous Operations**: The control loop runs in a separate thread to keep the GUI from freezing.
- **Extensible by Design**: Easily add support for new instruments by creating a new "bridge" class in the `hardware_api` directory.
- **Ready-to-use Simulation**: Comes with a built-in simulation bridge for full application testing without any hardware.
- **Unit Testing**: Includes a `tests` module for verifying core functionality.

## Directory Structure

```
Lab-Protocol/
├── .gitignore
├── TemperatureController.py  # The main control logic (PID, scheduling).
├── TemperatureVisualizer.py  # The PyQt5 GUI application.
├── config.csv              # (Untracked) Configuration file for setpoints and stable times.
├── environment.yaml        # Conda environment dependencies.
├── README.md               # This file.
├── hardware_api/           # The Hardware Abstraction Layer.
│   ├── __init__.py
│   ├── base.py             # Defines the abstract interface for all bridges.
│   ├── CryoSystem.py       # The physical model for the simulation.
│   ├── simulated.py        # The bridge for the simulated hardware.
│   └── visa.py             # A skeleton bridge for real VISA-based hardware.
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
2.  **Install GUI Dependencies (NEW)**: The graphical interface now uses `qt-material` for enhanced aesthetics. Install it within your active Conda environment:
    ```bash
    pip install qt-material
    ```
3.  **Configure the Schedule (Optional)**: Open `config.csv` to edit the temperature setpoints and the required time (in seconds) to hold at each temperature.
    - `setpoints`: A comma-separated list of target temperatures in Kelvin.
    - `stable_times`: A comma-separated list of times in seconds.

4.  **Run the Application**: Execute the visualizer script from the project root directory.
    ```bash
    python TemperatureVisualizer.py
    ```

5.  **Operating the GUI**:
    - **Default Mode**: The application starts in "Auto Mode" by default.
    - **Mode Selection**: Use the "Switch to Manual" button to toggle to manual mode.
    - **Manual Control**: In manual mode, once the system is stable, the "Request Next Setpoint" button will become active. Click it to proceed.
    - **Plot Control**: Manually zoom or pan the plot to inspect data. Click the "Reset View" button to return to the default auto-scaling view.
    - **Exporting Data**: Click the "Export Data" button at any time to save the complete history of the current run to a CSV file.
    - **Pausing**: The "Pause" button will halt the simulation/control loop.
    - **Reset**: The "Reset Simulation" button restarts the process (in Auto Mode) with the current schedule from `config.csv`.

6.  **Run Tests (Optional)**: To run the unit tests, use the following command from the project root:
    ```bash
    python -m unittest discover tests
    ```