
### 2025-08-24: chore: Correct .gitignore

**Objective:** To correctly configure the `.gitignore` file to exclude generated files and directories from version control.

**Changes:**
1.  **Untracked Files:** Removed previously tracked `__pycache__/` and `log/` directories from the git index using `git rm --cached`.
2.  **Updated .gitignore:** After several corrections prompted by the user, a comprehensive `.gitignore` file was created, including rules for Python cache, logs, OS-specific files, IDE configurations, and the project's `Resource/` directory.

**Outcome:** The project repository is now clean and no longer tracks unnecessary generated files.
