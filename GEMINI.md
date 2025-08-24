<!-- GEMINI'S MEMORY: DO NOT OVERWRITE. This file is a cumulative log. Always read the content, append new entries, and then write the full content back. -->

# GEMINI.md

## Project Goal

To build a robust, modular, and easily extensible temperature control and monitoring application. The system should execute a predefined temperature schedule, provide real-time visualization, and seamlessly switch between simulation and real hardware modes.

## Project Status (Active)

- **Branch:** `gemini`
- **Architecture:** The project uses a clean, decoupled architecture with a hardware abstraction layer.
- **Functionality:** 
    - Asynchronous GUI with real-time plotting.
    - Supports both simulated and real hardware via a strategy pattern.
    - Automatic and manual control modes for advancing through temperature setpoints.
    - Enhanced UI with clearer status indicators and dynamic plot scaling.
    - **New:** Added a real-time stability timer.
    - **New:** Improved plot visualization with a fixed-origin time axis.
    - **New:** Refined UI by removing redundant controls and indicators.
- **Next Steps:** The `VisaBridge` in `hardware_api/visa.py` is a skeleton and needs to be implemented with real hardware commands.

## Changelog

### 2025-08-24: Data Management & Plotting Overhaul

**Objective:** To enhance long-term data handling, improve plot visualization for large datasets, and provide data export functionality.

**Changes:**
1.  **Comprehensive Plot View:** The plot's X-axis logic has been redesigned. It now always starts at 0 and dynamically expands to show the entire history of the run, ensuring no data is ever hidden off-screen. A small padding is maintained on the right edge for better readability.
2.  **High-Performance Plotting:** Enabled `pyqtgraph`'s built-in downsampling feature. This significantly improves performance and keeps the GUI responsive, even when plotting thousands of data points over long durations.
3.  **Full Data Retention:** The internal data storage was switched from a fixed-size `deque` to a standard `list`, allowing the application to retain the complete history of temperature readings for the entire session.
4.  **Data Export Feature:**
    - Added a new "Data Management" panel to the UI.
    - Implemented an "Export Data" button that opens a file-save dialog.
    - Users can now save all recorded data to a CSV file, with a timestamp-based default filename (e.g., `2025-08-24_15-30-00.csv`).
    - The exported file contains two columns: a human-readable `Timestamp` and `Temperature (K)`.

**Outcome:** The application is now a more powerful tool for long-running experiments, offering robust data visualization, improved performance, and the critical ability to export complete datasets for external analysis.

### 2025-08-24: UI Interaction & Plotting Enhancements

**Objective:** To improve the user experience by refining default behaviors and adding more granular control over the plot visualization.

**Changes:**
1.  **Default to Auto Mode:** The application now starts and resets directly into "Auto Mode," streamlining the most common use case.
2.  **Advanced Plot Control:**
    - **"Reset View" Button:** A new button has been added that resets the plot's zoom and pan to the default auto-scaling view.
    - **Smart Auto-Scaling:** The plot's automatic scaling is now disabled whenever the user manually zooms or pans, allowing for detailed inspection of the data. Auto-scaling is re-enabled by clicking the "Reset View" button.
3.  **Non-Negative Time Axis:** The plot's X-axis (time) has been constrained to prevent it from ever showing negative values, improving clarity.

**Outcome:** The application is now more intuitive to operate, with sensible defaults and more powerful, user-friendly plot interaction.

### 2025-08-24: Feature Enhancement & UI Refinement

**Objective:** To improve usability and add new features based on user feedback.

**Changes:**
1.  **Plot Simplification:** Removed the red "Target Setpoint" line from the real-time plot to reduce visual clutter. The current setpoint is already clearly displayed in the status bar.
2.  **Stability Threshold:** The temperature stability check is now more lenient, with the required threshold changed from ±0.5K to ±1.0K.
3.  **Stability Timer:** Added a new "Time Stable" label to the UI, which displays a real-time, asynchronously updated timer showing how long the system has been within the stable temperature range.
4.  **Plot X-Axis Control:** The time axis on the plot has been improved. It now always starts at 0, maintains a minimum visible window of 100 seconds, and compresses its scale to show all data after the 100-second mark is passed.
5.  **UI Simplification:**
    - Removed the "Clear Data" button to avoid confusion with the "Reset Simulation" button.
    - Removed the redundant "Stability: Yes/No" label from the top status bar, as this information is already present in the "Stability Control" panel.
