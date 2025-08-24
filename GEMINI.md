<!-- GEMINI'S MEMORY: DO NOT OVERWRITE. This file is a cumulative log. Always read the content, append new entries, and then write the full content back. -->

# GEMINI.md

## Project Goal

To build a robust, modular, and easily extensible temperature control and monitoring application. The system should execute a predefined temperature schedule, provide real-time visualization, and seamlessly switch between simulation and real hardware modes.

## Project Status (Active)

- **Branch:** `gemini`
- **Architecture:** The project now uses a clean, decoupled architecture. A central `TemperatureController` operates on a hardware abstraction layer (`hardware_api`), allowing it to control either a `SimulatedBridge` or a `VisaBridge` without changing its core logic.
- **Functionality:** All previous functionalities are preserved. The GUI is fully asynchronous, preventing UI freezes. The codebase is standardized to English and follows PEP 8.
- **Next Steps:** The `VisaBridge` in `hardware_api/visa.py` is a skeleton and needs to be implemented with real hardware commands.

## Changelog

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
├── config.csv
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

### 2025-08-24: chore: Correct .gitignore

**Objective:** To correctly configure the `.gitignore` file to exclude generated files and directories from version control.

**Changes:**
1.  **Untracked Files:** Removed previously tracked `__pycache__/` and `log/` directories from the git index using `git rm --cached`.
2.  **Updated .gitignore:** After several corrections prompted by the user, a comprehensive `.gitignore` file was created, including rules for Python cache, logs, OS-specific files, IDE configurations, and the project's `Resource/` directory.

**Outcome:** The project repository is now clean and no longer tracks unnecessary generated files.
