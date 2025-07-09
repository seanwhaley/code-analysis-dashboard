# code-intelligence-dashboard

## Directory Structure (Best Practice, as of 2025-07-07)

```filetree
code-intelligence-dashboard/
│
├── src/                       # All core Python modules/scripts
│   ├── comprehensive_dashboard_test.py
│   ├── dashboard_maintenance.py
│   ├── dashboard_test_suite.py
│   ├── dashboard_validator.py
│   ├── final_test_report.py
│   ├── fix_indentation.py
│   ├── launch.py
│   ├── test_async_functionality.py
│   └── ... (other core modules)
│
├── tests/                     # All test scripts and test suites
│   └── (currently empty)
│
├── temp/                      # All outputs, logs, reports, and temp files
│   ├── dashboard_progress.json
│   ├── documentation.db
│   ├── final_dashboard_report.json
│   ├── final_test_results.json
│   ├── fix_results.json
│   ├── frontend_validation_report.json
│   ├── test-dashboard.html
│   └── test_results.json
│
├── docs/                      # All documentation (Markdown, HTML, etc.)
│   ├── AI_AGENT_COMPLETION_PROMPT.txt
│   ├── ASYNC_OPTIMIZATION_SUMMARY.md
│   ├── complete_layout_validation_report.md
│   ├── comprehensive_validation_report.md
│   ├── DASHBOARD_TEST_SUMMARY.md
│   ├── FINAL_STATUS.md
│   ├── LAYOUT_FIX_SUMMARY.md
│   ├── LAYOUT_VALIDATION_GUIDE.md
│   ├── LAYOUT_VALIDATION_SUMMARY.md
│   ├── quick_layout_validation.md
│   ├── README.md
│   ├── visual_testing_report.md
│   └── dashboard.html
│
├── api/                       # API subpackage (if part of core code)
├── assets/                    # Static assets (images, CSS, etc.)
├── components/                # Frontend or shared components
├── __pycache__/               # Should be gitignored
├── README.md
└── ... (other config or manifest files)
```

**Key Points:**

- All core Python code is in `src/` (no nested package folder).
- All tests are in `tests/`.
- All outputs/logs/temp files are in `temp/`.
- All documentation is in `docs/`.
- `api/`, `assets/`, and `components/` remain at the submodule root.
- `__pycache__/` is gitignored.

---

## Automated Contribution Instructions (as of 2025-07-07)

To contribute changes to this submodule (required by repository rules):

1. **Create a new branch:**

   ```powershell
   git checkout -b <your-feature-branch>
   ```

2. **Stage your changes:**

   ```powershell
   git add .
   ```

3. **Commit your changes:**

   ```powershell
   git commit -m "<your descriptive commit message>"
   ```

4. **Push your branch to origin:**

   ```powershell
   git push -u origin <your-feature-branch>
   ```

5. **Open a Pull Request:**
   - Go to your repository on GitHub and open a PR from your branch.

**Note:** Direct pushes to `main` are blocked. All changes must go through a pull request for code review and compliance scanning.
