# Install your redesigned dashboard

Use this final package instead of the earlier UI installation instructions.
The complete UI source is included. You do not need to copy code into separate files.

## 1. Before starting

Your existing project is:

`D:\III_TY All Sub\DL\DL_CP\Temporal_GNN_Streamlit`

Keep this folder, its `.venv` and its `artifacts` folder. They already contain the
Python environment and trained project needed by this upgrade.

Close the terminal running the old Streamlit app, if one is open. Close its browser tab
so that you do not accidentally view the old interface after installation.

You need an internet connection for the first installation. Training remains complete;
the laptop uses CPU inference and does not need CUDA configuration.

## 2. Extract and install

1. Find `Temporal_GNN_UI_Final.zip` in File Explorer.
2. Right-click it and select **Extract All**. Choose any convenient folder.
3. Open the extracted folder. Do not run files from inside the ZIP preview.
4. Double-click **INSTALL_UI.cmd**. Do not run it as administrator.
5. Leave the window open while it installs dependencies and runs the checks.

The installer automatically finds the existing project at the path above and uses its
own Python environment. You do not need to activate `.venv`, choose an interpreter,
find `requirements.txt`, or type pip commands.

You should see these steps:

- Installing the two interface dependencies.
- Checking dependency compatibility.
- Verifying the exported files, test results and all 49 inference periods.
- Checking all six interface pages, actual model inference and replay controls.
- **ALL CHECKS PASSED** and then **READY**.

Downloads may take several minutes depending on your connection. Some Streamlit
testing messages mention a missing ScriptRunContext; look for the final PASS/ERROR
result rather than treating every warning as a failure.

Do not close the window before READY appears. If it stops with an error, follow the
troubleshooting section below rather than repeatedly reinstalling packages.

## 3. Open the dashboard

1. Open your existing project folder:
   `D:\III_TY All Sub\DL\DL_CP\Temporal_GNN_Streamlit`
2. Double-click **START_UI.cmd** in that folder.
3. The new dashboard should open in your browser. If it does not, copy the local
   address printed in the terminal into the browser. It usually ends in `:8502`.
4. Keep the terminal open while using the dashboard. Close it, or press Ctrl+C in it,
   when you finish.

For future demonstrations, only repeat this section. Installation is a one-time step.
You can continue editing in VS Code; opening VS Code is not necessary just to run the app.
Use START_UI.cmd in the project folder, not the uninstalled copy in the extracted ZIP.

## 4. Check the new interface

The sidebar should show these six pages:

| Page | What to try |
|---|---|
| Command Center | Click Start; watch the period and real transaction counts advance; then Pause. |
| Transaction Intelligence | Select an example and click Analyze to run the saved model on CPU. |
| Temporal Risk | Inspect current/previous population scores and the changing trajectory. |
| Early Warning Center | Read the frozen warning rule; inspect separate exploratory thresholds. |
| Network Investigation | Inspect the highlighted transaction and hover over its actual neighbours. |
| Model Intelligence | Compare test results, curves, confusion matrices and training histories. |

At monitoring period 49, Command Center should show **36,824 transactions replayed**,
**1,578 high-risk transaction predictions**, and **0 frozen escalation flags**.
These are actual exported results, not demonstration placeholders.

The replay advances through historical periods 42-49. Reset returns to period 42.
It is not a live Bitcoin feed. Population risk changes describe different transactions
in successive periods, not one transaction's personal history.

Your test set really has zero frozen escalation flags. The interface keeps that result
and offers separately labelled historical examples and exploratory rules. High scores
are model review indicators, not confirmed criminal activity or calibrated probabilities.

## 5. If something fails

| What you see | What to do |
|---|---|
| Could not find the Python environment | Confirm the project path above and keep its `.venv` folder. Share the message; do not delete the environment. |
| A download/network error | Restore your internet connection, then run INSTALL_UI.cmd again. |
| A missing backend or artifact file | Keep the complete existing project together; do not create empty replacement files. Share the missing-file list. |
| A dependency conflict or failed verification | Share `ui_setup.log` from your project folder. Do not retrain or change model thresholds. |
| The old basic dashboard appears | Close the old browser tab and open the address printed by START_UI.cmd. The new entry point is app_intelligence.py. |
| Browser does not open automatically | Paste the printed `http://127.0.0.1:...` address into your browser. |
| A page displays an error | Expand Technical error details and copy the message. You can also run RUN_CHECKS.cmd from the project folder. |

If the project has moved, you can run INSTALL_UI.cmd with the new folder as a quoted
argument from Command Prompt. This is unnecessary for the current project location.

## What this upgrade changes

The installer adds `app_intelligence.py`, the `intelligence` presentation package,
the launcher, checks and these guides. It installs the tested Streamlit and Plotly
versions into your existing environment. Other packages may be resolved as their dependencies.

Your original `app.py`, `model.py`, `project_data.py`, `analytics.py`, verification
script and all artifacts are preserved. They are fingerprinted before and after checks.
If you install over an earlier UI upgrade, changed presentation files are backed up
under `ui_backups`. Python package changes are not included in that file backup.

The new flow is: existing artifacts → existing inference code → readable data adapter
→ six Streamlit pages. No training code is run.

For the demonstration story and scientific interpretation, read DESIGN_AND_DEMO.md.
For exactly what was tested and remaining limitations, read TEST_REPORT.md.
