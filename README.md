# Lab Instrument Control Panel

## 1. Introduction

This project provides a modular, web-based control panel for laboratory instruments. It is designed with a clear and simple architecture, allowing new instruments to be added easily by inheriting from a unified base class. The front end is built with Python Dash and displays each loaded instrument in its own tab.

## 2. Features

-   **Simplified Architecture**: A strong `UnifiedInstrument` base class contains all shared logic for UI, callbacks, data logging, and state management.
-   **Tab-Based UI**: Each instrument loaded from the configuration is displayed in a separate, easy-to-access tab.
-   **Extensible by Inheritance**: Add new instruments simply by creating a new class that inherits from `UnifiedInstrument` and implementing a few hardware-specific methods.
-   **Dynamic Configuration**: Instruments are loaded at runtime based on `instruments.csv` and `config.csv`.
-   **Automated Control**: "Auto Mode" automatically advances through a temperature schedule once stability at each setpoint is achieved.
-   **Persistent Data Logging**: Instrument data is logged to CSV files with automatic log trimming to manage file size.
-   **Data Export**: Export historical data for a specified date and time range directly from the UI.
-   **External API**: A REST API endpoint (`/api/v1/instrument/<instrument_id>/state`) provides external access to live instrument data.

## 3. Directory Structure (Simplified)

```
E:\Projects\Lab-Protocol\
├── src/
│   └── instruments/
│       ├── base.py                     # Core: UnifiedInstrument base class with all shared logic
│       ├── temperature_controller/     # Example: Real instrument inheriting from base
│       │   └── interface.py
│       └── pid_cooler_simulator/       # Example: Simulated instrument inheriting from base
│           └── interface.py
├── tests/
├── log/
├── app.py                  # Main Dash application entry point
├── config.csv              # Instrument-specific parameters (e.g., temperature schedule)
├── instruments.csv         # Instrument definitions and connection details
├── environment.yaml        # Conda environment dependencies
└── README.md               # This file
```

## 4. Usage / Installation

### 4.1. Environment Setup

This project uses Conda for environment management.

```bash
# 1. Create the environment from the YAML file
conda env create -f environment.yaml

# 2. Activate the environment
conda activate lab-protocol
```

### 4.2. Instrument Configuration

-   **`instruments.csv`**: Defines the instrument instances, their types (which map to the folder name in `src/instruments`), and connection details (e.g., VISA address).
-   **`config.csv`**: Contains instrument-specific operational parameters, like the temperature schedule.

**Example `instruments.csv`:**
```csv
instrument_id,type,visa_address
'TC290','temperature_controller','ASRL3::INSTR'
'pid_sim','pid_cooler_simulator','none'
```

**Example `config.csv`:**
```csv
instrument_id,config
'TC290','{"schedule": [{"setpoint": 300, "dwell_time": 10}, {"setpoint": 295, "dwell_time": 15}]}'
'pid_sim','{"schedule": [{"setpoint": 273, "dwell_time": 5}, {"setpoint": 250, "dwell_time": 5}]}'
```

### 4.3. Running the Application

```bash
python app.py
```
The application will be available at `http://127.0.0.1:8050`.

## 5. Adding a New Instrument

1.  Create a new folder under `src/instruments/` (e.g., `my_new_instrument/`).
2.  Inside, create an `interface.py` file.
3.  In `interface.py`, define a class `InstrumentInterface` that inherits from `src.instruments.base.UnifiedInstrument`.
4.  Implement the required abstract methods: `connect()`, `disconnect()`, `read_temperature()`, and `write_setpoint()`.
5.  Add your new instrument to `instruments.csv` and `config.csv`.
6.  Run the application. Your new instrument will automatically appear in its own tab.

## 6. Connecting to Real Hardware

For real instruments (like the `temperature_controller` example), you must edit its `interface.py` file to include the correct SCPI commands for your specific device. The methods to edit are `read_temperature()` and `write_setpoint()`. These are clearly marked in the source code.
