# Run your Temporal GNN project without Streamlit

This folder adds a separate FastAPI server and a custom HTML/CSS/JavaScript dashboard. It reads your existing project modules and verified Kaggle artifacts. It does not replace your Python model, preprocessing, checkpoints, scores or frozen thresholds.

## command to run the project

.\.venv\Scripts\python.exe web_dashboard\run_web.py

## 1. Put the new folder in the right place

Extract `Temporal_GNN_Web_Dashboard.zip`. Copy its **whole `web_dashboard` folder** into:

```text
D:\III_TY All Sub\DL\DL_CP\Temporal_GNN_Streamlit
```

The result must look like this:

```text
Temporal_GNN_Streamlit\
    .venv\
    artifacts\
    intelligence\
    model.py
    project_data.py
    analytics.py
    ...your existing files...
    web_dashboard\
        READ_ME_FIRST.md
        requirements_web.txt
        run_web.py
        server.py
        web_service.py
        check_web.py
        START_WEB.cmd
        project.json
        static\
```

Keep `artifacts` where it is. Do not put the new files into `artifacts`. Do not delete your `.venv` or rename your project. The existing folder name containing “Streamlit” does not cause Streamlit to run.

## 2. Open the existing project in VS Code

Choose **File → Open Folder** and select `Temporal_GNN_Streamlit` at the path above.

Choose **Terminal → New Terminal**. These instructions use VS Code's **PowerShell** terminal.

If the old Streamlit server is still running in another terminal, stop it with **Ctrl+C** first. You only need the new server running for this dashboard.

## 3. Install the small web dependencies — once

Copy this command into the terminal and press Enter:

```powershell
.\.venv\Scripts\python.exe -m pip install -r web_dashboard\requirements_web.txt
```

Wait for installation to finish. This uses your existing Python environment and its PyTorch/PyG dependencies. You do not need Node.js, npm, a React installation, a CUDA Toolkit or model retraining. Training remains the Kaggle work you already completed; local analysis uses your saved CPU inference path.

If your working environment is named `.venv311`, replace `.venv` with `.venv311` in all commands in this guide. Use the environment that successfully ran your original project.

## 4. Check the connection — once

```powershell
.\.venv\Scripts\python.exe web_dashboard\check_web.py
```

The final line should say **ALL 100 CHECKS PASSED**. This checks dashboard values, a fresh model prediction, original directed graph edges, chronological replay visibility, warning rules, model metrics, error responses and file fingerprints. The check uses real artifacts and may take longer on the first run while Python loads PyTorch. It does not open a browser or start Streamlit.

If a check fails, retain your files and share its terminal output. Do not edit an artifact or its manifest to bypass a failed verification. A deprecation warning from Starlette about its HTTP test client is not a failed check.

## 5. Start the website

```powershell
.\.venv\Scripts\python.exe web_dashboard\run_web.py
```

Wait for **Application startup complete**. Open this address in your browser:

**http://127.0.0.1:8000**

Keep the terminal open while you use the website. Stop it with **Ctrl+C** when finished. Do not double-click `index.html` or launch it through VS Code Live Server: the dashboard needs the Python server to obtain real data.

After closing your laptop, reopening only requires opening this project in VS Code and running the command in Step 5 again. Installation is not needed every day.

If port 8000 is already busy:

```powershell
.\.venv\Scripts\python.exe web_dashboard\run_web.py --port 8001
```

Then open **http://127.0.0.1:8001**. The server listens only on your laptop.

After installation, you can alternatively double-click `web_dashboard\START_WEB.cmd`. It finds `.venv` or `.venv311` in the parent project folder and starts the same server. The VS Code command above is the clearest option for seeing errors.

## 6. Review the Command Center first

The default design uses a dark teal navigation sidebar, a light background, white panels, clear charts and compact tables. Click **Dark theme** at the top right to switch; click **Light theme** to return. Your theme choice stays in the browser.

Open the Command Center before reviewing the other pages. It starts at observed period 42. Change **Period** to 49 to see the complete held-out population:

- Dataset coverage: **203,769** transactions.
- Transactions replayed: **36,824**.
- High-risk predictions: **1,578**, at your frozen model threshold of **0.60**.
- Frozen escalation flags: **0**.
- Temporal GNN test F1: approximately **0.4930**.

These values come from your original DataAdapter and exported results. If you want a different visual style, change only the files in this new folder after agreeing on the Command Center appearance.

