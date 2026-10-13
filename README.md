# Dataset link

https://www.kaggle.com/datasets/ellipticco/elliptic-data-set

# Command to run project

.\.venv\Scripts\python.exe -m streamlit run app_intelligence.py --server.port 8502 --theme.base light

# Phase 6 — Run the project in VS Code on Windows

This folder contains the six-page Streamlit app for your completed Kaggle experiment.
Training remains on Kaggle. Your laptop loads the trained weights and performs CPU inference.
You do not need CUDA Toolkit, NVIDIA drivers, a local GPU, or a new training run.

**Start here:** complete Steps 1–6 in order. These are terminal commands and local files;
do not append them as Kaggle Cells 38 onward.

## 1. Keep the completed Kaggle results

Download `temporal_gnn_inference_artifacts.zip` from Cell 37 or Kaggle's output file panel.
Keep a saved Kaggle notebook version with its outputs too. A temporary notebook download
link can expire: use the current output file panel if the old link returns 404.

The Phase 5 ZIP is the required export. Earlier Phase 3/4 checkpoint ZIPs are insufficient.
Keep the original ZIP as a backup. Do not change model settings or thresholds after testing.

## 2. Open this project in VS Code

If using the app source ZIP, right-click it in Windows Explorer → Extract All.
Open VS Code → File → Open Folder → select `Temporal_GNN_Streamlit`, the folder with `app.py`.
Use Terminal → New Terminal (PowerShell). All commands below run from this folder.

Extract **the contents** of your Kaggle Phase 5 ZIP into the `artifacts` folder:

```text
Temporal_GNN_Streamlit/
  app.py
  model.py
  analytics.py
  project_data.py
  verify_artifacts.py
  requirements.txt
  .streamlit/
    config.toml
  artifacts/
    artifact_manifest.json
    model_config.json
    temporal_gnn_weights.pth
    scaler.pkl
    inference_data.npz
    transaction_predictions.csv
    ... all other files from the Phase 5 ZIP
```

Check that `artifacts/model_config.json` exists directly there. Avoid an extra nested
`artifacts/temporal_gnn_inference_artifacts/` folder. Keep every exported file unchanged:
the verifier checks them against the manifest.

## 3. Create a Python environment

Use 64-bit **Python 3.11** for these instructions. Check it first:

```powershell
py -3.11 --version
```

If it is unavailable, install 64-bit Python 3.11 from the official Python downloads site
and reopen VS Code. An existing Python 3.11 installation is sufficient.

Create a project-specific environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

In VS Code, use Ctrl+Shift+P → Python: Select Interpreter → choose `.venv`.
Install Microsoft's Python extension if that command is absent.
The commands use the environment's Python directly, so PowerShell activation or execution
policy changes are unnecessary.

## 4. Install CPU inference dependencies

