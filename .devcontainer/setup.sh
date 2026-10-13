#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Checking Python and required files..."
python --version
python -c "import sys; assert sys.version_info[:2] == (3, 11), 'Python 3.11 is required. Create a new Codespace using the supplied devcontainer configuration.'"
test -f artifacts/artifact_manifest.json || { echo "Missing artifacts/artifact_manifest.json. Upload the complete artifacts folder."; exit 1; }
test -f web_dashboard/requirements_web.txt || { echo "Missing web_dashboard/requirements_web.txt. Keep the supplied folder structure."; exit 1; }

echo "Creating the Python 3.11 project environment..."
python -m venv .venv311
PYTHON_BIN="./.venv311/bin/python"
"$PYTHON_BIN" -c "import sys; assert sys.version_info[:2] == (3, 11), 'The project environment must use Python 3.11.'"
rm -f -- .venv311/.setup_complete
"$PYTHON_BIN" -m pip install --upgrade pip

echo "Installing CPU inference and application dependencies..."
"$PYTHON_BIN" -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu
"$PYTHON_BIN" -m pip install -r requirements.txt
"$PYTHON_BIN" -m pip install -r web_dashboard/requirements_web.txt
"$PYTHON_BIN" -m pip check

echo "Checking imports and the exported experiment..."
"$PYTHON_BIN" -c "import sys, numpy, torch, torch_geometric, fastapi, uvicorn; print('Python:', sys.version.split()[0]); print('NumPy:', numpy.__version__); print('PyTorch:', torch.__version__); print('Inference device: CPU')"
"$PYTHON_BIN" verify_artifacts.py
"$PYTHON_BIN" web_dashboard/check_web.py
touch .venv311/.setup_complete

echo
echo "CODESPACES SETUP COMPLETE"
echo "To start your dashboard, run: bash RUN_CODESPACES.sh"
