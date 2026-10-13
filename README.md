# Temporal GNN Transaction Risk Dashboard

A course project using the Elliptic Bitcoin dataset, a Temporal Graph Neural Network,
and a browser dashboard for transaction analysis, network investigation and historical replay.
The frontend uses HTML, CSS and JavaScript; the backend uses FastAPI.

## Model and experiment

Two GCN layers create 64-dimensional transaction embeddings. Graph mean pooling and a
GRUCell update one shared graph context per period. The model concatenates each node
embedding with that context and classifies transactions as licit or illicit.

- Dataset: 203,769 transactions, 234,355 original directed edges, 165 input features and 49 periods.
- Training: periods 1-34 on Kaggle GPU.
- Validation: periods 35-41 for checkpoint and threshold selection.
- Frozen testing: periods 42-49, with no test-based tuning.
- Comparison models: XGBoost, static GCN and a reset-history control.
- Temporal GNN test F1: 0.4930; Average Precision: 0.4577.
- XGBoost performed best on the recorded test set: F1 0.6091; Average Precision 0.5512.

The dashboard presents model scores and observed historical replay. It does not
forecast unseen future periods or confirm that a transaction is criminal.

## Run in GitHub Codespaces

1. Ensure the repository contains `.devcontainer`, `web_dashboard`, `intelligence`,
   the root Python files and the complete `artifacts` folder.
2. Click **Code > Codespaces > + / Create codespace on main**. Use a NEW Codespace
   after uploading this configuration; an existing Codespace may still use its old image.
3. This repository selects Python 3.11. Its setup command creates `.venv311`, installs
   CPU PyTorch and the application requirements, and verifies the exported artifacts
   and web backend. The launch script checks that setup completed successfully.
4. Wait for **CODESPACES SETUP COMPLETE**. If setup fails, read the first error;
   do not launch the server before installation and verification pass.
5. In the Codespaces terminal, run:

```bash
bash RUN_CODESPACES.sh
```

6. After **Application startup complete**, open **PORTS > 8000 > Open in Browser**.
   If necessary, use **Add Port** and enter `8000`.

For later runs, reopen this Codespace and use `bash RUN_CODESPACES.sh` again.
If setup was interrupted, retry `bash .devcontainer/setup.sh` before launching.
Keep the server terminal open. Press Ctrl+C to stop the server, and stop the Codespace
when finished to avoid using compute time unnecessarily.

Codespaces is a development/demo environment, not a permanent always-on hosting service.
Ports are private by default. A temporary public demo can be enabled manually using
**PORTS > right-click 8000 > Port Visibility > Public** while the Codespace is running.

## Run locally on Windows

Use Python 3.11 and open the root project folder in VS Code.

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt
.\.venv311\Scripts\python.exe -m pip install -r web_dashboard\requirements_web.txt
.\.venv311\Scripts\python.exe verify_artifacts.py
.\.venv311\Scripts\python.exe web_dashboard\run_web.py
```

For later local runs, only the final launch command is needed in that environment.
The compatibility requirements retain the project's existing dependency versions.
Training remains on Kaggle; this application uses saved weights for CPU inference.

## Files that must remain together

```text
.devcontainer/
    devcontainer.json
    setup.sh
artifacts/
    artifact_manifest.json
    temporal_gnn_weights.pth
    model_config.json
    scaler.pkl
    inference_data.npz
    ... all other supplied artifact files
intelligence/
web_dashboard/
    server.py
    web_service.py
    run_web.py
    requirements_web.txt
    static/
model.py
project_data.py
analytics.py
verify_artifacts.py
requirements.txt
RUN_CODESPACES.sh
```

The artifacts are tracked in Git. `.gitattributes` preserves their bytes so the
saved manifest fingerprints remain valid across Windows and Linux.
Virtual environments, caches and private local settings are ignored.

## Sources and setup documentation

- Elliptic dataset: https://www.kaggle.com/datasets/ellipticco/elliptic-data-set
- GCN paper: https://arxiv.org/abs/1609.02907
- Elliptic transaction analysis: https://arxiv.org/abs/1908.02591
- GitHub Python Codespaces setup: https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/setting-up-your-python-project-for-codespaces
- PyTorch CPU installation: https://pytorch.org/get-started/previous-versions/