Run these two commands separately. Initial downloads can take several minutes depending
on your connection; this is a one-time environment setup.

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The CPU wheel follows [PyTorch's official 2.10 installation instructions](https://pytorch.org/get-started/previous-versions/#v2100).
Core data/PyG versions match your reported Kaggle environment. XGBoost installation is
not needed for this UI: its verified test predictions supply the comparison page, while
the Transaction Analyzer performs fresh Temporal GNN inference.

Check imports and the local device:

```powershell
.\.venv\Scripts\python.exe -c "import torch, torch_geometric, streamlit, sklearn; print('PyTorch:', torch.__version__); print('Local inference: CPU'); print('CUDA available:', torch.cuda.is_available())"
```

`CUDA available: False` is expected for this laptop environment. Kaggle training already
used its T4 GPU; this is a separate, deliberate CPU inference installation.

## 5. Verify the downloaded export

```powershell
.\.venv\Scripts\python.exe verify_artifacts.py
```

This command checks:

1. Every exported file's fingerprint and the frozen checkpoint fingerprints.
2. Transaction ordering, original label mapping, chronological splits and warning rules.
3. Test metrics and confusion matrices recomputed from saved model predictions.
4. Actual CPU Temporal GNN inference on periods 1, 35, 42 and 49, compared with Kaggle.

The successful final line is:

```text
ALL CHECKS PASSED. Ready to run Streamlit.
```

It prints the measured numerical differences; no fixed timing or difference is promised.
If it fails, stop and share the full terminal traceback. Do not edit CSVs, thresholds or
assertions to make it pass. Most extraction issues are resolved by restoring the complete
Phase 5 export into the correct folder. Only load `scaler.pkl` from your own trusted export.

## 6. Launch the six pages

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the Local URL printed in the terminal, normally `http://localhost:8501`.
Keep that terminal running. Ctrl+C stops the app. Next time, only run this launch command;
you do not need to reinstall dependencies or rerun training.

| Page                 | What it uses                                                                          | What to check                                                                     |
| -------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Dashboard            | Verified saved predictions and metrics                                                | All 203,769 transactions; 36,824 test transactions; 0 frozen test-period flags    |
| Transaction Analyzer | Fresh CPU forward pass using real weights, scaler, full snapshot and previous context | Select time 42 and transaction 73160850; click Run model inference                |
| Future Risk          | Saved population means for test periods                                               | Periods 42–49 and previous/current score changes                                  |
| Early Warnings       | Frozen validation-derived rule                                                        | Zero frozen flags remains visible; exploratory sliders never replace the original |
| Suspicious Network   | Original directed edges and saved scores                                              | Real selected transaction, highlighted centre, at most 30 direct neighbours       |
| Model Performance    | Actual test prediction files and training logs                                        | XGBoost leads in AP; all four models and frozen thresholds are shown              |

Transaction 73160850 is an **unknown-label** example that your model scored highly.
Do not call it a confirmed illicit transaction. Small CPU/GPU score differences are normal
within the explicit verification tolerance.

The first graph/inference request loads the compressed inputs into RAM. The app retains
one feature matrix, not one copy per snapshot. It runs inference on one complete snapshot
at a time. An initial pause does not imply retraining.

## What the files do

| File                      | Responsibility                                                                |
| ------------------------- | ----------------------------------------------------------------------------- |
| `app.py`                  | Navigation and all six page layouts                                           |
| `model.py`                | Exact GCN + GRU architecture used for the Kaggle checkpoint                   |
| `project_data.py`         | Artifact validation, cached inputs, graph reconstruction and CPU inference    |
| `analytics.py`            | Population warning rule, snapshot indexing and capped neighbourhood selection |
| `verify_artifacts.py`     | Independent export and inference checks before launching                      |
| `IMPLEMENTATION_NOTES.md` | How to explain the design and measured results                                |
| `PHASE7_ACCEPTANCE.md`    | Local checks and demonstration sequence after the app starts                  |

Resources are loaded once using [Streamlit resource caching](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource).
Inference uses a lock and a fresh context copy for each request. No optimizer exists in
the app. If you replace artifacts, stop and restart Streamlit to clear cached data.

## Troubleshooting

- **Missing artifact files:** correct the extraction location; use the full Cell 37 ZIP.
- **Fingerprint mismatch:** restore the original export. Do not recreate the manifest to bypass the check.
- **`No module named ...`:** run the requirements command with `.venv\Scripts\python.exe`, then launch with that same Python.
- **Cannot find `py`:** install Python 3.11 with the Windows launcher, reopen VS Code, then repeat Step 3.
- **Package installation fails:** share the first full error and `py -3.11 --version`; avoid random upgrades.
- **Port already in use:** stop your earlier app terminal, or append `--server.port 8502` to the launch command.
- **Local prediction mismatch:** share the verifier traceback; do not retrain or loosen the tolerance.
- **Browser opens an empty setup screen:** this is intentional while artifacts are missing. The app has no fabricated fallback data.

## Verification status of this delivery

The code's syntax, model-source equivalence, warning boundaries, snapshot indexing and
neighbourhood behavior were checked locally. Your supplied Kaggle output confirms the
exported CPU inference check passed there. The trained ZIP is not included in this source
package, and an end-to-end Windows Streamlit run with your weights has **not yet been
performed here**. Step 5 and Phase 7 close that remaining verification gap.