To change the big dashboard heading, edit `static\app.js` and search for `Transaction Risk Intelligence` inside the `overview` function. To change the browser tab name and sidebar brand, edit `static\index.html`. Refresh the browser after saving; use **Ctrl+F5** if it retains old styles.

## 7. Demonstrate the other pages

**Transaction Intelligence:** search for `TX-73160850` at period 42. Select the reference and click **Run model analysis**. The first analysis loads the saved CPU model; subsequent analyses reuse it. The model uses all nodes and edges in that transaction's snapshot, your saved scaler and its exported preceding graph context. A score-verification message confirms agreement with Kaggle. This example has an unknown recorded label, so its high score is not proof of illicit activity.

**Network Investigation:** click **Investigate network** from the transaction page. The graph uses actual original directed connections. Click a node to investigate it. The view contains a selected transaction and up to 30 neighbours; connection statistics refer to the full neighbourhood, and model inference uses the complete undirected snapshot.

**Temporal Risk:** inspect population scores and changes across observed periods. Enable **Include earlier context** to view periods 1–41 separately from test periods 42–49. The GRU carries graph-level context; transactions do not persist across periods.

**Early Warning Center:** the frozen feed correctly contains zero test escalation flags. Both the population-level and increase conditions must hold. Earlier actual triggers are available as historical examples. The exploratory controls compare another rule without changing the saved model, scores, test results or frozen feed. Values here are shown as score points out of 100: your frozen conditions are approximately **21.32** population score and **3.07** increase points.

**Model Intelligence:** compare all four actual test results, inspect PR/ROC curves, confusion matrices and recorded histories, and download the original metric CSV. This full benchmark stays fixed while the replay cursor moves. XGBoost leads the recorded test AP; the temporal model's small AP difference over the reset-history control is not evidence of statistical significance.

**Replay controls:** Start advances through complete snapshots 42–49 at the selected speed. Pause stops advancement. Reset returns to 42 and clears the selected transaction. Selecting a period manually pauses replay. At 49 replay stops; Start begins again at 42. Replay is historical, with no live blockchain connection or simulated arrival order inside a snapshot.

## What the new files do

| File                          | Purpose                                                        |
| ----------------------------- | -------------------------------------------------------------- |
| `run_web.py`                  | Starts the local website and handles an occupied port.         |
| `server.py`                   | Serves the frontend and validated API endpoints.               |
| `web_service.py`              | Imports your existing data adapter and model inference code.   |
| `static\index.html`           | Browser shell, navigation and replay controls.                 |
| `static\styles.css`           | Dashboard layout, colours, themes and responsive styles.       |
| `static\app.js`               | Six pages, real API requests, charts and replay state.         |
| `static\vendor\plotly.min.js` | Bundled charts; no chart CDN or internet connection required.  |
| `check_web.py`                | Checks the new bridge against your actual artifacts.           |
| `project.json`                | Fallback location if you keep this folder outside the project. |

The server normally finds your project in its parent folder, so group members can use another drive or directory. `project.json` is used only if this folder is outside the original project. In that case edit `project_path` using forward slashes, or set `TEMPORAL_PROJECT_DIR` before launching.

For group sharing, include this folder together with the original Python files, `intelligence` and `artifacts`. Exclude `.venv`, `.venv311` and `__pycache__` from the shared ZIP. Each group member creates their own environment and installs the original project's requirements plus `web_dashboard\requirements_web.txt`.

## If something does not start

- **Python path not found:** confirm VS Code opened the parent project folder and use the actual environment name, `.venv` or `.venv311`.
- **requirements file not found:** check that `web_dashboard` is directly inside the original project, not inside a second extracted ZIP folder.
- **Missing project or artifact file:** keep the new folder alongside the original `project_data.py`, `model.py`, `analytics.py`, `intelligence` and complete `artifacts` folder.
- **Cannot connect:** keep the Python server terminal running and use its printed localhost address. Wait for startup to complete.
- **First analysis slow:** the first request loads PyTorch and the saved model. Stop a duplicate old dashboard if both are running. A memory-allocation error requires freeing laptop memory before restarting; do not delete project files.
- **Search returns nothing:** use an exported transaction reference from the currently replayed test periods. A period-49 record is unavailable while the cursor is at 42.
- **No warnings:** that is your recorded test outcome, not a malfunction.

The automated data/model checks are provided separately from visual browser approval. Inspect the Command Center on your laptop before approving its appearance. Browser automation was stopped during development, so a complete browser layout and interaction review is still outstanding.
