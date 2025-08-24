# GEMINI.md

## Project Goal

To build a robust temperature control and monitoring application. The system should be able to execute a predefined temperature schedule, stabilize at each setpoint, and provide real-time visualization of the process. The application should be easily switchable between a simulation mode for testing and a real mode for controlling hardware.

## Current Status (After merging 'main' and 'zhuyy')

- **Branch:** `gemini`
- **Core Logic:** The project is based on the `zhuyy` branch, which provides a modular structure with a simulation backend (`CryoSystem.py`), a PID controller (`TemperatureController.py`), and a PyQt5-based GUI (`TemperatureVisualizer.py`).
- **Functionality:** The application can load a temperature schedule from `config.csv`, simulate the cooling process, and visualize the data. It includes a control mechanism based on stability flags.
- **Known Issues:** The control logic runs in the main GUI thread, which will cause the UI to become unresponsive. The codebase uses Chinese for comments and identifiers, which needs to be refactored.

## Development Plan

### Part 1: Asynchronous Refactoring

- **Objective:** Prevent the GUI from freezing by moving the long-running simulation task to a separate thread.
- **Method:** Use PyQt's `QThread` to run the `TemperatureController` in a background worker thread. Communication between the worker and the main GUI thread will be handled safely using signals and slots.

### Part 2: Codebase Refactoring (Adherence to Standards)

- **Objective:** Align the entire codebase with the agreed-upon development protocol.
- **Tasks:**
    1.  **Internationalization:** Convert all comments, identifiers (variables, functions, classes), and UI text to English.
    2.  **Documentation:** Add standard file headers and comprehensive docstrings to all modules, classes, and functions.
    3.  **Code Style:** Ensure compliance with the PEP 8 style guide.
    4.  **Project Docs & Environment:** After refactoring, generate a new `environment.yaml` and update the `README.md`.
