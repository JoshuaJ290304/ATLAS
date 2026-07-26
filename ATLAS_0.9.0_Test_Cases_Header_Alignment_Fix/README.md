# ATLAS 0.9.0 — Test Cases Header Alignment Fix

This fixes the exact issue shown in the screenshots:

- Removes the four full-width stacked Test Case statistic cards.
- Places the Test Case metrics on the right side of the project header.
- Uses the same `atlas-page-header`, `atlas-header-metrics`, and `atlas-metric-card` layout as Traceability.
- Shows the current project name on the left side of the header.
- Preserves all Test Case functionality below the header.

## Apply

Extract this folder directly inside the ATLAS project root, then run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\ATLAS_0.9.0_Test_Cases_Header_Alignment_Fix\APPLY_TEST_CASES_HEADER_ALIGNMENT.ps1
```

After the frontend restarts, open `http://localhost:5173` and press `Ctrl+F5`.