6.  **Reset Fix:** The "Reset Simulation" button now correctly clears all data from the plot and resets the view to its initial state, providing a clean restart.

**Outcome:** The application is now more intuitive, provides better visual feedback on stability, and has a more polished and predictable user interface.

### 2025-08-24: GUI Enhancement & Auto Mode

**Objective:** To improve the user interface and add an automatic control mode for unattended operation.

**Changes:**
1.  **Auto/Manual Mode:** Implemented a toggle button allowing the system to automatically proceed to the next setpoint after stability is achieved.
2.  **UI Layout:** Redesigned the status bar in `TemperatureVisualizer` to include separators and distinct labels for "Final Target" and "Current Setpoint", improving clarity.
3.  **Dynamic Plot Scaling:** The Y-axis of the temperature plot now automatically scales to fit the entire range of the temperature schedule (from start to final target), providing a better overview.
4.  **Configuration Management:** The `config.csv` file is now untracked by Git, allowing for local modifications without affecting the repository.

**Outcome:** The application is now more user-friendly and capable of running a full temperature schedule without manual intervention.

### 2025-08-24: Architectural Refactoring (Strategy Pattern)

**Objective:** To implement a clean, scalable architecture that separates control logic from hardware interaction, based on the user's suggestion.

**Changes:**
1.  **Hardware Abstraction Layer:** Created a new `hardware_api` directory to serve as a hardware abstraction layer (HAL).
2.  **Defined Common Interface:** Created an abstract base class `AbstractTemperatureBridge` (`hardware_api/base.py`) to define a strict API contract for all hardware implementations.
3.  **Separated Implementations:**
    - `SimulatedBridge` (`hardware_api/simulated.py`): Encapsulates the `CryoSystem` simulation logic.
    - `VisaBridge` (`hardware_api/visa.py`): Provided a ready-to-use skeleton file for implementing real VISA-based hardware control.
4.  **Decoupled Controller:** Refactored `TemperatureController` to remove all `if/else` debug checks. It now relies entirely on the `AbstractTemperatureBridge` interface and uses a factory pattern in its `__init__` to select the correct bridge (simulated or real) at runtime.

**Outcome:** The new architecture is highly modular, easy to maintain, and simple to extend with new hardware implementations in the future without touching the core control logic.

### 2025-08-24: Asynchronous Refactor & Standardization

- **Asynchronous GUI:** Re-implemented the `TemperatureVisualizer` to run the `TemperatureController` in a separate `QThread`. This resolved UI freezing issues.
- **Code Standardization:** Translated the entire codebase (variables, comments, UI) to English. Added file headers, docstrings, and ensured PEP 8 compliance.
- **Unit Testing:** Established a `tests` directory with a basic unit test for the controller.
- **Documentation:** Updated `README.md` and `environment.yaml`.

## Current Directory Structure

```
Lab-Protocol/
├── .gitignore
├── TemperatureController.py
├── TemperatureVisualizer.py
├── environment.yaml
├── GEMINI.md
├── README.md
├── hardware_api/
│   ├── __init__.py
│   ├── base.py
│   ├── CryoSystem.py
│   ├── simulated.py
│   └── visa.py
├── log/
└── tests/
    └── test_controller.py
```
*Note: `config.csv` is now untracked by Git.*

### 2025-08-24: chore: Correct .gitignore

**Objective:** To correctly configure the `.gitignore` file to exclude generated files and directories from version control.

**Changes:**
1.  **Untracked Files:** Removed previously tracked `__pycache__/` and `log/` directories from the git index using `git rm --cached`.
2.  **Updated .gitignore:** After several corrections prompted by the user, a comprehensive `.gitignore` file was created, including rules for Python cache, logs, OS-specific files, IDE configurations, and the project's `Resource/` directory.

**Outcome:** The project repository is now clean and no longer tracks unnecessary generated files.