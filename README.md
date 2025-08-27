# Lab Instrument Control Panel

## 1. Introduction

This project provides a modular, web-based control panel for laboratory instruments. It is designed for high cohesion and low coupling, allowing new instruments to be added easily. The front end is built with Python Dash and Plotly for a modern user experience. The application can be run in either a **Real Mode**, interfacing with physical hardware via VISA, or a **Simulated Mode**, which runs a virtual instrument for testing and development.

## 2. Features

-   **Modular Architecture**: Each instrument is a self-contained package.
-   **Dual-Mode Operation**: Switch between a real VISA instrument and a fully simulated instrument directly from the UI.
-   **Web-Based UI**: A responsive user interface built with Dash and Dash Bootstrap Components.
-   **Dynamic Configuration**: The active instrument is loaded at runtime based on the selected mode and the `instruments.csv` and `config.csv` files.
-   **Per-Setpoint Dwell Time**: Configure individual stability dwell times for each setpoint in the temperature schedule.
-   **Automated Control**: "Auto Mode" is enabled by default, allowing the system to automatically advance through setpoints once stability is achieved.
-   **Persistent Data Logging**: All instrument data is logged to CSV files with second-level timestamp precision, and logs are automatically trimmed to manage file size.
-   **Data Export**: Export historical data for a specified date and time range directly from the UI.
-   **External API**: A REST API is exposed to allow other applications to access live data from the currently active instrument.
-   **Unified Interface**: All instruments adhere to a common base class, ensuring consistent behavior.

## 3. Directory Structure

```
E:\Projects\Lab-Protocol\
├── src/
│   └── instruments/
│       ├── base.py                     # Abstract base class for all instruments
│       ├── temperature_controller/     # REAL instrument package for VISA hardware
│       │   ├── interface.py
│       │   └── layout.py
│       └── pid_cooler_simulator/       # SIMULATED instrument package for development/testing
│           ├── interface.py
│           └── layout.py
├── tests/
│   └── test_temperature_controller.py
├── log/
├── Resource/
├── app.py                  # Main Dash application entry point
├── config.csv              # Instrument specific configuration parameters
├── instruments.csv         # Instrument connection and type definitions
├── environment.yaml        # Conda environment dependencies
└── README.md               # This file
```

## 4. Usage / Installation

### 4.1. Environment Setup

This project uses Conda for environment management. To create and activate the environment, run:

```bash
# 1. Create the environment from the YAML file
conda env create -f environment.yaml

# 2. Activate the environment
conda activate lab-protocol
```

### 4.2. Instrument Configuration

Instrument configurations are now split into two files for better organization:

-   `instruments.csv`: Defines the instrument instances, their types, and connection details (e.g., VISA address).
-   `config.csv`: Contains instrument-specific operational parameters, including the temperature schedule with individual dwell times for each setpoint.

**Example `instruments.csv`:**
```csv
instrument_id,type,visa_address
TC290,temperature_controller,ASRL3::INSTR
pid_cooler_sim,pid_cooler_simulator,none
```

**Example `config.csv` (with per-setpoint dwell times):**
```csv
instrument_id,config
TC290,'{"schedule": [{"setpoint": 300, "dwell_time": 10}, {"setpoint": 295, "dwell_time": 15}, {"setpoint": 290, "dwell_time": 20}]}'
pid_cooler_sim,'{"schedule": [{"setpoint": 273, "dwell_time": 10}, {"setpoint": 250, "dwell_time": 10}, {"setpoint": 220, "dwell_time": 10}, {"setpoint": 200, "dwell_time": 10}]}'
```

The `config` column in `config.csv` is a JSON string containing a `schedule` array. Each object in the `schedule` array specifies a `setpoint` (target temperature) and its corresponding `dwell_time` (time in seconds the system must remain stable at that setpoint before advancing).

### 4.3. Running the Application

Once the environment is activated, start the web server:

```bash
python app.py
```

The application will be available at `http://127.0.0.1:8050`. By default, it starts in **Simulated Mode**. Use the radio buttons in the navigation bar to switch between **Simulated** and **Real** modes.

## 5. Connecting to Real Hardware

The `temperature_controller` module is designed to connect to a real instrument via VISA. To make it work with your specific hardware, you need to edit the following methods in `src/instruments/temperature_controller/interface.py`:

-   `get_temperature_from_device(self) -> float`:
    -   Replace the placeholder code with the SCPI command that queries your device for its temperature.
-   `set_setpoint_on_device(self, temp: float)`:
    -   Replace the placeholder code with the SCPI command that sets a new temperature setpoint on your device.

These methods are clearly marked with `!! This is a placeholder !!` in the source code.

## 6. Testing

Unit tests are located in the `tests/` directory. To run a specific test file, execute the following command from the project root:

```bash
python -m unittest tests/test_temperature_controller.py
```

## 7. Changelog

-   **2025-08-28**:
    -   **Configuration Refactor**: Split `config.csv` into `instruments.csv` (for connection details) and `config.csv` (for instrument-specific parameters).
    -   **Per-Setpoint Dwell Time**: Implemented the ability to define a unique `dwell_time` for each setpoint within the instrument's schedule.
    -   **Auto Mode Default**: "Auto Mode" is now enabled by default on application startup.
    -   **CSV Timestamp Precision**: Optimized CSV data logging to use second-level timestamp precision.
    -   **Enhanced Data Export UI**: Improved the data export interface with separate date and time input fields for more precise range selection.
    -   **Codebase Cleanup**: Removed the unused `hardware_api` directory.
-   **2025-08-27**:
    -   Refactored `app.py` to preload all instruments on startup instead of on-demand.
    -   This resolves a bug that caused a Dash callback error (`Output is already in use`) when switching between Simulated and Real modes multiple times.
    -   The application now manages instrument connections and UI visibility dynamically, improving stability and performance.